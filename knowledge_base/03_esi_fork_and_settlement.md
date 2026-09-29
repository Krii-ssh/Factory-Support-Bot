---
doc_id: esi_fork_flow_design
title: "ESI vs Employee's Compensation — the first branch point; and the settlement-warning flow"
citation_label: "Flow design — ESI / compensation fork"
status: design_doc
in_force_from: null
sphere: national
source_type: derived
jurisdiction: india
language: en
retrieved_on: "2026-08-13"
verification: mixed
review_required: true
index: false        # design doc — do NOT embed. See notes below.
---

# The ESI fork — first branch point in the death flow

> `index: false` — this file is a **design specification for your code**, not
> retrievable knowledge. The bot must not answer *from* it. The decision
> logic belongs in the intent/routing layer; only the plain-language
> fragments marked `→ BOT COPY` should be lifted into fixed responses.

---

## Why this has to come first

Your current pipeline goes: intent → RAG → answer. For a death case that is
one step too early. **Before any compensation question can be answered
correctly, one fact has to be established: was the deceased covered by ESI?**

Because if he was:

| | ESI-covered | Not ESI-covered |
|---|---|---|
| Governing chapter | SS Code Ch. IV (ESI) | SS Code Ch. VII (Employee's Compensation) |
| What the family gets | **Dependants' benefit — a monthly pension** | **A lump sum** (50% × wages × relevant factor) |
| Where they go | ESIC Sub-Regional Office / Branch Office | Competent Authority (labour dept.) |
| Who pays | ESIC | The employer |
| Funeral | ESIC funeral expenses | Employer, min ₹15,000 (s.76) |
| Typical timeline | Faster, administrative | Slower, adjudicatory |

These are **different offices, different forms, different money, and
different timelines.** A bot that skips the fork and confidently walks an
ESI-covered family through a Chapter VII compensation claim has not merely
given a suboptimal answer — it has sent a grieving family to the wrong
building to file the wrong form, and they may lose months before anyone
tells them. In Ludhiana, where the registered manufacturing base is heavily
ESI-covered, **this will be the common case, not the edge case.**

---

## The bar on double recovery

`verification: principle verified, section number UNVERIFIED`

Under the ESI regime an insured person or their dependants are **barred from
also claiming compensation** under the employee's compensation route for the
same injury. The family does not choose the more generous option — coverage
decides it for them.

> ⚠️ The exact section of the Code on Social Security carrying forward
> s.53 of the ESI Act, 1948 was **not confirmed**. State the principle
> without a citation until a lawyer supplies the section number.

This is why the fork cannot be deferred "until later in the conversation."
It is not a refinement. It determines the whole answer.

---

## Decision logic

```
death_case_detected
        │
        ▼
┌───────────────────────────────────────────┐
│ ESI COVERAGE TRIAGE  (ask, don't assume)  │
└───────────────────────────────────────────┘
        │
        ├── strong signal COVERED ────────► ESI branch
        │
        ├── strong signal NOT COVERED ────► Ch. VII compensation branch
        │
        └── UNCERTAIN (default) ──────────► DUAL-PATH + HUMAN HANDOFF
```

**The default is UNCERTAIN, and uncertain does not mean guess.** Your ground
rule — answer only from retrieved knowledge, hand off when not confident —
applies to this classification exactly as it applies to a legal question.

### Triage questions (voice-friendly, in priority order)

The family will not know the phrase "ESI coverage." Ask about artefacts they
would have seen:

1. **"Did he have an ESI card, or a Pehchan card?"** — strongest single
   signal.
2. **"When he was ill, did you go to the ESI dispensary or ESI hospital?"** —
   families remember this even when they don't remember the card.
3. **"On his pay slip, was money cut for ESI?"** — good if pay slips exist.
4. **"Roughly how many workers were in the factory?"** — 10 or more points
   toward coverage.
5. **"About how much did he earn in a month?"** — ≤ ₹21,000 points toward
   coverage. *(Wage ceiling for ESI coverage: ₹21,000/month, per the Ministry
   of Labour FAQs dated 16.03.2026. A higher ceiling applies for persons
   with disability — figure not confirmed.)*
6. **"Did he work directly for the factory, or through a thekedar?"** —
   contractor engagement complicates both branches (see below).

### Scoring

- Q1 or Q2 answered **yes** → treat as **COVERED**, but still confirm with a
  human before the family acts.
- Q1 and Q2 both clearly **no**, *and* (Q4 under 10 **or** Q5 above ₹21,000)
  → treat as **NOT COVERED**.
- **Anything else → UNCERTAIN.** Including "I don't know," which will be the
  most common answer and must not be coerced into a branch.

### → BOT COPY — the UNCERTAIN response

> *"I'm not able to tell yet which route applies to your family, and I don't
> want to send you to the wrong office. There are two different systems, and
> which one applies decides where you go and what you receive.*
>
> *There is one thing that settles it: whether he was registered under ESI.
> If you can find an ESI card or Pehchan card among his papers, or a pay slip
> showing an ESI deduction, that answers it. The ESI office in Ludhiana can
> also check using his name and the factory's name.*
>
> *I'm connecting you with free legal aid who can check this with you. In the
> meantime, please keep every document safe — his ID card, any pay slips, and
> anything from the factory.*
>
> *This is general information, not a lawyer's advice — your case may differ.
> Contact: [legal aid contact]"*

---

## Branch A — ESI-covered

`verification: UNVERIFIED — rates and split not confirmed`

Dependants' benefit is paid as a **periodic monthly payment**, not a lump
sum, divided among the widow, children and (in some circumstances) dependent
parents. ESIC also pays funeral expenses.

> ⚠️ **Do not state the rate or the split until verified.** Commonly cited
> figures (a percentage of wage; shares among widow and children) were not
> confirmed against the Code or current ESIC notifications. The bot may say
> *"a monthly payment to the family"* — the contrast with a lump sum is the
> useful part and is safe. It must not put a number on it yet.

**What the family should do:** report the death to the ESIC Branch Office
where the worker was attached, and ask about the dependants' benefit claim.
The employer is separately required to submit an accident report to ESIC.

→ **Content still to source:** the current dependants' benefit rate, the
share split, the claim form number and the limitation period.

---

## Branch B — not ESI-covered

Route to `01_compensation_ss_code_2020.md` — Chapter VII.

Note that **the calculator itself is still blocked** on three unresolved
items (notified minimum, Sixth Schedule confirmation, wage ceiling). Until
those clear, Branch B should explain the *structure* of the entitlement —
that it is a lump sum based on wages and age, plus at least ₹15,000 for
funeral expenses — and hand off for the figure. **Structure without a number
is safe and still genuinely useful. A number that turns out to be wrong is
not recoverable.**

---

## Cross-cutting — the contractor (thekedar) case

`verification: verified_primary` — ✅ **RESOLVED 13 Aug 2026**

A large share of Ludhiana factory workers are engaged through contractors,
and the factory will often deny the employment relationship outright.

**Section 85(1)** settles it: where an employer contracts out work **which
is ordinarily part of the employer's own trade or business**, the employer
is liable to pay any employee employed on that work the compensation the
employer **would have been liable to pay if that worker had been directly
employed**. Under **s.85(3)** the family may instead recover from the
contractor. Under **s.85(4)** this does not apply where the accident
happened away from premises the employer controls.

> The factory cannot hide behind the thekedar for a death on its own floor
> doing its own core work. **Downgrade from blanket handoff** — the bot can
> now state the principle. Keep handoff for the s.85(4) edge case (accident
> off-premises) and wherever the family cannot say what work he was doing.
>
> → BOT COPY: *"Even if he was hired through a thekedar and not directly by
> the factory, the factory can still be responsible — if the work he was
> doing was the factory's normal work and the accident happened on their
> premises. Do not accept 'he wasn't our worker' as the end of the matter."*

---

# The settlement-warning flow

## Status: legal basis IDENTIFIED but NOT YET SIGNED OFF — message stays uncited

Your pipeline correctly specifies this as a **fixed, pre-approved message,
not RAG-generated**. That decision stands.

**What the gazette check established (13 Aug 2026):**

There is **no successor to s.17 of the repealed 1923 Act** in the Code. This
is not a retrieval failure — it is confirmed absent: the Code contains **zero
occurrences of "null and void"**, and "relinquish" appears only in the
Chapter IV gratuity context. The blanket voiding provision is simply gone.

**The Code protects families a different way — through registration
scrutiny:**

- **s.89(1) proviso (c)** — the competent authority **may refuse to record**
  a settlement agreement by reason of the **inadequacy of the sum**, or where
  it was **obtained by fraud or undue influence or other improper means** —
  and may make orders about money already paid. This ground is expressly
  attached to agreements with **a woman or a person under a legal
  disability**, which is precisely the widow at the factory gate.
- **s.89(1) proviso (a)** — nothing is recorded until **seven days** after
  notice to the parties.
- **s.89(3)** — where the employer never sends the memorandum, the employer
  **remains liable for the full compensation**, and may not deduct more than
  half of what was already paid.
- **s.74(7)(b)** — but an agreement made *in accordance with the Chapter*
  does close off the civil-suit route.

In practice this may be **more** protective than the old s.17, because
"inadequacy" is an express ground and an unregistered back-room settlement
does not discharge liability at all.

> 🟡 **The message stays uncited, as instructed.** The reading above is
> mine, not a lawyer's, and s.89 read with s.74(7)(b) raises a question I
> cannot answer: what exactly to tell a family who has **already signed**.
> Ship the uncited message; add the citation only when the legal partner
> signs off.

### → BOT COPY — settlement-pressure response (uncited draft, pending sign-off)

> *"Please stop and read this before you sign anything.*
>
> *If someone from the factory is offering you money now and asking you to
> sign a paper, a receipt, or a stamp paper — please do not sign it yet, and
> please do not take a thumb impression on anything you have not had read to
> you by someone you trust.*
>
> *A paper like this is often written to say the family accepts this money as
> full and final, and gives up the right to claim anything more. The amount
> the law entitles a family to after a death is usually far more than what is
> offered in the first days. Once you sign, getting the rest becomes much
> harder.*
>
> *You are allowed to take time. You are allowed to say 'I will sign after I
> have shown this to a lawyer.' Nobody can require you to sign today.*
>
> *If you have already signed something — that is not the end of the road.
> Please still speak to a lawyer, and take a copy of whatever you signed.*
>
> *Free legal help is available and it costs you nothing: [legal aid
> contact]."*

### Design notes on this message

- **No section citation** until the successor provision is identified.
- **No rupee figure** — a family told "you're entitled to ₹15 lakh" may
  reject a reasonable offer on the strength of a bot's arithmetic.
- **The already-signed path must be included.** Many families reach the bot
  *after* signing, and a message that only addresses the before-case abandons
  them at the worst moment. The line "that is not the end of the road" is
  doing real work.
- **Thumb impression is named explicitly.** Literacy assumptions in the
  standard framing ("do not sign") miss how this actually happens.
- This intent should **pre-empt every other flow**, including the ESI fork —
  it is time-critical in a way that the fork is not.
- Log the trigger with a distinct `case_events.stage` value so you can audit
  how often it fires and whether it fires wrongly.

---

## Sources

- [Additional FAQs on Labour Codes (16.03.2026) — Ministry of Labour & Employment](https://www.labour.gov.in/static/uploads/2026/03/a4ccf4c6d97c4f1f36a6d83f8c64213d.pdf)
- [Code on Social Security, 2020 — India Code](https://www.indiacode.nic.in/bitstream/123456789/16823/1/aA2020-36.pdf)
- [Arrangement of Clauses — PRS India](https://prsindia.org/files/bills_acts/bills_parliament/2020/Code%20On%20Social%20Security,%202020.pdf)
