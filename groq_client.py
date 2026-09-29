#!/usr/bin/env python3
"""
One Groq transport for both the answer model and the classifier.

This exists because they drifted. The answer path had rate limiting, retry and
a typed failure; the classifier had a bare try/except that swallowed everything
and returned None, so when it started failing it looked exactly like the network
being down and went unnoticed through a whole test run.

Anything that calls Groq goes through here, so a protection added for one caller
cannot silently be missing from the other.
"""

from __future__ import annotations

import json
import os
import threading
import time
import urllib.error
import urllib.request

import config

config.load_env()

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# Groq sits behind Cloudflare, which rejects urllib's default User-Agent with a
# 403 "error code: 1010" before the request ever reaches the API. Any explicit
# UA passes. This was invisible until a key existed.
USER_AGENT = "factory-bot/0.1"

MAX_RETRIES = 4

# Free-tier ceilings, per ORGANISATION, extra API keys do not raise them.
# (requests/minute, tokens/minute). Tokens bind long before requests do on the
# answer model, because every prompt carries five chunks of statute.
MODEL_LIMITS = {
    "openai/gpt-oss-120b": (30, 8_000),
    "openai/gpt-oss-20b": (30, 8_000),
}
DEFAULT_LIMITS = (30, 6_000)

# Retrying a 400 or a 401 just burns a budget we do not have: those are our bug
# or our key. 429 is rate limiting and 5xx is Groq having a bad moment.
RETRYABLE = (429, 500, 502, 503, 504)


# --------------------------------------------------------------------------
# Failure type and rate limiting
# --------------------------------------------------------------------------


class ModelUnavailable(Exception):
    """
    Groq could not be reached, or the rate limit did not clear in time.

    Never shown to a family: callers degrade to the handoff message, the same
    thing they do when the knowledge base has no good answer. An HTTP status
    code is not theirs to read.
    """


class RateLimiter:
    """
    Trailing-60-second window over both ceilings.

    Budget is reserved BEFORE the request goes out rather than recorded after it
    returns. Two callers arriving together would otherwise both see an empty
    window and both fire.
    """

    def __init__(self, rpm: int, tpm: int):
        self._rpm, self._tpm = rpm, tpm
        self._calls: list[tuple[float, int]] = []
        self._lock = threading.Lock()

    def reserve(self, tokens: int) -> float:
        """Block until `tokens` fit in the window. Returns seconds waited."""
        # A prompt larger than the whole per-minute budget would never fit and
        # would spin forever. Clamp it: the request then 429s and is retried,
        # which is a real outcome, rather than hanging with no output.
        tokens = min(tokens, self._tpm)
        waited = 0.0
        while True:
            with self._lock:
                now = time.monotonic()
                self._calls = [(t, n) for t, n in self._calls if now - t < 60.0]
                used = sum(n for _, n in self._calls)
                if used + tokens <= self._tpm and len(self._calls) < self._rpm:
                    self._calls.append((now, tokens))
                    return waited
                sleep_for = max(0.05, 60.0 - (now - min(t for t, _ in self._calls)))
            time.sleep(sleep_for)
            waited += sleep_for


_limiters: dict[str, RateLimiter] = {}
_limiters_lock = threading.Lock()


def limiter_for(model: str) -> RateLimiter:
    """One limiter per model: the quotas are separate, so the windows are too."""
    with _limiters_lock:
        if model not in _limiters:
            rpm, tpm = MODEL_LIMITS.get(model, DEFAULT_LIMITS)
            _limiters[model] = RateLimiter(rpm, tpm)
        return _limiters[model]


def estimate_tokens(text: str, max_output: int) -> int:
    """
    Roughly four characters per token for English, plus the reply we asked for.

    Deliberately an over-estimate. gpt-oss is a reasoning model and its
    reasoning tokens bill against the same ceiling while never appearing in the
    response, so under-estimating here is what produces a surprise 429.
    """
    return len(text) // 4 + max_output


def _retry_after(err: urllib.error.HTTPError, attempt: int) -> float:
    """Prefer the server's own backoff; fall back to exponential."""
    try:
        return float(err.headers.get("retry-after", ""))
    except (TypeError, ValueError, AttributeError):
        return min(2.0**attempt, 30.0)


# --------------------------------------------------------------------------
# The one call everything goes through
# --------------------------------------------------------------------------


def chat(
    model: str,
    system: str,
    user: str,
    *,
    max_tokens: int,
    temperature: float = 0.2,
    reasoning_effort: str = "low",
    timeout: int = 60,
    on_wait=None,
) -> str:
    """
    Returns the assistant's message content. Raises ModelUnavailable otherwise.

    NOTE: `max_tokens` must cover REASONING as well as the reply on gpt-oss
    models. Reasoning tokens come out of this same budget and never appear in
    the content, so too small a value returns finish_reason=length with an empty
    content rather than an error: which is how the classifier failed
    intermittently on max_tokens=20 for a five-token label.
    """
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        raise ModelUnavailable("GROQ_API_KEY not set")

    body = json.dumps(
        {
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "reasoning_effort": reasoning_effort,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
    ).encode("utf-8")

    limiter = limiter_for(model)
    estimate = estimate_tokens(system + user, max_tokens)

    for attempt in range(MAX_RETRIES + 1):
        limiter.reserve(estimate)
        req = urllib.request.Request(
            GROQ_URL,
            data=body,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "User-Agent": USER_AGENT,
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                payload = json.load(r)
            choice = payload["choices"][0]
            content = (choice["message"].get("content") or "").strip()
            if not content:
                raise ModelUnavailable(
                    f"empty content, finish_reason={choice.get('finish_reason')}"
                    ", so max_tokens is probably too small for the reasoning"
                )
            return content
        except urllib.error.HTTPError as e:
            if e.code not in RETRYABLE or attempt == MAX_RETRIES:
                detail = e.read().decode("utf-8", "replace")[:200]
                raise ModelUnavailable(f"HTTP {e.code}: {detail}") from e
            delay = _retry_after(e, attempt)
            if on_wait:
                on_wait(delay, attempt + 1)
            time.sleep(delay)
        except ModelUnavailable:
            raise
        except Exception as e:  # network down, DNS, timeout, malformed payload
            if attempt == MAX_RETRIES:
                raise ModelUnavailable(f"{type(e).__name__}: {e}") from e
            delay = min(2.0**attempt, 30.0)
            if on_wait:
                on_wait(delay, attempt + 1)
            time.sleep(delay)

    raise ModelUnavailable("retries exhausted")
