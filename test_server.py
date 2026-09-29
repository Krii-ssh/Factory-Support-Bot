#!/usr/bin/env python3
"""
End-to-end webhook tests. Run: py -3.11 test_server.py

Drives the real FastAPI app with simulated Twilio requests. Nothing is sent and
no model is called, Twilio's send and the pipeline are both stubbed, so this
proves the wiring rather than the answers, which the other suites cover.

Needs the full stack (fastapi, uvicorn, python-multipart, httpx, chromadb).
"""

import base64
import hashlib
import hmac
import os

TOKEN = "test_auth_token_not_real"
os.environ["TWILIO_ACCOUNT_SID"] = "AC" + "0" * 32
os.environ["TWILIO_AUTH_TOKEN"] = TOKEN
os.environ["TWILIO_WHATSAPP_FROM"] = "whatsapp:+14155238886"

import query  # noqa: E402
import server  # noqa: E402
import whatsapp  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

FAILS = 0
SENT: list[tuple[str, str]] = []


def check(name, cond):
    global FAILS
    print(("  PASS  " if cond else "  FAIL  ") + name)
    if not cond:
        FAILS += 1


# Stub the transport and the pipeline. load_env() would otherwise overwrite the
# test credentials above with whatever is in the real .env.
whatsapp.send = lambda to, body: SENT.append((to, body))
server.whatsapp.send = whatsapp.send
whatsapp.load_env = lambda *a, **kw: None

_FAKE = query.Answer(
    text="Do not let the body go without a post-mortem.",
    route="RAG -> test",
    rules=["INTENT_body_postmortem:classifier"],
)


def fake_resolve(question, *, on_progress=None):
    if on_progress:
        on_progress(query.HOLDING)
    return _FAKE


server.query.resolve = fake_resolve

URL = "http://testserver/whatsapp"
client = TestClient(server.app)


def sign(form, url=URL):
    payload = url + "".join(f"{k}{form[k]}" for k in sorted(form))
    return base64.b64encode(
        hmac.new(TOKEN.encode(), payload.encode(), hashlib.sha1).digest()
    ).decode()


def post(form, signature=None):
    return client.post(
        "/whatsapp",
        data=form,
        headers={"X-Twilio-Signature": signature if signature is not None else sign(form)},
    )


print("\nunsigned requests are refused")
form = {"From": "whatsapp:+919876543210", "Body": "hello", "MessageSid": "SM_a"}
check("a forged request gets 403", post(form, signature="forged").status_code == 403)
check("nothing was sent for it", SENT == [])

print("\na properly signed message is answered")
SENT.clear()
r = post(form)
check("returns 200", r.status_code == 200)
check("returns TwiML", "<Response/>" in r.text)
check("two messages sent: holding, then answer", len(SENT) == 2)
check("holding message goes first", SENT[0][1] == query.HOLDING)
check("answer follows", SENT[1][1] == _FAKE.text)
check("both go to the sender", all(to == form["From"] for to, _ in SENT))

print("\na Twilio retry does not answer twice")
SENT.clear()
r = post(form)  # same MessageSid
check("retry returns 200", r.status_code == 200)
check("but sends nothing", SENT == [])

print("\na new message is answered again")
SENT.clear()
form2 = dict(form, MessageSid="SM_b", Body="the police refuse to write the FIR")
post(form2)
check("new MessageSid is processed", len(SENT) == 2)

print("\nan empty body is ignored")
SENT.clear()
post(dict(form, MessageSid="SM_c", Body="   "))
check("whitespace-only message sends nothing", SENT == [])

print("\na pipeline crash still reaches the family")
SENT.clear()


def exploding(question, *, on_progress=None):
    raise RuntimeError("retrieval died")


server.query.resolve = exploding
post(dict(form, MessageSid="SM_d", Body="what are we owed?"))
check("a crash still sends one message", len(SENT) == 1)
check("and it carries the legal aid number", "0161-2400051" in SENT[0][1])
server.query.resolve = fake_resolve

print("\nSEND_HOLDING protects the trial message budget")
SENT.clear()
os.environ["SEND_HOLDING"] = "0"
post(dict(form, MessageSid="SM_e", Body="what are we owed?"))
check("with SEND_HOLDING=0, one message per question", len(SENT) == 1)
check("and it is the answer, not the holding text", SENT[0][1] == _FAKE.text)

for off in ("false", "no", "off", "0"):
    SENT.clear()
    os.environ["SEND_HOLDING"] = off
    post(dict(form, MessageSid=f"SM_off_{off}", Body="what are we owed?"))
    check(f"SEND_HOLDING={off!r} disables it", len(SENT) == 1)

SENT.clear()
os.environ["SEND_HOLDING"] = "1"
post(dict(form, MessageSid="SM_f", Body="what are we owed?"))
check("back on, two messages again", len(SENT) == 2)

del os.environ["SEND_HOLDING"]
SENT.clear()
post(dict(form, MessageSid="SM_g", Body="what are we owed?"))
check("default with the flag unset is ON", len(SENT) == 2)

print("\nhealth endpoint")
h = client.get("/health").json()
check("reports ok", h.get("ok") is True)
check("reports credential state", h.get("twilio") == "configured")

print(f"\n{'ALL PASS' if not FAILS else str(FAILS) + ' FAILURE(S)'}\n")
raise SystemExit(1 if FAILS else 0)
