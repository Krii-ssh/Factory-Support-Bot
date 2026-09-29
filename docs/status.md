# Goals against delivery, as at 3 September 2026

The working system compared against the two planning documents, which are kept
outside the repository:

- **A**: *Chatbot Factory Workers Safety*, the original brief
- **B**: *factory_safety_bot_pipeline*, the four-day build plan

Legend: ✅ done · 🔶 partial · 🔴 not built · ⛔ blocked externally

---

## Headline

**The one flow that B said to build works end to end on a real phone.**

On 3 September a real WhatsApp message from a real handset produced the
settlement warning with a case ID, routed entirely offline with no retrieval and
no model call. That was B's Day 2 goal and A's most important protective
feature.

The knowledge base and safety layers went **well beyond** both documents. The
delivery surfaces beyond WhatsApp text did not get built.

---

## The finding that reframes the brief

Document A names the legal sources the bot should draw on:

> Factories Act, 1948 / OSHWC Code 2026, Employees' Compensation Act, IPC
> sections for negligence and FIR filing procedures

**Three of those four are no longer law, and the fourth is misnamed.**

| Named in the brief | Actual position |
|---|---|
| Factories Act, 1948 | **Repealed** 21 November 2025 |
| Employees' Compensation Act | **Repealed** 21 November 2025 and replaced by Code on Social Security 2020, Chapter VII |
| IPC sections for negligence | **Replaced** by the Bharatiya Nyaya Sanhita 2023, with FIR procedure now in the BNSS 2023 |
| "OSHWC Code 2026" | The Code is **Act 37 of 2020**, not 2026 |

The brief also never mentions **s.194 BNSS**, the inquest and post-mortem
provision that governs a factory death and the most time-critical thing a family
needs to be told in the first hours.

A build that had followed A literally would have produced a bot citing repealed
statutes, fluently and with confidence, to people in a legal crisis. That is the
exact failure A itself names as the biggest risk:

> The agent must never give confident wrong legal advice.

---

## A's core requirements

| Requirement (A) | Status | Notes |
|---|---|---|
| Multilingual WhatsApp interface | 🔶 | WhatsApp **working**. English only, see the language blocker below |
| Voice-first (Bhashini) | 🔴 | Not built. Bhashini shelved and Whisper is the plan |
| Knowledge: Factories Act and OSHWC | ✅ **Exceeded** | Rebuilt from gazette texts after finding the Act was repealed |
| Knowledge: Employees' Compensation | ✅ **Exceeded** | Replaced with Code on Social Security Chapter VII |
| Knowledge: IPC and FIR procedure | ✅ **Exceeded** | Replaced with BNSS and BNS 2023, and added the s.194 inquest that A lacked |
| PPCB complaint filing | 🔴 | Out of scope for the pilot flow |
| Punjab Labour Department directory | 🔶 | Structure exists and only DLSA Ludhiana is verified |
| Legal aid services (DLSA) | ✅ | Verified and used on every handoff |
| Union contacts (Ludhiana) | 🔴 | Not collected |

## A's four conversation flows

| Flow | Status |
|---|---|
| "My husband died" leading to rights, FIR, calculator and legal aid | 🔶 Rights ✅ and legal aid ✅, **calculator deliberately off**, FIR *status* checking not built |
| "The owner offered us money to sign a paper" | ✅ **Exceeded.** An offline keyword pre-empt returns pre-approved text and never reaches the model. **Proven on a real phone** |
| "We don't know what gas killed him" leading to RTI and PPCB | 🔴 Not built |
| "The factory has no FIR yet" leading to escalation to the SP or DCP | ✅ Built, answering from **s.173(4) BNSS** and not the repealed CrPC section the source material cited |

## A's "agentic" behaviours

| Behaviour | Status |
|---|---|
| Flags manipulation and settlement pressure | ✅ Two independent layers: offline keywords, then a classifier |
| Connects to real humans when out of depth | ✅ Every uncertain path ends at verified legal aid |
| Reasons about the specific situation | 🔶 Handles the contractor (thekedar) case through s.85 and the ESI fork. Does not ask clarifying questions yet |
| Proactive 48-hour FIR nudge | 🔴 Not built, and B deferred it explicitly |

## A's document generation

| | Status |
|---|---|
| RTI applications, complaint letters, legal notices, FIR draft | 🔴 **Deliberately not built** |

Both the original build session and the project's legal partner independently
argued against it. A generated document a family actually *files* is a bigger
liability step than a generated answer, and the output validator does not cover
documents. It waits for the legal partner.

---

## B's four-day plan

| Day | Goal | Status |
|---|---|---|
| **1** | Knowledge base and RAG core | ✅ **Exceeded** with 31 chunks, all from primary gazette sources |
| **1** | Retrieval confidence gate as the "single most important safety mechanism" | 🔶 **Superseded.** Built, measured, found insufficient and replaced with metadata gating and output validation |
| **2** | WhatsApp end to end | ✅ **Working on a real phone** |
| **2** | Voice in and out (Bhashini) | 🔴 Not built |
| **2** | Intent classifier | ✅ 6 labels, 22 of 22 on required cases |
| **3** | Settlement-trap flow | ✅ **Exceeded** |
| **3** | Case tracker (SQLite) | ✅ Working, and `LDH-1002` was issued live |
| **3** | Document drafting (RTI) | 🔴 Deferred, see above |
| **4** | Full test pass including out-of-scope | ✅ 8 of 8 pipeline cases, 22 of 22 routing |
| **4** | Tests in Hindi and Punjabi | 🔴 English only |
| **4** | **Legal partner reviews 15 to 20 transcripts** | ⛔ **Not done. Hard prerequisite before any real family** |
| **4** | Deploy to Render or Railway | 🔴 Runs locally. A Render blueprint exists |

Why the confidence gate was superseded. B calls the similarity threshold the
single most important safety mechanism, and measurement disagreed:

- An off-topic question ("what is the weather in Ludhiana") scored **0.653**,
  higher than three legitimate questions including "how much exactly will we
  get" at **0.598**. The bands are inverted, so no threshold satisfies both.
- The repealed Factories Act chunk retrieved at **rank 1 with 0.786**, the
  highest score in the whole suite. A confidence gate passes it happily because
  it is genuinely the most relevant text. It is simply no longer law.

---

## Built that neither document asked for

These came out of measurement, not the plan:

1. **A source audit before writing any code.** It found that 2 of 5 sources were
   repealed law, one was not the Act it claimed to be and one was a blog citing
   five repealed sections.
2. **Metadata gating before similarity.** Legal status decides what the model
   sees, evaluated before any score.
3. **A deterministic output validator.** Contacts never come from the model, and
   every figure and citation must appear verbatim in retrieved law. Fabricated
   contacts went from 3 of 6 to **zero**.
4. **Provenance on every answer.** Route, chunks and rules fired, so a reviewer
   grades sources rather than prose.
5. **A refusal log.** Every refusal is recorded as evidence of a corpus gap.
6. **A web chat client.** The same pipeline, showing the trace, needing no
   WhatsApp.
7. **The ESI versus compensation fork.** It is absent from both documents and it
   decides which office a family goes to.
8. **A shared LLM transport.** Rate limiting, retry and typed failures for both
   the answer model and the classifier, added after the classifier was found
   failing silently and intermittently.

---

## Still blocked, and why

| Item | Blocker | Who unblocks it |
|---|---|---|
| **Compensation calculator** | The Code delegates both the minimum amount (s.76(1)(a)) and the wage ceiling (s.76(3)) to notifications not in the Act | A lawyer or labour-law practitioner |
| **Citing the settlement provision** | The old blanket protection was repealed. It is likely s.89 with s.74(7) but unconfirmed | The legal partner |
| **Answers in Hindi or Punjabi** | The validator checks the **English** answer. Machine translation would put unchecked text in front of a family, and a mistranslated deadline bypasses every safety layer | A trusted translator and legal sign-off |
| **Anything reaching a real family** | Transcript review | The legal partner |
| **Contacts beyond DLSA** | Nobody has phoned them | The project owner |
| **Always-on availability** | Runs on a developer laptop | Deployment |

---

## Why WhatsApp was never blocked on money

An earlier version of this document said WhatsApp delivery needed a paid
upgrade. That was wrong, and it is the kind of wrong that stops work for the
wrong reason.

Twilio is a genuine dead end for this use case and is kept only as the fallback
transport. Meta's Cloud API is the working path.

| | Twilio (fallback) | Meta Cloud API (the working path) |
|---|---|---|
| Free-form text on a trial or free tier | **No.** Error 21654, templates only | **Yes**, inside the 24-hour service window |
| Cost for user-initiated conversations | Metered | **Free, and uncapped since November 2024** |
| Setup | Paid upgrade to send freely | Free signup, and the test number allows 5 verified recipients |

The access token on Meta's API Setup page **expires in 24 hours**. For anything
demoed on a fixed date, use a System User token instead. See
[whatsapp-setup.md](whatsapp-setup.md).

---

## Honest scorecard

**Ahead of plan:** knowledge base rigour, retrieval safety, output validation,
intent routing, provenance, test coverage and the ESI fork. These are precisely
the parts A calls "the biggest risk to get right".

**On plan:** WhatsApp delivery, the settlement flow, the case tracker and FIR
escalation.

**Behind plan:** voice, document generation, Hindi and Punjabi, deployment and
legal review.

B's own closing line remains the fair summary:

> Shipping one flow that's genuinely safe and grounded beats five flows that
> might mislead someone in a legal crisis.

One flow is genuinely safe, grounded and now **delivered to a real phone**. The
rest are not built, and two of them deliberately so.
