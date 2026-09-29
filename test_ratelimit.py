#!/usr/bin/env python3
"""
Tests for rate limiting and transport failure. Run: python test_ratelimit.py

These cover the demo-day failure: several people messaging the number at once,
against a free tier that allows one or two answers a minute. No network calls, 
the limiter is deterministic and the transport is stubbed.
"""

import json
import os
import threading
import time
import urllib.error
import urllib.request

import groq_client
import query
from groq_client import ModelUnavailable, RateLimiter, estimate_tokens

FAILS = 0


def check(name, cond):
    global FAILS
    print(("  PASS  " if cond else "  FAIL  ") + name)
    if not cond:
        FAILS += 1


print("\nbudget is reserved before the call, not recorded after")
# Two callers arriving together must not both see an empty window.
lim = RateLimiter(rpm=30, tpm=1000)
seen = []


def grab():
    seen.append(lim.reserve(600))


t1, t2 = threading.Thread(target=grab), threading.Thread(target=grab)
start = time.monotonic()
t1.start()
t2.start()
# One fits in the 1000-token window, the other must wait out the 60s window.
# Give them a moment, then confirm exactly one got through.
time.sleep(0.4)
check("second caller is still blocked, not fired alongside the first", len(seen) == 1)

print("\noversized prompt does not hang forever")
lim2 = RateLimiter(rpm=30, tpm=100)
done = threading.Event()
threading.Thread(target=lambda: (lim2.reserve(999_999), done.set()), daemon=True).start()
check("a prompt larger than the whole budget still returns", done.wait(timeout=2.0))

print("\nrequest ceiling is enforced independently of tokens")
lim3 = RateLimiter(rpm=2, tpm=10_000_000)
lim3.reserve(1)
lim3.reserve(1)
blocked = threading.Event()
threading.Thread(target=lambda: (lim3.reserve(1), blocked.set()), daemon=True).start()
check("third call blocked on RPM despite unlimited tokens", not blocked.wait(timeout=0.5))

print("\ntoken estimate over-estimates rather than under")
est = estimate_tokens("x" * 4400, query.MAX_OUTPUT_TOKENS)
check("counts prompt and reserves output headroom", est >= 1100 + query.MAX_OUTPUT_TOKENS - 1)

print("\nretryable vs fatal HTTP codes")

calls = {"n": 0}


def counting(code):
    def _f(*a, **kw):
        calls["n"] += 1
        e = urllib.error.HTTPError(groq_client.GROQ_URL, code, "err", {}, None)
        e.read = lambda: b"boom"
        raise e

    return _f


real_open, real_sleep = urllib.request.urlopen, time.sleep
groq_client.time.sleep = lambda s: None  # do not actually wait out the backoff
os.environ["GROQ_API_KEY"] = "test-key-not-real"

try:
    calls["n"] = 0
    urllib.request.urlopen = counting(400)
    try:
        query.call_groq("sys", "q")
        check("400 raises", False)
    except ModelUnavailable:
        check("400 raises ModelUnavailable", True)
    check("400 is not retried", calls["n"] == 1)

    calls["n"] = 0
    urllib.request.urlopen = counting(429)
    try:
        query.call_groq("sys", "q")
        check("429 raises after retries", False)
    except ModelUnavailable:
        check("429 raises ModelUnavailable after retries", True)
    check(
        f"429 is retried ({calls['n']} attempts)",
        calls["n"] == groq_client.MAX_RETRIES + 1,
    )
finally:
    urllib.request.urlopen = real_open
    groq_client.time.sleep = real_sleep
    os.environ.pop("GROQ_API_KEY", None)

print("\nempty content is a failure, not an answer")
# The classifier bug of 19 Aug 2026: max_tokens=20 was spent entirely on
# reasoning tokens, so the API returned 200 OK with content="" and
# finish_reason="length". That is a success at the HTTP layer and a total
# failure at every layer above it.


class _FakeResp:
    def __init__(self, payload):
        self._p = json.dumps(payload).encode()

    def read(self):
        return self._p

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


os.environ["GROQ_API_KEY"] = "test-key-not-real"
try:
    urllib.request.urlopen = lambda *a, **kw: _FakeResp(
        {"choices": [{"message": {"content": ""}, "finish_reason": "length"}]}
    )
    try:
        query.call_groq("sys", "q")
        check("empty content raises", False)
    except ModelUnavailable as e:
        check("empty content raises ModelUnavailable", True)
        check("failure names finish_reason", "length" in str(e))

    # And the classifier must not turn that into a confident label.
    import classify

    label, route, how = classify.classify("what is the weather in Ludhiana")
    check("classifier reports the real reason, not 'unavailable'", "empty" in how)
finally:
    urllib.request.urlopen = real_open
    os.environ.pop("GROQ_API_KEY", None)

print("\nmissing key is a ModelUnavailable, not a fake answer")
try:
    query.call_groq("sys", "q")
    check("no key raises", False)
except ModelUnavailable:
    check("no key raises ModelUnavailable", True)

print(f"\n{'ALL PASS' if not FAILS else str(FAILS) + ' FAILURE(S)'}\n")
raise SystemExit(1 if FAILS else 0)
