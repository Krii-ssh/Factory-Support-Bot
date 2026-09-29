#!/usr/bin/env python3
"""
Intent classification: the routing layer.

Spec: knowledge_base/08_intent_classification.md

Why this exists: measurement established that **scope cannot be decided by
similarity**. "What is the weather in Ludhiana" scored 0.653, above three
legitimate questions including "how much exactly will we get" at 0.598. The
bands are inverted in rank order, so no threshold and no rescaling separates
them. "Is this about a factory death at all?" is a classification question, so
it gets a classifier.

Order is the safety design:

    keyword pre-empt   (settlement pressure: never touches the network)
        -> LLM classifier
        -> route

The keyword check runs BEFORE the classifier rather than instead of it. The
classifier is a network call and can time out, rate-limit, or return junk. The
keyword check cannot. Settlement pressure is the one intent where a miss is
unrecoverable, a signature cannot be un-signed, so it gets a path that does
not depend on the network being up.
"""

from __future__ import annotations

import re
from pathlib import Path

import groq_client
from groq_client import ModelUnavailable

CLASSIFIER_MODEL = "openai/gpt-oss-20b"
REASONING_EFFORT = "low"

# A label is five tokens, so 20 looked generous. It is not: reasoning tokens
# come out of the same budget and never appear in `content`, so the model
# returned an empty content whenever its reasoning ran long. That failed
# silently into the fallback, letting out_of_scope questions reach the answer
# model: the exact failure this layer exists to prevent.
MAX_CLASSIFIER_TOKENS = 256

KEYWORD_FILE = Path(__file__).parent / "settlement_keywords.txt"

SETTLEMENT = "settlement_pressure"
BODY = "body_postmortem"
FIR = "fir_police"
DEATH = "death_case"
CASE_STATUS = "case_status"
OUT_OF_SCOPE = "out_of_scope"

LABELS = (SETTLEMENT, BODY, FIR, DEATH, CASE_STATUS, OUT_OF_SCOPE)

# Route per label. "fixed" and "handoff" never reach the answer model, that
# is the point of case 7, where the weather question was drafted and paid for.
ROUTE = {
    SETTLEMENT: "fixed",
    BODY: "rag",
    FIR: "rag",
    DEATH: "rag",
    CASE_STATUS: "handoff",
    OUT_OF_SCOPE: "handoff",
}

# When the classifier is unreachable or returns something unparseable, route to
# the main RAG flow rather than to handoff. Spec ordering rule 3: when torn
# between a real label and out_of_scope, pick the real label, retrieval and the
# metadata gates refuse safely on their own, whereas a handoff on a transport
# blip silences a family who asked a real question. Settlement pressure is
# already covered above this line by the keyword check.
FALLBACK = DEATH


# --------------------------------------------------------------------------
# Layer 1: keyword pre-empt. No network.
# --------------------------------------------------------------------------


def _load_keywords() -> tuple[list[str], list[str]]:
    """Latin phrases match on word boundaries; Indic phrases match anywhere."""
    latin, indic = [], []
    for line in KEYWORD_FILE.read_text(encoding="utf-8").splitlines():
        term = line.split("#", 1)[0].strip()
        if not term:
            continue
        (latin if term.isascii() else indic).append(term)
    return latin, indic


_LATIN, _INDIC = _load_keywords()
_LATIN_RE = re.compile(
    "|".join(rf"\b{re.escape(t)}\b" for t in _LATIN), re.I | re.U
)


def settlement_keyword_hit(question: str) -> str | None:
    """Return the phrase that fired, or None. Deterministic, offline."""
    m = _LATIN_RE.search(question)
    if m:
        return m.group(0).lower()
    for term in _INDIC:
        if term in question:
            return term
    return None


# --------------------------------------------------------------------------
# Layer 2: LLM classifier.
# --------------------------------------------------------------------------

CLASSIFIER_PROMPT = """You label incoming WhatsApp messages from families of factory accident
victims in Ludhiana, Punjab. Reply with exactly ONE label and nothing else.

LABELS:
settlement_pressure - being pushed to sign, take cash, give a thumb
  impression, accept "full and final", withdraw the case
body_postmortem - the body, post-mortem, inquest, cremation, "they took him
  away", "they say take him home"
fir_police - filing an FIR, police refusing, escalating to a senior officer,
  which section was applied, how the thana is behaving
death_case - compensation, entitlement, employer duty, ESI, contractor or
  thekedar, deadlines, what the family is owed
case_status - asking what is happening with their own case, or about a case ID
out_of_scope - anything else

RULES:
1. settlement_pressure wins over every other label whenever it is even
   plausibly present. It is the only irreversible harm here.
2. body_postmortem outranks the rest. Its window is hours.
3. If torn between a real label and out_of_scope, pick the real label.
4. If torn between two real labels, pick the higher-priority one, in the order
   above.
5. out_of_scope is a CORRECT and USEFUL answer, not a failure. Use it without
   hesitation for weather, cricket, phone recharge, ration cards, pensions,
   and any other government scheme. Do not stretch a message to fit a label.
6. If no death has been confirmed - a missing worker, a worker injured but
   alive - use out_of_scope. Nothing in this service addresses those, and
   improvising is worse than handing the family to a human.

EXAMPLES:
the owner is offering 2 lakh, is that enough? -> settlement_pressure
we already signed the paper -> settlement_pressure
they gave us money for the funeral, should we take it? -> settlement_pressure
they are saying take the body and go home -> body_postmortem
when will we get the post-mortem report? -> body_postmortem
police wrote the FIR but under a light section -> fir_police
the police are refusing to write the FIR -> fir_police
how much are we owed? -> death_case
he worked through a thekedar -> death_case
what does the Factories Act say? -> death_case
my husband died in a factory accident -> death_case
what is the weather in Ludhiana -> out_of_scope
how do I get a ration card -> out_of_scope
my husband is missing since the fire -> out_of_scope

Reply with one label only."""


def _call_classifier(question: str) -> str | None:
    """
    Shares the transport with the answer model, so rate limiting, retry and the
    empty-content check apply here too. They did not, and that is how this layer
    failed silently.
    """
    try:
        return groq_client.chat(
            CLASSIFIER_MODEL,
            CLASSIFIER_PROMPT,
            question,
            max_tokens=MAX_CLASSIFIER_TOKENS,
            temperature=0,
            reasoning_effort=REASONING_EFFORT,
            timeout=30,
        )
    except ModelUnavailable as e:
        return f"!{e}"


def _parse_label(raw: str | None) -> str | None:
    """Accept only an exact label. A chatty reply is a failure, not a guess."""
    if not raw or raw.startswith("!"):
        return None
    token = raw.strip().strip(".`\"' ").lower()
    return token if token in LABELS else None


# --------------------------------------------------------------------------


def classify(question: str) -> tuple[str, str, str]:
    """
    Returns (label, route, how) where `how` records which layer decided, so a
    reviewer auditing a transcript can tell a keyword hit from a model call
    from a fallback after the model was unreachable.
    """
    hit = settlement_keyword_hit(question)
    if hit:
        return SETTLEMENT, ROUTE[SETTLEMENT], f"keyword:{hit}"

    raw = _call_classifier(question)
    label = _parse_label(raw)
    if label is None:
        # Say which failure this was. "classifier_unavailable" covered a dead
        # network, an empty response and a chatty one that did not match a
        # label: three different bugs wearing the same name, which is how the
        # empty-response one survived a whole test run unnoticed.
        if raw and raw.startswith("!"):
            why = raw[1:60]
        else:
            why = f"unparseable:{(raw or '')[:24]!r}"
        return FALLBACK, ROUTE[FALLBACK], f"fallback:{why}"
    return label, ROUTE[label], "classifier"
