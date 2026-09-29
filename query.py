#!/usr/bin/env python3
"""
Retrieval core for the factory-accident support bot.

    python query.py "my husband died in a factory accident, what are we owed?"
    python query.py --test

Order of operations is the safety design, not an implementation detail:

    intent classification            (classify.py, keyword, then classifier)
        -> settlement pressure       -> fixed text, never reaches RAG at all
        -> out_of_scope/case_status  -> handoff, retrieval and LLM not called
        -> retrieve top-K
        -> hard metadata gates       (apply_filters, from ingest.py)
        -> similarity threshold      (LLM is never called below it)
        -> LLM, with rules built from answer_constraints()
        -> output validator          (validate_answer: what reaches the USER)

The threshold sits AFTER the gates so a repealed-but-relevant chunk cannot
score its way past, and BEFORE the LLM so a weak context is never drafted
from and then judged. Classification sits above all of it because similarity
cannot decide scope: see classify.py.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import classify
import config
import groq_client
from groq_client import ModelUnavailable
from ingest import (
    Chunk,
    answer_constraints,
    apply_filters,
    embedder,
    using_fallback_embedder,
)

# --------------------------------------------------------------------------
# Tunables
# --------------------------------------------------------------------------

# A floor against nonsense, not a relevance gate. Off-topic questions score
# ABOVE legitimate ones here: the weather question hit 0.653 while "how much
# exactly will we get" hit 0.598, so no threshold separates them. Scope is
# decided by the classifier instead; see classify.py.
#
# Calibrated per embedder, because the scale does not transfer:
# sentence-transformers spans 0.598-0.776 over the test questions, chroma's
# ONNX fallback spans 0.242-0.551 because it truncates chunks at 256 tokens.
# See embedder() in ingest.py. The ONNX figure is provisional, from one run.
_ST_MIN_SIMILARITY = 0.55
_ONNX_MIN_SIMILARITY = 0.20
MIN_SIMILARITY = (
    _ONNX_MIN_SIMILARITY if using_fallback_embedder() else _ST_MIN_SIMILARITY
)

# Spec says 5. Measured consequence: the s.76 death-formula chunk ranked #7 on
# its own flagship question, so it fell outside the window and the figure gate
# never armed. Fixed in the corpus rather than here, the chunk now opens in the
# register families actually use and ranks #1. Raise to 7 if that regresses.
TOP_K = 5
COLLECTION = "factory_bot_kb"

# Absolute, not "./chroma". A relative path resolves against the working
# directory, so the store was found when running from the project folder and
# silently missing when uvicorn was started from anywhere else, which is how
# the first real WhatsApp message died on "Collection does not exist".
#
# Resolved by config so ingest and query cannot disagree about where the store
# lives. Set CHROMA_PATH to move it onto a mounted disk; unset, it is the
# project folder exactly as before.
CHROMA_PATH = str(config.CHROMA_PATH)

# Both models originally specified are retired: neither appears in
# GET /v1/models, and llama-3.1-8b-instant 404s as model_not_found. The
# classifier runs on the smaller sibling so it stays off the answer model's
# quota, which is the tighter of the two.
ANSWER_MODEL = "openai/gpt-oss-120b"      # was llama-3.3-70b-versatile (retired)
CLASSIFIER_MODEL = "openai/gpt-oss-20b"   # was llama-3.1-8b-instant (retired)

# gpt-oss are reasoning models: reasoning tokens land in a separate `reasoning`
# field but still bill against the observed 8,000 TPM ceiling. "low" cuts them
# ~5x (122 -> 26 on a two-sentence answer) without touching answer quality.
REASONING_EFFORT = "low"

KB_DIR = Path(__file__).parent / "knowledge_base"

HANDOFF = (
    "I don't have reliable information on this specific point — let me "
    "connect you with free legal aid."
)

# Sent the moment we know the answer model is going to be called, before the
# call starts. On WhatsApp a twenty-second silence reads as broken and people
# re-send, which costs another slot in an already tight token budget. This
# reads as deliberate: and it is true: retrieval and validation are running.
HOLDING = "One moment, I'm checking this against the law."

# Case status needs its own words. The generic handoff says "I don't have
# reliable information on this point", which reads as evasion to someone asking
# what is happening with their own case.
CASE_STATUS_HANDOFF = (
    "I can't check the status of your case yet. The legal aid office below "
    "has your file and can tell you where it has reached."
)

# The one contact anyone has actually dialled. Appended by code AFTER
# validation; it never enters the model's context, so the model cannot corrupt
# it. Becomes a SQLite lookup once the rest of the directory is phone-verified.
CONTACT_LINE = (
    "District Legal Services Authority, Ludhiana — ADR Centre, Ground Floor, "
    "Additional Block, District Courts Complex, Ludhiana — 0161-2400051"
)
CONTACT_BLOCK = f"Free legal help, and it costs you nothing:\n{CONTACT_LINE}"

REFUSAL_LOG = Path(__file__).parent / "refusals.jsonl"

SYSTEM_PROMPT = """You are a legal-rights assistant for families of factory accident victims in
Punjab, India.

RULES (do not break these):
1. Answer ONLY using the CONTEXT below. Never use outside knowledge.
2. If the context doesn't clearly answer the question, say: "I don't have
   reliable information on this specific point — let me connect you with free
   legal aid" and stop. Do not guess or generalise.
3. Write in simple, warm, plain language. The reader may be grieving and
   unfamiliar with legal terms. Short sentences.
3a. Keep the answer under 120 words — about 4 or 5 short sentences plus the
   closing line. It will be read on a phone, often aloud by a neighbour, and
   may be spoken back as audio. A grieving person can hold two points, not six.
3b. Give ONE next action, not a checklist. If there is more to say, say the
   most urgent thing and offer the rest if they ask. For a fresh death that
   next action is almost always the post-mortem.
3c. Do NOT open with condolences. No "I am sorry for your loss". Lead with the
   useful thing. Warmth belongs in plain language, not in a sympathy sentence.
4. End every substantive answer with exactly this sentence and then stop:
   "This is general information, not a lawyer's advice — your case may differ."
   Never write a phone number, email address, website or office address.
   Contact details are added afterwards by the system, not by you.
5. {figure_rule}
6. {citation_rule}

CONTEXT:
{retrieved_chunks}

QUESTION:
{user_question}"""

NO_FIGURES = (
    "Do NOT state any rupee amount or calculated figure. Explain what the "
    "family is entitled to and how it is worked out, but say the exact amount "
    "must be confirmed with legal aid."
)
FIGURES_OK = (
    "You may repeat a rupee amount only if it appears verbatim in the "
    "CONTEXT. Never calculate, estimate or total a figure yourself."
)
NO_CITATIONS = "Do NOT cite any section number or Act name."
CITATIONS_OK = (
    "You may cite a section number or Act name only if it appears verbatim "
    "in the CONTEXT. Never reconstruct one from memory."
)

# --------------------------------------------------------------------------
# Settlement pressure: pre-empts retrieval entirely.
#
# The trigger vocabulary moved to settlement_keywords.txt so a Punjabi speaker
# can extend it without touching logic; the keyword layer and the classifier
# both live in classify.py.
# --------------------------------------------------------------------------


def settlement_response() -> str:
    """
    Lift the fixed, pre-approved text out of the design doc.

    Read from the file rather than pasted here so the legal reviewer edits
    one place. 03 is `index: false`, so this text is never embedded and can
    never be reached by retrieval: only by this hardcoded path.
    """
    src = (KB_DIR / "03_esi_fork_and_settlement.md").read_text(encoding="utf-8")
    lines = src.splitlines()
    start = next(
        i for i, ln in enumerate(lines)
        if ln.startswith("###") and "BOT COPY" in ln and "settlement-pressure" in ln
    )

    quoted: list[str] = []
    for ln in lines[start + 1:]:
        if ln.startswith("#"):
            break
        if ln.startswith(">"):
            quoted.append(ln.lstrip(">").strip())
        elif quoted and not ln.strip():
            quoted.append("")

    body = "\n".join(quoted).replace("*", "").replace('"', "")
    paras = [" ".join(p.split()) for p in body.split("\n\n") if p.strip()]
    return "\n\n".join(paras)


# --------------------------------------------------------------------------
# Retrieval
# --------------------------------------------------------------------------

_CHUNK_FIELDS = {
    f for f in Chunk.__dataclass_fields__ if f not in ("text", "warnings")
}


def to_chunk(meta: dict, text: str) -> Chunk:
    """Rebuild a Chunk from Chroma metadata so the gates can be reused as-is."""
    return Chunk(text=text, **{k: v for k, v in meta.items() if k in _CHUNK_FIELDS})


def similarity(distance: float) -> float:
    """
    Chroma's default space is squared L2. all-MiniLM-L6-v2 emits unit-norm
    vectors, so d2 = 2 - 2*cos and cosine falls out directly.
    """
    return 1.0 - distance / 2.0


def retrieve(question: str):
    import chromadb

    client = chromadb.PersistentClient(path=CHROMA_PATH)
    coll = client.get_collection(COLLECTION, embedding_function=embedder())
    res = coll.query(query_texts=[question], n_results=TOP_K)

    out = []
    for meta, doc, dist in zip(
        res["metadatas"][0], res["documents"][0], res["distances"][0]
    ):
        out.append((to_chunk(meta, doc), similarity(dist)))
    return out


MAX_OUTPUT_TOKENS = 800


def call_groq(system_prompt: str, question: str, *, on_wait=None) -> str:
    """
    Rate limiting, retry and the empty-content check live in groq_client, shared
    with the classifier: see the note at the top of that module for why.
    """
    return groq_client.chat(
        ANSWER_MODEL,
        system_prompt,
        question,
        max_tokens=MAX_OUTPUT_TOKENS,
        temperature=0.2,
        reasoning_effort=REASONING_EFFORT,
        on_wait=on_wait,
    )


# --------------------------------------------------------------------------
# Output validator: the post-generation gate. Deterministic, no LLM.
#
# The pre-generation gate controls what the model SEES. This controls what
# reaches the USER. Neither relies on the model choosing to obey.
# Runs on the raw generation, before the contact block is appended, the
# verified number would otherwise trip Check 1 itself.
# --------------------------------------------------------------------------

_EMAIL = re.compile(r"[^\s@]+@[^\s@]+\.[A-Za-z]{2,}")
_URL = re.compile(
    r"https?://\S+|www\.\S+|\b[\w-]+\.(?:com|org|net|in|gov|edu)\b", re.I
)
# A digit run allowing phone-ish separators. Commas are deliberately excluded
# so Indian money grouping (15,000) never reads as a phone number.
_DIGIT_RUN = re.compile(r"\d[\d\s().\-]*\d")
# Must end on a digit, or "…Sanhita, 2023, the police" yields "2023," and
# then fails grounding on the trailing comma.
_NUMBER = re.compile(r"\d(?:[\d,]*\d)?(?:\.\d+)?")
_SECTION = re.compile(r"\b(?:sections?|sec\.|s\.)\s*(\d+[A-Z]?)", re.I)

ACT_NAMES = (
    "Code on Social Security", "Bharatiya Nagarik Suraksha Sanhita",
    "Bharatiya Nyaya Sanhita", "BNSS", "BNS",
    "Occupational Safety, Health and Working Conditions Code", "OSHWC",
    "Factories Act", "Employee's Compensation Act",
    "Employees' Compensation Act", "Employees' State Insurance", "ESI Act",
)


def _phone_like(text: str) -> list[str]:
    """Digit runs of 7+ digits, per the spec."""
    out = []
    for m in _DIGIT_RUN.finditer(text):
        run = m.group(0)
        if sum(c.isdigit() for c in run) >= 7:
            out.append(run.strip())
    return out


def _verbatim(needle: str, haystack: str) -> bool:
    """Standalone occurrence, so '50' is not satisfied by '150'."""
    return re.search(
        rf"(?<![\d,.]){re.escape(needle)}(?![\d,.])", haystack
    ) is not None


def validate_answer(answer: str, context: str) -> tuple[bool, str, list[str]]:
    """
    Returns (ok, failed_check, offending_items).

    Any failure means: do not send. Return the handoff instead.
    """
    # Check 1: no contact details from the model, ever.
    bad = (_EMAIL.findall(answer) + _URL.findall(answer) + _phone_like(answer))
    if bad:
        return False, "CHECK1_contact_details", sorted(set(bad))

    # Check 3 runs before Check 2. An invented "Section 999" is caught by both
    # (999 is also an ungrounded number); reporting it as a citation failure
    # rather than a figure failure keeps the refusal log diagnostic.
    #
    # Section numbers are compared as numbers, not as literal strings: the
    # corpus writes "s.85(4)" where the model writes "Section 85(4)", and
    # refusing on notation would catch correct citations while missing the
    # actual risk, which the spec names as invention.
    ctx_sections = {s.lower() for s in _SECTION.findall(context)}
    bad_sections = [
        s for s in dict.fromkeys(_SECTION.findall(answer))
        if s.lower() not in ctx_sections
    ]
    if bad_sections:
        return False, "CHECK3_ungrounded_section", bad_sections

    bad_acts = [
        a for a in ACT_NAMES
        if re.search(rf"\b{re.escape(a)}\b", answer, re.I)
        and not re.search(rf"\b{re.escape(a)}\b", context, re.I)
    ]
    if bad_acts:
        return False, "CHECK3_ungrounded_act_name", bad_acts

    # Check 2: every figure must be grounded verbatim in the context.
    ungrounded = [
        n for n in dict.fromkeys(_NUMBER.findall(answer))
        if not _verbatim(n, context)
    ]
    if ungrounded:
        return False, "CHECK2_ungrounded_figure", ungrounded

    return True, "", []


def log_refusal(question: str, answer: str, check: str, items: list[str]) -> None:
    """Check 4. A refusal is a signal that the knowledge base has a gap."""
    rec = {
        "question": question,
        "check": check,
        "offending": items,
        "generated": answer,
    }
    with REFUSAL_LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def with_contact(text: str) -> str:
    """Attach the verified contact by concatenation, after validation."""
    if "[legal aid contact]" in text:
        return text.replace("[legal aid contact]", CONTACT_LINE)
    return f"{text}\n\n{CONTACT_BLOCK}"


# --------------------------------------------------------------------------
# One question, end to end
# --------------------------------------------------------------------------


@dataclass
class Answer:
    """
    What the pipeline decided, separated from how it is displayed.

    The CLI prints this; the WhatsApp adapter sends `text` and logs the rest.
    Provenance travels WITH the answer rather than being printed as a side
    effect, so the transport cannot accidentally ship an answer while dropping
    the record of which law produced it.
    """

    text: str
    route: str
    chunks: list = field(default_factory=list)
    labels: list = field(default_factory=list)
    rules: list = field(default_factory=list)


def show(a: Answer) -> None:
    """Provenance on every run. This is what the legal reviewer audits."""
    print(a.text)
    print("\n" + "-" * 70)
    print(f"route            : {a.route}")
    print(f"chunks used      : {a.chunks or '(none)'}")
    print(f"citation labels  : {a.labels or '(none)'}")
    print(f"rules fired      : {a.rules or '(none)'}")
    print("-" * 70)


def resolve(question: str, *, on_progress=None) -> Answer:
    """
    One question, end to end. Returns rather than prints.

    `on_progress` is called with a message to send to the user immediately,
    before the slow part starts. The WhatsApp adapter passes its send function
    here; the CLI prints it. Nothing downstream depends on it, so a caller that
    does not care can leave it out.
    """
    label, route, how = classify.classify(question)
    rules = [f"INTENT_{label}:{how}"]

    if route == "fixed":
        rules.append("PREEMPT_settlement_pressure_fixed_response")
        return Answer(
            text=with_contact(settlement_response()),
            route="hardcoded (no retrieval, no LLM)",
            rules=rules,
        )

    if route == "handoff":
        msg = CASE_STATUS_HANDOFF if label == classify.CASE_STATUS else HANDOFF
        return Answer(
            text=with_contact(msg),
            route=f"handoff ({label}) - retrieval and LLM not called",
            rules=rules,
        )

    hits = retrieve(question)
    scored = {c.chunk_id: s for c, s in hits}
    kept, gate_rules = apply_filters([c for c, _ in hits])
    rules += gate_rules

    # RULE 6 from docs/metadata-schema.md: contact chunks are never sent to the
    # LLM - they are looked up and string-substituted, gated on a human
    # having dialled the number. There is no SQLite yet, so the only safe
    # thing to do is withhold them.
    survivors = []
    for c in kept:
        if c.source_type == "directory":
            rules.append(f"RULE6_contact_chunk_withheld:{c.chunk_id}")
        else:
            survivors.append(c)

    con = answer_constraints(survivors)
    if con["handoff"]:
        return Answer(
            text=with_contact(HANDOFF),
            route=f"handoff ({con['reason']})",
            rules=rules,
        )

    best = max(scored[c.chunk_id] for c in survivors)
    if best < MIN_SIMILARITY:
        rules.append(f"RULE7_below_threshold:{best:.3f}<{MIN_SIMILARITY}")
        return Answer(
            text=with_contact(HANDOFF),
            route=f"handoff (weak match {best:.3f}) - LLM not called",
            rules=rules,
        )

    if con["requires_review"]:
        rules.append("REVIEW_REQUIRED_legal_partner_signoff_pending")

    context = "\n\n".join(
        f"[{c.chunk_id} | {c.citation_label}]\n{c.text}" for c in survivors
    )
    prompt = SYSTEM_PROMPT.format(
        figure_rule=FIGURES_OK if con["may_state_figures"] else NO_FIGURES,
        citation_rule=CITATIONS_OK if con["may_cite_sections"] else NO_CITATIONS,
        retrieved_chunks=context,
        user_question=question,
    )
    if not con["may_state_figures"]:
        rules.append("RULE4_figures_suppressed")
    if not con["may_cite_sections"]:
        rules.append("RULE3_citations_suppressed")

    chunks = [f"{c.chunk_id} ({scored[c.chunk_id]:.3f})" for c in survivors]
    labels = con["citation_labels"]

    # Everything above this line is local and fast. The model call is the only
    # slow part, so this is the moment the holding message is worth sending.
    if on_progress:
        on_progress(HOLDING)

    try:
        raw = call_groq(
            prompt,
            question,
            on_wait=lambda d, n: rules.append(f"RETRY_{n}_after_{d:.0f}s"),
        )
    except ModelUnavailable as e:
        # Degrade to the handoff, not to an error string. A family reading
        # "HTTP 429" learns nothing and loses trust; the legal aid number is
        # useful to them either way. The cause goes to the provenance, which
        # is for the reviewer.
        rules.append(f"MODEL_UNAVAILABLE:{e}")
        return Answer(
            text=with_contact(HANDOFF),
            route=f"handoff (model unavailable) - {e}",
            chunks=chunks, labels=labels, rules=rules,
        )

    ok, check, items = validate_answer(raw, context)
    if not ok:
        log_refusal(question, raw, check, items)
        rules.append(f"{check}:{items}")
        return Answer(
            text=with_contact(HANDOFF),
            route=f"REFUSED by validator ({check}) - answer withheld",
            chunks=chunks, labels=labels, rules=rules,
        )

    return Answer(
        text=with_contact(raw),
        route=f"RAG -> {ANSWER_MODEL} (best {best:.3f}) - validator PASS",
        chunks=chunks, labels=labels, rules=rules,
    )


def answer_question(question: str, *, on_progress=None) -> Answer:
    """CLI wrapper: resolve, then print the answer and its provenance."""
    print(f"\n=== Q: {question}")
    a = resolve(question, on_progress=on_progress)
    show(a)
    return a


TEST_CASES = [
    ("my husband died in a factory accident, what are we owed?",
     "s.76 structure, NO rupee figure (blocker chunks)"),
    ("how much money will we get exactly?",
     "No figure; explains it needs confirming"),
    ("the police are refusing to write the FIR",
     "s.173(4) BNSS escalation to SP"),
    ("they took his body away, what should we do?",
     "s.194 BNSS: inquest, post-mortem urgency"),
    ("the owner is offering us 2 lakh to sign a paper",
     "HARDCODED settlement response, not RAG"),
    ("he worked through a thekedar, not directly",
     "s.85 principal-employer liability"),
    ("what is the weather in Ludhiana",
     "Handoff, no LLM call"),
    ("what does the Factories Act say the factory must do",
     "Must NOT answer from the repealed Factories Act"),
]


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser()
    ap.add_argument("question", nargs="?")
    ap.add_argument("--test", action="store_true")
    args = ap.parse_args()

    if using_fallback_embedder():
        print(
            "\n!! Running on chroma's bundled ONNX embedder, which truncates "
            f"chunks at 256 tokens.\n   Threshold lowered to {MIN_SIMILARITY} "
            "to compensate. Scores below are NOT comparable\n   to the ones in "
            "the task write-ups, so install sentence-transformers for those."
        )

    def progress(msg: str) -> None:
        print(f"    ... {msg}", flush=True)

    if args.test:
        for i, (q, expected) in enumerate(TEST_CASES, 1):
            print(f"\n{'=' * 70}\nCASE {i}: expect: {expected}")
            answer_question(q, on_progress=progress)
        return 0

    if not args.question:
        ap.error("give a question, or --test")
    answer_question(args.question, on_progress=progress)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
