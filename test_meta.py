#!/usr/bin/env python3
"""
Tests for the Meta WhatsApp Cloud API transport. Run: python test_meta.py

No network. Signature checking is the security boundary of the service, and the
receipt filter is what stops the bot answering its own delivery notifications,
so both are tested against hand-built payloads rather than against themselves.
"""

import hashlib
import hmac
import json
import os

import meta_whatsapp as meta

FAILS = 0
SECRET = "test_app_secret_not_real"


def check(name, cond):
    global FAILS
    print(("  PASS  " if cond else "  FAIL  ") + name)
    if not cond:
        FAILS += 1


def sign(raw: bytes, secret: str = SECRET) -> str:
    """Meta's algorithm, written independently of the implementation."""
    return "sha256=" + hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()


os.environ["WHATSAPP_PHONE_NUMBER_ID"] = "123456789012345"
os.environ["WHATSAPP_ACCESS_TOKEN"] = "EAAtest"
os.environ["WHATSAPP_APP_SECRET"] = SECRET
os.environ["WHATSAPP_VERIFY_TOKEN"] = "my-verify-token"


def envelope(msgs=None, statuses=None):
    value = {"messaging_product": "whatsapp", "metadata": {}}
    if msgs is not None:
        value["messages"] = msgs
    if statuses is not None:
        value["statuses"] = statuses
    return {"object": "whatsapp_business_account",
            "entry": [{"id": "1", "changes": [{"value": value, "field": "messages"}]}]}


TEXT_MSG = [{"from": "917453083224", "id": "wamid.AAA", "type": "text",
             "text": {"body": "they took his body away, what should we do?"}}]

print("\nsignature verification")
raw = json.dumps(envelope(TEXT_MSG)).encode()
check("a correctly signed body is accepted", meta.verify_signature(raw, sign(raw)))
check("a wrong signature is rejected", not meta.verify_signature(raw, "sha256=beef"))
check("an empty signature is rejected", not meta.verify_signature(raw, ""))
check("a bare hex digest without the prefix is rejected",
      not meta.verify_signature(raw, sign(raw)[len("sha256="):]))
check("a body signed with a different secret is rejected",
      not meta.verify_signature(raw, sign(raw, "wrong_secret")))

tampered = json.dumps(envelope(
    [{"from": "917453083224", "id": "wamid.AAA", "type": "text",
      "text": {"body": "the owner is offering money to sign"}}])).encode()
check("a tampered body invalidates the signature",
      not meta.verify_signature(tampered, sign(raw)))

# The digest is over raw bytes, so re-serialising the parsed JSON breaks it.
# This is the mistake that looks exactly like an attack in the logs.
reserialised = json.dumps(json.loads(raw), sort_keys=True).encode()
check("re-serialised JSON no longer matches (why raw bytes are required)",
      not meta.verify_signature(reserialised, sign(raw)))

print("\n  ...and with no app secret configured, nothing is trusted")
os.environ["WHATSAPP_APP_SECRET"] = ""
check("unconfigured server rejects a well-formed signature",
      not meta.verify_signature(raw, sign(raw)))
os.environ["WHATSAPP_APP_SECRET"] = SECRET

print("\nwebhook handshake")
check("correct token echoes the challenge",
      meta.verify_handshake("subscribe", "my-verify-token", "12345") == "12345")
check("wrong token refuses", meta.verify_handshake("subscribe", "nope", "12345") is None)
check("wrong mode refuses",
      meta.verify_handshake("unsubscribe", "my-verify-token", "12345") is None)

print("\nmessage extraction")
got = meta.extract_messages(envelope(TEXT_MSG))
check("a text message is extracted", got == [("917453083224", TEXT_MSG[0]["text"]["body"])])
check("message id is available for dedupe",
      meta.message_ids(envelope(TEXT_MSG)) == ["wamid.AAA"])

# Every answer the bot sends produces a delivery receipt on this same webhook.
# Answering one would make the bot reply to itself, forever.
receipt = envelope(statuses=[{"id": "wamid.OUT", "status": "delivered",
                             "recipient_id": "917453083224"}])
check("a delivery receipt yields no message", meta.extract_messages(receipt) == [])
check("a read receipt yields no message",
      meta.extract_messages(envelope(statuses=[{"status": "read"}])) == [])
check("an empty envelope yields no message", meta.extract_messages({}) == [])

check("a non-text message is ignored",
      meta.extract_messages(envelope(
          [{"from": "91745", "id": "w1", "type": "image",
            "image": {"id": "x"}}])) == [])
check("a text message with an empty body is ignored",
      meta.extract_messages(envelope(
          [{"from": "91745", "id": "w2", "type": "text",
            "text": {"body": "   "}}])) == [])

print("\ncredential shape checks")
os.environ["WHATSAPP_PHONE_NUMBER_ID"] = "+91745308322"
check("a phone NUMBER given instead of the phone number ID is caught",
      "not the phone number itself" in (meta.credentials_look_wrong() or ""))
os.environ["WHATSAPP_PHONE_NUMBER_ID"] = "123456789012345"
check("correctly shaped credentials pass", meta.credentials_look_wrong() is None)
os.environ["WHATSAPP_VERIFY_TOKEN"] = ""
check("a missing verify token is caught",
      "handshake" in (meta.credentials_look_wrong() or ""))
os.environ["WHATSAPP_VERIFY_TOKEN"] = "my-verify-token"

print("\nmessage splitting")
check("a short message is one part", meta.split_for_whatsapp("hello") == ["hello"])
paras = "\n\n".join(f"paragraph {i} " + "x" * 400 for i in range(30))
parts = meta.split_for_whatsapp(paras)
check("a long message is split", len(parts) > 1)
check("every part is within the limit", all(len(p) <= meta.MAX_BODY for p in parts))
check("no text is lost",
      "".join(parts).replace("\n", "").replace(" ", "")
      == paras.replace("\n", "").replace(" ", ""))

import query  # noqa: E402

settlement = query.with_contact(query.settlement_response())
sparts = meta.split_for_whatsapp(settlement)
check("the settlement warning survives splitting intact",
      "".join(sparts).replace("\n", "").replace(" ", "")
      == settlement.replace("\n", "").replace(" ", ""))
check("the legal aid number survives", "0161-2400051" in "".join(sparts))

print(f"\n{'ALL PASS' if not FAILS else str(FAILS) + ' FAILURE(S)'}\n")
raise SystemExit(1 if FAILS else 0)
