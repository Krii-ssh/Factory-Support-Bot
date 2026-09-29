---
doc_id: intent_classification_spec
title: "Intent classification — labels, routing, and boundary cases"
citation_label: "Flow design — intent classification"
status: design_doc
in_force_from: null
sphere: national
source_type: derived
jurisdiction: india
language: en
retrieved_on: "2026-08-18"
verification: derived
review_required: true
index: false
---

# Intent classification

> `index: false` — spec for the routing layer, not retrievable knowledge.

## Why this exists

Day 1 measurement established that **scope cannot be decided by similarity**.
"What is the weather in Ludhiana" scored 0.653 — above three legitimate
questions, including "how much exactly will we get" at 0.598. The bands are
inverted and the overlap is in rank order, so no rescaling fixes it. Two
relative measures (gap-from-mean, z-score) were tried and were worse; the
weather question had the *highest* z-score of anything tested.

"Is this about a factory death at all?" is a classification question. It gets
a classifier.

**The threshold stays** as a floor against total nonsense. It is not a
relevance gate and the code should keep saying so.

---

## Labels

Six. Resist adding more — every extra label is a new way to route someone
wrongly.

| Label | What it covers | Route |
|---|---|---|
| `settlement_pressure` | Being pushed to sign, take cash, give a thumb impression, accept "full and final" | **Fixed message. No RAG, no LLM.** |
| `body_postmortem` | The body, post-mortem, inquest, cremation, "they took him away" | RAG — **time-critical, answer fast and short** |
| `fir_police` | Filing an FIR, police refusing, escalation, which section, thana behaviour | RAG |
| `death_case` | Compensation, entitlement, employer duty, ESI, contractor, deadlines | RAG — the main flow |
| `case_status` | "What's happening with my case", checking a case ID | **Stub → handoff** (Day 3) |
| `out_of_scope` | Everything else | **Handoff. No answer call.** |

### Ordering rules

1. **`settlement_pressure` pre-empts everything.** If it is even plausibly
   present, it wins — including over `body_postmortem`. It is the only
   irreversible harm in the set: a signature cannot be un-signed.
2. **`body_postmortem` outranks the rest.** Its window is hours. A
   compensation answer can wait until tomorrow; a post-mortem cannot.
3. **When genuinely torn between a real label and `out_of_scope`, pick the
   real label** — a family asking clumsily should be helped, and RAG plus the
   gate will refuse safely if there is nothing to say.
4. **When torn between two real labels, pick the higher-priority one.**

### The classifier must be willing to say `out_of_scope`

Models bias toward being helpful and will stretch to fit a label. The prompt
must state explicitly that `out_of_scope` is a correct, useful answer and not
a failure. Test it with weather, cricket, recharge, and government-scheme
questions — all should return `out_of_scope` without hesitation.

---

## Belt-and-braces on settlement pressure

**Run the keyword check before the classifier, not instead of it.** The
classifier is an LLM call; it can time out, rate-limit, or return malformed
output. The keyword check cannot. Settlement pressure is the one intent where
a miss is unrecoverable, so it gets a path that does not depend on the
network.

Order: keyword check → classifier → retrieval.

Over-triggering is the correct failure direction. A family that gets the
warning unnecessarily loses thirty seconds. A family that misses it can lose
their entire claim.

### Trigger vocabulary

Keep as a flat list in one file so a Punjabi speaker can extend it without
touching logic.

**English / romanized:** sign, signature, thumb impression, angutha, paper,
kagaz, stamp paper, settlement, full and final, compromise, samjhauta,
raazinama, "giving us money", "offering", "cash", "take it and close",
"withdraw the case", "case wapas"

**Hindi:** दस्तखत, हस्ताक्षर, अंगूठा, कागज़, समझौता, राज़ीनामा, पैसे दे रहे
हैं, केस वापस

**Punjabi:** ਦਸਤਖ਼ਤ, ਅੰਗੂਠਾ, ਕਾਗਜ਼, ਸਮਝੌਤਾ, ਰਾਜ਼ੀਨਾਮਾ, ਪੈਸੇ ਦੇ ਰਹੇ ਨੇ

> ⚠️ **Needs a native Punjabi/Hindi speaker to review and extend.** I have
> drafted these; I am not the right person to finalise them. Ludhiana usage
> will include forms I have not thought of, and the romanized spellings
> people actually type are unpredictable. Flag this to whoever does community
> outreach — a union rep will produce a better list in ten minutes than any
> amount of desk work.

---

## Boundary cases the classifier will get wrong

Give these to the classifier as few-shot examples. Each is a real
distinction that matters.

| Input | Correct label | Why it's hard |
|---|---|---|
| "the owner is offering 2 lakh, is that enough?" | `settlement_pressure` | Sounds like a compensation question. It isn't — they are mid-decision. |
| "how much are we owed?" | `death_case` | No pressure signal. Genuine information request. |
| "they gave us money for the funeral, should we take it?" | `settlement_pressure` | Funeral money is a real entitlement (s.76(7)) — **but** it is also the standard wrapper for a waiver. Route protectively. |
| "we already signed the paper" | `settlement_pressure` | Past tense. The fixed message has an already-signed path. |
| "they are saying take the body and go home" | `body_postmortem` | Reads as logistics. It is the hours-critical case. |
| "when will we get the post-mortem report?" | `body_postmortem` | Follow-up, not urgent — same label, no harm. |
| "police wrote the FIR but under a light section" | `fir_police` | Not a refusal. Still in scope. |
| "he worked through a thekedar" | `death_case` | Employment-status question feeding compensation. |
| "what does the Factories Act say?" | `death_case` | Corpus handles it — RULE 1 drops the repealed chunk and s.6 answers. |
| "what is the weather in Ludhiana" | `out_of_scope` | The Day-1 failure. Must not reach the LLM. |
| "how do I get a ration card" | `out_of_scope` | Real need, wrong service. Handoff warmly. |
| "my husband died in a factory accident" | `death_case` | The flagship. |
| "my husband is missing since the fire" | `out_of_scope` → handoff | **No death confirmed.** Nothing in the corpus addresses this. Do not improvise. |

That last row matters. Several plausible situations — missing worker, injured
but alive, death at home after an old injury — sit just outside the corpus.
The classifier should not stretch them into `death_case`.

### Negative examples — death-adjacent but still out of scope

Added 18 Aug 2026 after a held-out probe. `"is there any pension scheme for
widows in punjab"` was classified `death_case`. It should be `out_of_scope` —
the corpus has nothing on state welfare schemes.

The failure is instructive: "widow" + "Punjab" reads as death-adjacent, and
the model stretched to be helpful exactly as this spec predicted. **A question
being asked by the right person is not the same as being about the right
subject.** Our user is often a widow; that does not make every question she
asks answerable from a corpus of compensation and criminal-procedure law.

Give these as explicit `out_of_scope` few-shot examples:

| Input | Label |
|---|---|
| "is there any pension scheme for widows in punjab" | `out_of_scope` |
| "how do I get a widow certificate" | `out_of_scope` |
| "can I get my children into a government school" | `out_of_scope` |
| "is there any government scheme to help us" | `out_of_scope` |
| "how do I apply for a ration card now that he is gone" | `out_of_scope` |
| "the landlord is asking us to leave the room" | `out_of_scope` |
| "can I get a job in the same factory now" | `out_of_scope` |
| "how do I transfer his bank account to my name" | `out_of_scope` |

All are real needs a widow will have. All are outside this corpus. **Warm
handoff, not a stretched answer** — and the handoff message should sound like
help, not a rejection, because for several of these DLSA can genuinely
assist.

> ⚠️ **Measurement rule.** Any input used as a few-shot example in the
> classifier prompt **must not** be counted as a test result. Doing so
> measures recall of the prompt. Report required cases and **held-out
> paraphrases separately**, always.
>
> This was caught on 18 Aug 2026: 13 of 21 "required" cases were prompt
> examples, and the classifier scored 21/21 on them while missing a held-out
> case. The 21/21 was real but told us almost nothing.

---

## Answer length and register

Not strictly classification, but it belongs with the routing work because it
is a system-prompt constraint and the current prompt has none.

**Cap substantive answers at roughly 120 words**, or 4–5 short sentences plus
the disclaimer. Reasons:

- It will be read on a phone, often aloud, sometimes by a neighbour to
  someone who cannot read.
- It may be spoken back through Bhashini TTS. Long paragraphs are unbearable
  as audio.
- A grieving person cannot hold six points. Two is realistic.

**Give one next action, not a checklist.** The corpus contains long document
lists; the bot should surface the single most urgent item and offer the rest
if asked. For a fresh death that item is almost always the post-mortem.

**Never open with a condolence formula.** "I am sorry for your loss" from a
bot reads as hollow to some and as a stalling preamble to most. Lead with the
useful thing. Warmth belongs in the plainness of the language, not in a
sympathy sentence.

---

## Verification before this ships

Test the classifier on all thirteen boundary cases above, plus the eight
Day-1 cases, and report a confusion matrix. The two that must be perfect:

- **No `settlement_pressure` input classified as anything else.** Zero
  tolerance.
- **No `out_of_scope` input classified as a real label**, since that is the
  case-7 failure the classifier exists to fix.

Everything else can be imperfect at MVP.
