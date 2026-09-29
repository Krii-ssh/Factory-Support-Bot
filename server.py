#!/usr/bin/env python3
"""
WhatsApp webhook for the factory accident support bot.

    py -3.11 -m uvicorn server:app --port 8000

Then expose port 8000 publicly (ngrok, or the Twilio CLI) and paste that URL
plus /whatsapp into the Twilio sandbox's "When a message comes in" box.

Two design points worth knowing before changing anything here.

**The webhook answers immediately and does the work afterwards.** Twilio gives a
webhook about fifteen seconds before it gives up; this pipeline can take longer
than that on its own, because the free tier allows one or two answers a minute
and requests queue rather than collide. So the handler acknowledges at once and
runs the pipeline in the background, sending the holding message and then the
answer as separate outbound messages.

**Each message is answered on its own, with no conversation history.** That is
a safety decision, not a missing feature. The whole design rests on the model
seeing nothing but retrieved, verified law; feeding earlier turns back in would
put unverified text: including the family's own guesses about their case, and
anything a stranger forwarded them: into the context the answer is built from.
The one thing that IS remembered is which message IDs have been handled, so a
Twilio retry cannot produce a second answer and a second charge.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, Form, Header, Request, Response
from fastapi.responses import HTMLResponse

import config
import groq_client
import meta_whatsapp
import query
import tracker
import whatsapp

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s  %(levelname)-7s %(message)s"
)
log = logging.getLogger("factory-bot")

whatsapp.load_env()


# --------------------------------------------------------------------------
# The three strings a family sees that are not generated from law
# --------------------------------------------------------------------------

# Someone who sends a voice note usually did so because typing is hard - low
# literacy, a cracked screen, or hands that are shaking. "Unsupported media
# type" energy would land as a second refusal on the worst day of their life.
# So: apologise for the bot's limit rather than theirs, keep the door open,
# and give the human number in the same breath.
UNSUPPORTED_MEDIA = (
    "Sorry - I can only read typed messages at the moment. If you can, please "
    "type your question and I will help.\n\n"
    "If typing is difficult, please call free legal aid instead. They will "
    "speak with you directly:\n" + query.CONTACT_LINE
)

# Appended once, on the first reply of a new case. Deliberately says what it
# is FOR - a number with no stated purpose gets discarded.
CASE_ID_LINE = (
    "\n\nYour reference number is {case_id}. Please keep it - it helps us "
    "find your case if you message again or call."
)

# Sent when Groq is rate limited and the retries did not clear it. Says what
# to do, gives a timescale, and does not mention rate limits or capacity -
# none of that is the family's problem to understand.
BUSY_REPLY = (
    "I am handling a lot of messages right now and could not get your answer. "
    "Please send your question again in a minute - it will go through.\n\n"
    "If it is urgent, please call free legal aid now:\n" + query.CONTACT_LINE
)


# One lock per WhatsApp number, so a person's own messages are answered in the
# order they were sent.
#
# This is not a nicety. Distressed people send several short messages in a row
# - that is the normal pattern here, not an edge case. Send "the owner is
# offering us money" and then "what should we do", and concurrent handling can
# deliver the compensation answer BEFORE the settlement warning. The one
# message whose entire value is arriving first would arrive second.
#
# threading.Lock rather than asyncio.Lock because _handle is a sync function
# and FastAPI runs it in a worker thread, where an asyncio primitive would not
# apply.
_sender_locks: dict[str, threading.Lock] = {}
_sender_locks_guard = threading.Lock()


def _lock_for(sender: str) -> threading.Lock:
    with _sender_locks_guard:
        if sender not in _sender_locks:
            _sender_locks[sender] = threading.Lock()
        return _sender_locks[sender]

# Twilio retries a webhook it thinks failed, including when it merely timed out
# waiting. Without this a retry runs the whole pipeline again and the family
# receives the answer twice.
_handled: set[str] = set()
_handled_lock = threading.Lock()


def _already_handled(message_sid: str) -> bool:
    with _handled_lock:
        if message_sid in _handled:
            return True
        _handled.add(message_sid)
        # Unbounded growth is a slow leak on a long-running process. A demo
        # never gets near this, and dropping the oldest entries only risks
        # re-answering a very old retry.
        if len(_handled) > 5000:
            _handled.clear()
        return False


# --------------------------------------------------------------------------
# Message handling: runs off the request thread
# --------------------------------------------------------------------------


def holding_enabled() -> bool:
    """
    Whether to send the "one moment" message before the answer.

    On by default, because a twenty-second silence on WhatsApp reads as broken
    and people re-send: which costs another slot in an already tight budget.

    Set SEND_HOLDING=0 while testing. A Twilio trial allows a fixed number of
    outbound messages (96 at the time of writing) and the holding message
    doubles the cost of every question, so a few rehearsals can eat the demo.
    Turn it back on before demo day: it is the difference between the wait
    looking deliberate and looking dead.
    """
    return os.environ.get("SEND_HOLDING", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def transport():
    """
    Meta when it is configured, Twilio otherwise.

    Both are built and tested. Meta is preferred because a Twilio trial account
    cannot send free-form text at all: it demands a pre-approved template for
    every message, which a generated legal answer can never be.
    """
    return whatsapp if meta_whatsapp.credentials_look_wrong() else meta_whatsapp


def _handle(sender: str, body: str) -> None:
    """Run the pipeline and send the result. Runs off the request thread."""
    # Serialised per sender: see the note on _sender_locks. Two messages from
    # two different people still run concurrently.
    with _lock_for(sender):
        _handle_locked(sender, body)


def _handle_non_text(sender: str, kind: str) -> None:
    """
    Answer a voice note, image or document by saying what the bot can do.

    Logged with the media type because the count decides whether voice input is
    urgent. Building Whisper before anyone has sent a voice note would be
    guessing; building it after twenty would be late.
    """
    with _lock_for(sender):
        conn = tracker.connect()
        case_id, _ = tracker.get_or_create_case(conn, sender)
        tracker.log_event(conn, case_id, "unsupported_media", "declined",
                          {"media_type": kind})
        log.info("case   : %s  unsupported media: %s", case_id, kind)
        try:
            transport().send(sender, UNSUPPORTED_MEDIA)
        except Exception:
            log.exception("could not send the unsupported-media reply")


def _handle_locked(sender: str, body: str) -> None:
    send = transport().send
    on_progress = (lambda msg: send(sender, msg)) if holding_enabled() else None

    conn = tracker.connect()
    case_id, is_new_case = tracker.get_or_create_case(conn, sender)

    try:
        answer = query.resolve(body, on_progress=on_progress)
    except groq_client.ModelUnavailable as e:
        # Distinguish "we are out of capacity, try again" from everything else.
        # After four retries a 429 means the free tier is genuinely saturated,
        # and telling someone to resend in a minute is true and actionable.
        # Any other ModelUnavailable is our problem, not something a resend
        # fixes, so it gets the handoff and a phone number instead.
        rate_limited = "429" in str(e)
        log.warning("model unavailable (%s) for case %s",
                    "rate limited" if rate_limited else str(e)[:120], case_id)
        tracker.log_event(conn, case_id, "model_unavailable",
                          "rate_limited" if rate_limited else "error",
                          {"detail": str(e)[:200]})
        try:
            send(sender, BUSY_REPLY if rate_limited
                 else query.with_contact(query.HANDOFF))
        except Exception:
            log.exception("could not send the fallback message either")
        return
    except Exception:
        # Never let a crash mean silence. The family gets the handoff and a real
        # phone number; the traceback goes to the log, where it belongs.
        log.exception("pipeline failed for an incoming message")
        tracker.log_event(conn, case_id, "pipeline_error", "error", None)
        try:
            send(sender, query.with_contact(query.HANDOFF))
        except Exception:
            log.exception("could not send the fallback message either")
        return

    # Provenance to the log, exactly as the CLI prints it. This is the record a
    # legal reviewer audits, and it must exist for messages sent to real people
    # at least as much as for test runs.
    log.info("case   : %s", case_id)
    log.info("route  : %s", answer.route)
    log.info("chunks : %s", answer.chunks or "(none)")
    log.info("rules  : %s", answer.rules or "(none)")

    # The same provenance, durably, where a legal partner can read it without
    # a terminal open. This is the Day-4 sign-off artefact.
    tracker.log_turn(conn, case_id, answer)

    text = answer.text
    if is_new_case:
        text += CASE_ID_LINE.format(case_id=case_id)

    try:
        send(sender, text)
    except Exception:
        log.exception("answer was produced but could not be delivered")


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(_app):
    # Loud, but not fatal: the server should still start so /health and the logs
    # are available while the .env is being fixed.
    meta_problem = meta_whatsapp.credentials_look_wrong()
    if meta_problem:
        log.warning("Meta WhatsApp not configured -> %s", meta_problem)
        twilio_problem = whatsapp.credentials_look_wrong()
        if twilio_problem:
            log.warning("Twilio not configured either -> %s", twilio_problem)
            log.warning("No WhatsApp transport available. Web chat still works.")
        else:
            log.info("Falling back to Twilio.")
    else:
        log.info("Meta WhatsApp configured, webhook is POST /meta")

    if holding_enabled():
        log.info("holding message ON - 2 outbound messages per question")
    else:
        # Warned, not just noted. Leaving this off on demo day means every
        # answer arrives after a silent twenty-second gap.
        log.warning(
            "holding message OFF (SEND_HOLDING=0) - 1 message per question. "
            "Remember to turn this back on before the demo."
        )

    # Assert the encoder is loaded, and say how long it took.
    #
    # This fork does NOT have the 16-second cold start seen elsewhere: query.py
    # computes MIN_SIMILARITY at module level via using_fallback_embedder(),
    # which constructs the embedder during import - so uvicorn pays the load
    # before it binds the port, and no family ever waits for it. Measured here
    # at 0.1s for exactly that reason.
    #
    # Kept anyway as a startup check: if retrieval is going to be unavailable,
    # the log says so at boot rather than on someone's first question.
    try:
        import ingest
        started = time.monotonic()
        ingest.embedder()(["warm up the encoder"])
        log.info("embedding model ready in %.1fs", time.monotonic() - started)
    except Exception as e:
        # Not fatal: the web page and /health should still come up so the
        # problem is diagnosable rather than invisible.
        log.warning("could not pre-warm the embedding model -> %s: %s",
                    type(e).__name__, e)

    yield


app = FastAPI(title="Factory accident support bot", lifespan=lifespan)


@app.get("/", response_class=HTMLResponse)
def chat_page() -> str:
    """
    The demo surface. Same pipeline as WhatsApp, no Twilio, no quota, no tunnel.

    Worth keeping even once WhatsApp works: it runs entirely on the presenter's
    laptop, so a dead conference network cannot take the demo with it.
    """
    return (Path(__file__).parent / "chat.html").read_text(encoding="utf-8")


@app.post("/chat")
async def chat(request: Request) -> dict:
    """
    Ask a question, get the answer AND its provenance.

    The provenance is returned rather than only logged, because the page shows
    it beside the answer: the point of the demo is that a viewer can see which
    law produced a reply and which gates fired, instead of taking it on trust.
    """
    payload = await request.json()
    question = (payload.get("question") or "").strip()
    if not question:
        return {"error": "empty question"}

    try:
        answer = query.resolve(question)
    except Exception:
        log.exception("pipeline failed for a web chat message")
        return {
            "text": query.with_contact(query.HANDOFF),
            "route": "error - see server log",
            "rules": [],
            "chunks": [],
            "labels": [],
        }

    log.info("web chat | route: %s | rules: %s", answer.route, answer.rules)
    return {
        "text": answer.text,
        "route": answer.route,
        "rules": answer.rules,
        "chunks": answer.chunks,
        "labels": answer.labels,
    }


@app.get("/health")
def health() -> dict:
    # key_source is reported because a stale `setx GROQ_API_KEY` silently beats
    # a working key in .env and returns 401 from some shells and not others.
    # "environment (overriding .env)" here is the one-line diagnosis for a
    # class of bug that otherwise costs an afternoon.
    return {
        "ok": True,
        "transport": transport().__name__,
        "meta": meta_whatsapp.credentials_look_wrong() or "configured",
        "twilio": whatsapp.credentials_look_wrong() or "configured",
        "holding_message": "on" if holding_enabled() else "off",
        "messages_per_question": 2 if holding_enabled() else 1,
        "groq_key": config.key_source("GROQ_API_KEY"),
        "whatsapp_token": config.key_source("WHATSAPP_ACCESS_TOKEN"),
        "cases_logged": _case_count(),
    }


def _case_count() -> int | str:
    try:
        conn = tracker.connect()
        return conn.execute("SELECT COUNT(*) AS c FROM cases").fetchone()["c"]
    except Exception as e:
        return f"unavailable: {type(e).__name__}"


@app.get("/meta")
async def meta_verify(request: Request) -> Response:
    """
    Meta's one-time webhook handshake. It GETs this URL with a token you chose
    and expects the challenge echoed back as plain text before it will deliver
    any message. A mismatch here shows in the dashboard only as "callback URL
    could not be validated".
    """
    q = request.query_params
    challenge = meta_whatsapp.verify_handshake(
        q.get("hub.mode", ""), q.get("hub.verify_token", ""), q.get("hub.challenge", "")
    )
    if challenge is None:
        log.warning("rejected a webhook handshake with a bad verify token")
        return Response(status_code=403)
    log.info("webhook handshake verified")
    return Response(content=challenge, media_type="text/plain")


@app.post("/meta")
async def meta_webhook(request: Request, background: BackgroundTasks) -> Response:
    raw = await request.body()

    if not meta_whatsapp.verify_signature(
        raw, request.headers.get("x-hub-signature-256", "")
    ):
        log.warning("rejected an unsigned request to /meta")
        return Response(status_code=403)

    payload = json.loads(raw or b"{}")

    # Always 200, even for receipts and unhandled types. Meta retries anything
    # else with backoff and eventually disables the webhook.
    for sid in meta_whatsapp.message_ids(payload):
        if _already_handled(sid):
            log.info("ignoring a retry of %s", sid)
            return Response(status_code=200)

    for sender, text in meta_whatsapp.extract_messages(payload):
        log.info("incoming message, %d chars", len(text))
        background.add_task(_handle, sender, text)

    for sender, kind in meta_whatsapp.non_text_messages(payload):
        log.info("incoming %s message - not supported yet", kind)
        background.add_task(_handle_non_text, sender, kind)

    return Response(status_code=200)


@app.post("/whatsapp")
async def whatsapp_webhook(
    request: Request,
    background: BackgroundTasks,
    From: str = Form(...),
    Body: str = Form(""),
    MessageSid: str = Form(""),
    x_twilio_signature: str = Header(default=""),
) -> Response:
    form = {k: v for k, v in (await request.form()).items()}

    # Twilio signs over the URL it actually called. Behind ngrok the app sees
    # http while Twilio signed https, so the scheme is taken from the forwarded
    # header when there is one: otherwise every real request fails the check.
    scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
    url = str(request.url.replace(scheme=scheme))

    if not whatsapp.verify_signature(url, form, x_twilio_signature):
        log.warning("rejected an unsigned request to /whatsapp")
        return Response(status_code=403)

    if MessageSid and _already_handled(MessageSid):
        log.info("ignoring a Twilio retry of %s", MessageSid)
        return Response(content="<Response/>", media_type="text/xml")

    text = Body.strip()
    if text:
        log.info("incoming message, %d chars", len(text))
        background.add_task(_handle, From, text)

    # Empty TwiML: acknowledge now, reply out of band. Putting the answer in
    # this response instead would mean holding the connection open for the
    # whole pipeline, which is what makes Twilio time out and retry.
    #
    # text/xml, not application/xml. Twilio logged error 12300 "Invalid
    # Content-Type" against every inbound message until this changed, the
    # message still arrived, but each one was recorded as a delivery failure.
    return Response(content="<Response/>", media_type="text/xml")
