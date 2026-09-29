#!/usr/bin/env python3
"""
Meta WhatsApp Cloud API transport.

Replaces the Twilio path, which a trial account cannot use: Twilio required a
pre-approved template for every send, and a legal answer generated from
retrieved statute cannot be a template. Meta's Cloud API allows free-form text
inside the 24-hour window that opens when a person messages you first, which is
the only shape this bot ever needs, it never initiates a conversation.

Four differences from the Twilio adapter, all of which will bite if missed:

  * Auth is a Bearer token, not basic auth on an account SID.
  * The signature is HMAC-SHA256 over the RAW request body with the app secret,
    not SHA1 over the URL plus sorted form fields.
  * Meta verifies the webhook with a GET handshake before it will send anything.
  * Delivery receipts arrive on the same webhook as real messages, so anything
    that does not carry `messages` must be ignored rather than answered.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import urllib.error
import urllib.request

import config

config.load_env()

GRAPH_VERSION = "v21.0"

# Meta's own limit is 4096 characters for a text body. Answers are capped near
# 120 words so this should never fire, but the settlement warning plus the
# contact block is the longest thing the bot sends and losing the end of "do not
# sign anything" is not a risk worth carrying.
MAX_BODY = 3800


# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------


def _cfg() -> tuple[str, str, str, str]:
    return (
        os.environ.get("WHATSAPP_PHONE_NUMBER_ID", ""),
        os.environ.get("WHATSAPP_ACCESS_TOKEN", ""),
        os.environ.get("WHATSAPP_APP_SECRET", ""),
        os.environ.get("WHATSAPP_VERIFY_TOKEN", ""),
    )


def credentials_look_wrong() -> str | None:
    """Catch the setup mistakes at startup rather than on the first message."""
    phone_id, token, secret, verify = _cfg()
    if not phone_id:
        return "WHATSAPP_PHONE_NUMBER_ID missing from .env"
    if not phone_id.isdigit():
        return (
            f"WHATSAPP_PHONE_NUMBER_ID should be all digits, got {phone_id[:8]!r}: "
            "this is the Phone number ID from the API Setup page, not the "
            "phone number itself"
        )
    if not token:
        return "WHATSAPP_ACCESS_TOKEN missing from .env"
    if not secret:
        return "WHATSAPP_APP_SECRET missing, so inbound signatures cannot be verified"
    if not verify:
        return "WHATSAPP_VERIFY_TOKEN missing, so Meta's webhook handshake will fail"
    return None


# --------------------------------------------------------------------------
# Inbound: the security boundary
# --------------------------------------------------------------------------


def verify_signature(raw_body: bytes, header: str) -> bool:
    """
    Meta signs the raw request body with the app secret, as
    `X-Hub-Signature-256: sha256=<hex>`.

    It must be computed over the exact bytes received. Re-serialising the parsed
    JSON changes key order and whitespace and the digest stops matching, which
    looks identical to an attack. Without this check the endpoint is open to
    anyone who finds the URL, and every forged request spends real tokens from a
    free tier that allows one or two answers a minute.
    """
    _, _, secret, _ = _cfg()
    if not secret or not header or not header.startswith("sha256="):
        return False
    expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header[len("sha256="):])


def verify_handshake(mode: str, token: str, challenge: str) -> str | None:
    """
    Meta calls the webhook with GET once, at setup, and expects the challenge
    echoed back verbatim. Returns the challenge on success, None to refuse.
    """
    _, _, _, verify = _cfg()
    if mode == "subscribe" and verify and token == verify:
        return challenge
    return None


def extract_messages(payload: dict) -> list[tuple[str, str]]:
    """
    Pull (sender, text) out of Meta's envelope. Returns [] for anything else.

    Delivery receipts and read receipts arrive on this same webhook wrapped in
    the same structure, differing only in carrying `statuses` instead of
    `messages`. Treating one of those as an incoming message would answer a
    receipt: and since every outbound answer generates one, the bot would
    reply to itself in a loop.
    """
    out: list[tuple[str, str]] = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for msg in value.get("messages", []):
                if msg.get("type") != "text":
                    continue
                sender = msg.get("from", "")
                text = (msg.get("text", {}) or {}).get("body", "").strip()
                if sender and text:
                    out.append((sender, text))
    return out


def non_text_messages(payload: dict) -> list[tuple[str, str]]:
    """
    Pull (sender, media_type) for messages `extract_messages` skipped.

    Silence is the wrong answer to a voice note. Someone who records one has
    usually done it because typing is hard, and getting nothing back reads as
    being ignored rather than as a limitation of the bot.

    The type is returned as well as the sender so the log can answer a real
    question before voice is built: how often is voice actually attempted?
    """
    out: list[tuple[str, str]] = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            for msg in change.get("value", {}).get("messages", []):
                kind = msg.get("type", "unknown")
                sender = msg.get("from", "")
                if kind != "text" and sender:
                    out.append((sender, kind))
    return out


def message_ids(payload: dict) -> list[str]:
    """Message ids, for dropping Meta's retries of a webhook it thinks failed."""
    ids = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            for msg in change.get("value", {}).get("messages", []):
                if msg.get("id"):
                    ids.append(msg["id"])
    return ids


# --------------------------------------------------------------------------
# Outbound
# --------------------------------------------------------------------------


def split_for_whatsapp(text: str, limit: int = MAX_BODY) -> list[str]:
    """
    Split on paragraph boundaries, never mid-sentence.

    A legal instruction cut in half reads as a different instruction, "do not
    sign anything until" is worse than useless, so a long paragraph is sent
    whole and split on words only as a last resort.
    """
    if len(text) <= limit:
        return [text]

    parts: list[str] = []
    current = ""
    for para in text.split("\n\n"):
        if len(para) > limit:
            if current:
                parts.append(current)
                current = ""
            line = ""
            for w in para.split(" "):
                if len(line) + len(w) + 1 > limit:
                    parts.append(line.strip())
                    line = ""
                line += w + " "
            if line.strip():
                current = line.strip()
            continue
        if len(current) + len(para) + 2 > limit:
            parts.append(current)
            current = para
        else:
            current = f"{current}\n\n{para}" if current else para
    if current:
        parts.append(current)
    return parts


def send(to: str, body: str) -> None:
    """
    POST to the Cloud API. Long bodies go as several messages.

    Raises with Meta's own error text on failure, a send that fails silently
    means a family sat waiting for an answer that was never delivered.
    """
    phone_id, token, _, _ = _cfg()
    url = f"https://graph.facebook.com/{GRAPH_VERSION}/{phone_id}/messages"

    for chunk in split_for_whatsapp(body):
        payload = json.dumps(
            {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to,
                "type": "text",
                # preview_url off: a link preview would render an unverified
                # third-party page next to verified legal text.
                "text": {"preview_url": False, "body": chunk},
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=30):
                pass
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")
            try:
                err = json.loads(detail).get("error", {})
                detail = (
                    f"{err.get('code')}/{err.get('error_subcode')}: "
                    f"{err.get('message')}: {err.get('error_data', {}).get('details', '')}"
                )
            except ValueError:
                detail = detail[:300]
            raise RuntimeError(f"Meta refused the message -> {detail}") from e
