# Factory Accident Support Bot: progress summary

**A WhatsApp assistant for families of factory accident victims in Ludhiana,
Punjab.** It helps a grieving family understand their legal rights, avoid being
pressured into a bad settlement and reach real legal aid.

**Status:** the knowledge base is built and verified, the retrieval and safety
layers work and the bot generates answers. The settlement warning has reached a
real handset over the Meta Cloud API. There is no voice and it is not hosted,
and two legal blockers remain before it can go near a real family.

Everything used so far is free or open source: the WhatsApp Cloud API, the Groq
free tier, sentence-transformers, ChromaDB and SQLite. Bhashini (Government of
India) was considered for voice and shelved. Whisper is the current plan for
voice input.

---

## The core problem

In a legal crisis, **a confidently wrong answer is worse than no answer.** A
widow told the wrong figure, or sent to the wrong office, loses months she does
not have.

So the design rule is that the bot answers **only** from a knowledge base of
verified law, and hands off to a human whenever it is not certain.

Most of the work has gone into making that rule actually hold, because asking a
language model nicely turns out not to be enough.

---

## What was done, in order

### 1. Audited the source material and found most of it unusable

Before building anything, every collected source was checked against its
original PDF and against current law. Findings:

- **The Factories Act 1948 and the Employees' Compensation Act 1923 are both
  repealed** (21 November 2025, replaced by the new labour codes). Two of five
  legal sources were dead law.
- **The "Employees' Compensation Act" file was not the Act.** It was a two-page
  FAQ with obsolete figures that also **omitted factory workers** from its
  coverage list. A bot using it could have told a factory widow she was not
  covered.
- **The FIR file was a law-firm blog post** citing five repealed CrPC and IPC
  sections, including the exact police-escalation step the product promises.
- It was missing **s.194 BNSS** entirely. That is the inquest and post-mortem
  provision that governs a factory death, and the most time-critical thing a
  family needs to know.

**Had this step been skipped, the bot would have confidently cited repealed
statutes to grieving families.**

### 2. Rebuilt the knowledge base from primary sources

Current law only, verified against gazette texts: Code on Social Security 2020
Chapter VII and the Sixth Schedule, BNSS and BNS 2023, the OSHWC Code 2020 and
the OSH&WC Central Rules 2026. There are now 31 indexed chunks, each tagged with
`status`, `source_type`, `sphere` and a per-fact verification level.

### 3. Built a retrieval gate that filters on law, not similarity

Standard RAG ranks by similarity. That is not sufficient here. A chunk of the
**repealed** Factories Act scores *highly* on "what was the factory required to
do". It is genuinely relevant. It is simply no longer law.

So hard metadata rules run **before** any similarity threshold. Repealed law is
dropped, secondary sources cannot support a citation, unverified figures cannot
produce a number and Central rules are not served to a state-sphere factory.

**Measured result:** the repealed Factories Act chunk retrieved at **rank 1 with
the highest similarity score in the whole test suite (0.786)** and was dropped
anyway. The question was then answered correctly from the current Code.

### 4. Made the bot speak, and caught it fabricating a helpline

The first live generation run produced good, legally sound answers. It also
**invented contact details in three of six answers**, including a fake legal aid
helpline number.

The root cause was that the safety rules lived in the prompt, so they depended
on the model choosing to comply. It complied most of the time, which is the
worst possible reliability profile because it looks fine in testing.

### 5. Added an output validator

A deterministic check that runs on every answer **before it is sent**:

- **No contact details from the model, ever.** Verified contacts are appended by
  code afterwards, so a phone number never passes through the model.
- **Every figure must appear verbatim in the retrieved law.** Correct quotes
  pass. Computed or invented numbers cannot, because a multiplied figure will not
  appear verbatim anywhere.
- **Every section citation must be grounded** in the same way.
- Every refusal is logged as a signal that the knowledge base has a gap.

**Result: zero fabricated contacts across all test cases.**

The validator refused exactly one answer, and the refusal was more interesting
than the passes. The Code spells the death formula as *"fifty per cent."* in
words, and the model rendered it as *"50 %"* in numerals. The validator compares
literally, so a correct and useful answer was withheld. The same statutory fact
passed in another case because that answer happened to write "half".

**Which answer a family got was a coin flip on the model's phrasing.** It was
fixed in the corpus, not the validator: the source now reads *"fifty per cent
(50%)"*, which grounds both renderings. Relaxing the validator to understand
numeral and word equivalence was the tempting fix and the wrong one. The whole
reason the check works is that a *computed* figure cannot appear verbatim
anywhere. Grounding `50` was verified not to ground `50,000` or `₹1,50,000`,
because the match must be standalone, so the blocker on the compensation total
is untouched.

### 6. Built the intent classifier, because similarity cannot decide scope

The validator fixed what the bot *says*. It did not fix what the bot *answers at
all*. "What is the weather in Ludhiana" scored **0.653**, higher than three
legitimate questions including "how much exactly will we get" at **0.598**. The
bands are inverted in rank order, so no threshold and no rescaling separates
them. Two relative measures were tried and were worse: the weather question had
the *highest* z-score of anything tested.

Scope is a classification question, so it now gets a classifier. There are six
labels. Settlement pressure goes to fixed text, out-of-scope and case-status go to a human and the rest go to retrieval.

The ordering is the safety property. **A keyword check runs before the
classifier, not instead of it.** The classifier is a network call that can time
out or hit a rate limit, and settlement pressure is the one intent where a miss
is unrecoverable, because a signature cannot be un-signed. That path never
touches the network. When the classifier is unreachable the fallback is the main
answer flow, not a handoff, so a transport blip cannot silence a family.

The trigger vocabulary lives in a flat text file with one phrase per line, so a
Punjabi speaker can extend it without touching code.

**Measured against a live key:** the full confusion matrix over all thirteen
boundary cases plus the eight Day 1 cases is **22 of 22, zero misroutes.** Both
zero-tolerance rows are clean: no settlement-pressure input was classified as
anything else, and no out-of-scope input was stretched into a real label. All
four settlement cases are caught by the offline keyword layer alone, and the
weather question no longer reaches retrieval or the answer model at all, which
was the whole point. Writing the list surfaced its own bug. The bare word
*muavza* ("compensation") was in the draft, which would have routed the flagship
"how much are we owed?" to the don't-sign warning instead of an answer. It was
removed, and the reason is recorded in the file so it does not get added back.

---

## Where it stands

| | |
|---|---|
| ✅ Working | Knowledge base, retrieval, metadata gate, output validator, settlement-warning flow, intent classifier and routing, case tracker, WhatsApp delivery |
| 🔜 Next | Voice input, then deployment |
| 🔴 Blocked | Two Central Government notifications and a lawyer's sign-off |

Two things are open on the classifier, both deliberate rather than unfinished:

- **The confusion matrix is only partly run in continuous integration.** The
  keyword layer is deterministic and passes offline. The eighteen cases that need the model are reported as `skip` and not as passes, so they need a key to count.
- **One known over-trigger:** *"what papers do we need for the claim?"* fires on
  `papers` and gets the don't-sign warning instead of a document list. The spec
  calls over-triggering the correct failure direction, so this was left in
  rather than quietly narrowed. It is a common question, though, and worth a
  decision rather than a shrug.

**The compensation calculator is deliberately switched off.** The Code sets the
death formula as *50% of monthly wages multiplied by an age factor*, but
delegates both the minimum amount and the wage ceiling to notifications that are
not in the Act. Until those are located, the bot explains **how** the amount is
worked out and refuses to state a total. This is enforced in code, not by
instruction.

A legal partner still needs to sign off the settlement-warning wording and
confirm which provision voids a coerced settlement. The old provision was
repealed and the new Code protects families by a different mechanism.

---

## The numbers reproduce

The index was deleted and rebuilt from the corpus on a clean install, and the
measured results came back unchanged: the FIR case at 0.746, the post-mortem
case at 0.720, the thekedar case at 0.623 and the weather question at 0.653,
still scoring above the lowest legitimate question. That is the inversion the
classifier exists to handle. The headline result reproduces exactly: **the
repealed Factories Act chunk returns at rank 1 with 0.786, the highest score in
the suite, and the gate drops it.**

Two cases moved. Both were the chunks edited for the percentage fix above, and that fix is confirmed: **case 2, the one answer the validator used to
withhold, now passes while writing "50 %" in numerals.** The answer a family
gets no longer depends on whether the model happened to spell the number out.

One thing fell out of rebuilding: **similarity scores are not portable between
embedders.** Chroma's bundled ONNX build truncates chunks at 128 tokens and
scores the same questions 0.24 to 0.55, so a threshold tuned on one embedder
silently refuses almost everything on the other. The threshold is now calibrated
per embedder and says so out loud. It is one more piece of evidence for the same
conclusion: a similarity number is not a fact about relevance, and scope cannot
rest on one.

---

## Seeing it

[`demo/demo.html`](../demo/demo.html) replays all eight recorded runs side by
side, showing what the family would have received when the safety rules lived in
the prompt against what they receive now. The pipeline trace sits beside each
answer, so the invented helpline and the gate that drops the repealed statute
are both visible rather than described. It has no dependencies and makes no
network calls. The raw transcripts are in
[`recorded-runs/`](recorded-runs/).

---

## What this project is really about

The interesting problem here was not building a chatbot. It was discovering that
**the obvious safety mechanisms do not work**:

- A similarity threshold cannot tell "no good answer" from "a very good answer
  in a repealed statute".
- It also cannot decide scope. An off-topic question scored *higher* than three
  legitimate ones.
- A safety rule in a prompt is a request, not a guarantee.

Each of those was found by measurement rather than assumption, and each was
replaced by something deterministic.
