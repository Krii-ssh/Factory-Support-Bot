#!/usr/bin/env python3
"""
Tests for the WhatsApp transport. Run: python test_whatsapp.py

No network. Signature checking is the security boundary of the whole service, 
an unsigned request that gets answered spends real tokens from a free tier that
allows one or two answers a minute, so it is tested against Twilio's published
algorithm rather than against itself.
"""

import base64
import hashlib
import hmac
import os

import whatsapp

FAILS = 0
TOKEN = "test_auth_token_not_real"


def check(name, cond):
    global FAILS
    print(("  PASS  " if cond else "  FAIL  ") + name)
    if not cond:
        FAILS += 1


def sign(url, form, token=TOKEN):
    """Twilio's algorithm, written independently of the implementation."""
    payload = url + "".join(f"{k}{form[k]}" for k in sorted(form))
    return base64.b64encode(
        hmac.new(token.encode(), payload.encode(), hashlib.sha1).digest()
    ).decode()


os.environ["TWILIO_ACCOUNT_SID"] = "AC" + "0" * 32
os.environ["TWILIO_AUTH_TOKEN"] = TOKEN
os.environ["TWILIO_WHATSAPP_FROM"] = "whatsapp:+14155238886"

URL = "https://example.ngrok.io/whatsapp"
FORM = {"From": "whatsapp:+919876543210", "Body": "my husband died", "MessageSid": "SM1"}

print("\nsignature verification")
check("a correctly signed request is accepted", whatsapp.verify_signature(URL, FORM, sign(URL, FORM)))
check("a wrong signature is rejected", not whatsapp.verify_signature(URL, FORM, "nope"))
check("an empty signature is rejected", not whatsapp.verify_signature(URL, FORM, ""))

tampered = dict(FORM, Body="the owner is offering money to sign")
check(
    "a tampered body invalidates the signature",
    not whatsapp.verify_signature(URL, tampered, sign(URL, FORM)),
)
check(
    "a different URL invalidates the signature",
    not whatsapp.verify_signature("https://evil.test/whatsapp", FORM, sign(URL, FORM)),
)

print("\n  ...and with no auth token configured, nothing is trusted")
os.environ["TWILIO_AUTH_TOKEN"] = ""
check(
    "unconfigured server rejects even a well-formed signature",
    not whatsapp.verify_signature(URL, FORM, sign(URL, FORM)),
)
os.environ["TWILIO_AUTH_TOKEN"] = TOKEN

print("\ncredential shape checks")
os.environ["TWILIO_ACCOUNT_SID"] = "SK" + "0" * 32
check("an SK account SID is caught", "expected 'AC'" in (whatsapp.credentials_look_wrong() or ""))
os.environ["TWILIO_ACCOUNT_SID"] = "AC" + "0" * 32
os.environ["TWILIO_AUTH_TOKEN"] = "SK" + "0" * 32
check("an SK auth token is caught", "API Key SID" in (whatsapp.credentials_look_wrong() or ""))
os.environ["TWILIO_AUTH_TOKEN"] = TOKEN
check("correctly shaped credentials pass", whatsapp.credentials_look_wrong() is None)

print("\nmessage splitting")
check("a short message is one part", whatsapp.split_for_whatsapp("hello") == ["hello"])

paras = "\n\n".join(f"paragraph {i} " + "x" * 200 for i in range(20))
parts = whatsapp.split_for_whatsapp(paras)
check("a long message is split", len(parts) > 1)
check("every part is within the limit", all(len(p) <= whatsapp.MAX_BODY for p in parts))
check(
    "no text is lost in the split",
    "".join(parts).replace("\n", "").replace(" ", "")
    == paras.replace("\n", "").replace(" ", ""),
)

# The message that must never arrive truncated.
import query

settlement = query.with_contact(query.settlement_response())
sparts = whatsapp.split_for_whatsapp(settlement)
check(
    "the settlement warning survives splitting intact",
    "".join(sparts).replace("\n", "").replace(" ", "")
    == settlement.replace("\n", "").replace(" ", ""),
)
check(
    "the legal aid number is still present after splitting",
    "0161-2400051" in "".join(sparts),
)

single = "word " * 800
check(
    "one huge paragraph is still split rather than dropped",
    all(len(p) <= whatsapp.MAX_BODY for p in whatsapp.split_for_whatsapp(single)),
)

print(f"\n{'ALL PASS' if not FAILS else str(FAILS) + ' FAILURE(S)'}\n")
raise SystemExit(1 if FAILS else 0)
