#!/usr/bin/env python3
"""
Twilio WhatsApp transport: config, signature checking, sending, splitting.

No Twilio SDK. The three things needed here, an HMAC check, a form POST and a
string split: are a few lines of standard library each, and the SDK is a large
dependency to add to a project whose whole argument is that it keeps its moving
parts few and inspectable.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import urllib.error
import urllib.parse
import urllib.request

import config

# WhatsApp rejects bodies over 1600 characters. Answers are capped near 120
# words so this should never fire: but the settlement message plus the contact
# block is the longest thing the bot sends, and silently losing the end of the
# "do not sign anything" message is not a failure worth risking.
MAX_BODY = 1500

load_env = config.load_env


def _creds() -> tuple[str, str, str]:
    sid = os.environ.get("TWILIO_ACCOUNT_SID", "")
    token = os.environ.get("TWILIO_AUTH_TOKEN", "")
    sender = os.environ.get("TWILIO_WHATSAPP_FROM", "")
    return sid, token, sender


def credentials_look_wrong() -> str | None:
    """
    Catch the two mistakes that cost an afternoon each, at startup rather than
    on the first message.

    An Account SID starts with "AC". An "SK" value is an API Key SID, which is
    a different credential used with a separate secret, pasting one in as the
    account SID or the auth token authenticates against nothing and returns a
    generic 401.
    """
    sid, token, sender = _creds()
    if not sid or not token:
        return "TWILIO_ACCOUNT_SID or TWILIO_AUTH_TOKEN missing from .env"
    if not sid.startswith("AC"):
        return f"TWILIO_ACCOUNT_SID starts with {sid[:2]!r}, expected 'AC'"
    if token.startswith("SK"):
        return (
            "TWILIO_AUTH_TOKEN looks like an API Key SID (starts 'SK'). "
            "The Auth Token is the value under the Account SID on the console "
            "dashboard, and has no letter prefix."
        )
    if not sender.startswith("whatsapp:"):
        return "TWILIO_WHATSAPP_FROM should look like 'whatsapp:+14155238886'"
    return None


# --------------------------------------------------------------------------
# Inbound: the security boundary
# --------------------------------------------------------------------------


def verify_signature(url: str, form: dict[str, str], signature: str) -> bool:
    """
    Twilio signs each webhook: HMAC-SHA1 over the full URL with every POST
    parameter appended in key order, keyed by the auth token.

    Without this the endpoint is open to anyone who finds it, and every forged
    request spends real tokens from a free tier that allows one or two answers
    a minute. An unsigned request is not a user, so it does not get an answer.
    """
    _, token, _ = _creds()
    if not token or not signature:
        return False
    payload = url + "".join(f"{k}{form[k]}" for k in sorted(form))
    digest = hmac.new(
        token.encode("utf-8"), payload.encode("utf-8"), hashlib.sha1
    ).digest()
    return hmac.compare_digest(base64.b64encode(digest).decode(), signature)


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
            words, line = para.split(" "), ""
            for w in words:
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
    POST to Twilio's Messages endpoint. Long bodies go as several messages.

    Raises on failure so the caller can log it, a send that silently fails
    means a family sat waiting for an answer that was never delivered.
    """
    sid, token, sender = _creds()
    endpoint = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
    auth = base64.b64encode(f"{sid}:{token}".encode()).decode()

    for chunk in split_for_whatsapp(body):
        data = urllib.parse.urlencode(
            {"From": sender, "To": to, "Body": chunk}
        ).encode()
        req = urllib.request.Request(
            endpoint,
            data=data,
            headers={
                "Authorization": f"Basic {auth}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=30):
                pass
        except urllib.error.HTTPError as e:
            # Twilio explains itself in the body: a numeric code and a
            # sentence naming the actual problem. Letting urllib raise a bare
            # "HTTP Error 400: Bad Request" throws that away and leaves nothing
            # to debug from, which is exactly what happened on the first real
            # message.
            detail = e.read().decode("utf-8", "replace")
            try:
                payload = json.loads(detail)
                detail = (
                    f"{payload.get('code')}: {payload.get('message')} "
                    f"({payload.get('more_info', '')})"
                )
            except ValueError:
                detail = detail[:300]
            raise RuntimeError(f"Twilio refused the message -> {detail}") from e
