---
doc_id: output_validation_spec
title: "Output validation — the post-generation gate"
citation_label: "Flow design — output validation"
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

# Output validation — the post-generation gate

> `index: false` — spec for the code, not retrievable knowledge.

## Why this exists

Day 2 Task 1 was the first time the model generated text. It fabricated
contact details in three of six generated answers:

- `freelegalaid@example.org` (cases 1 and 6)
- "free legal aid helpline **1800123 4567**" (case 3)

Against a knowledge base whose contacts file opens with *"nothing in this
file should reach a user until a human has dialled it."*

A grieving widow dialling a number a language model invented is the worst
outcome this product can produce. It is worse than saying nothing, worse than
a wrong legal citation, and worse than the figure leak that was flagged as
the blocker.

**Diagnosis, and it is the right one:** we have a strong pre-generation gate
and no post-generation gate. Everything after the model starts writing is
enforced by asking it politely in a system prompt. It complies most of the
time, which is the worst possible reliability profile — good enough to look
fine in testing, not good enough to trust.

**Principle from here on:**

> The gate controls **what the model sees** (pre-generation) and **what
> reaches the user** (post-generation). It never relies on the model choosing
> to obey.

---

## The validator

One deterministic function. No LLM. Runs on every generated answer before it
is sent. Any failure → **do not send; return the handoff message instead.**

### Check 1 — no contact details from the model, ever

Reject any output containing an email address, URL, or phone-like digit run
(7+ digits, or grouped forms like `1800 123 4567`).

**The model must never be asked to emit a contact.** This was my design
error: the system prompt told it to end with *"Contact: [legal aid
contact]"*, and a placeholder in a template is an invitation to fill it in.
Of course it filled it in.

**Fix in two parts:**

1. Remove the contact instruction from the system prompt entirely. The model
   ends its answer with the disclaimer sentence and stops.
2. The **code appends** the contact block by string concatenation after
   validation, from the verified constant (Day 1–2) or the SQLite table
   (Day 3+).

A contact string must never pass through the model's context window on its
way to the user. It cannot corrupt what it never touches.

### Check 2 — every figure must be grounded

Extract every rupee amount and every quantity from the output. Each must
appear **verbatim** in the retrieved chunk text. If any does not → refuse.

This one check subsumes what RULE 4 was straining to do, and does it better:

- A **correct quoted figure** (₹15,000 funeral expenses, s.76(7)) passes,
  because it is verbatim in the context.
- A **computed figure** fails automatically, because a number the model
  arrived at by multiplying will not appear verbatim anywhere in the context.
  This is the property that matters — it blocks the compensation calculation
  while the two notifications remain unresolved, without needing to know
  anything about notifications.
- A **fabricated figure** fails for the same reason.

### Check 3 — every citation must be grounded

Every `Section N` / `s.N` / Act name in the output must appear verbatim in
the retrieved chunk text. Else refuse.

Note that **RULE 3 has never fired** in any test run, because every chunk in
the corpus is `source_type: primary` — the secondary sources were deliberately
removed during the source audit. RULE 3 is therefore dormant by design, not
passing. Check 3 covers the actual risk, which is invention rather than
provenance.

### Check 4 — log every refusal

A refusal is a signal, not just a safety action. Log the input, the generated
text, and which check failed. If the validator starts refusing often, the
knowledge base has a gap and the fix is content, not tuning.

---

## What stays at prompt level, and why

**Answer length (~120 words) stays a prompt instruction.** It is the one rule
where failure is cosmetic rather than dangerous — a 200-word answer is worse
UX, not a safety incident. Measure it, report it, don't gate on it.

Everything with a safety consequence moves into the validator.

---

## Re: the ₹15,000 "leak" — a correction to my own instruction

I flagged a rupee figure appearing under `RULE4_figures_suppressed` as a
shipping blocker. The finding is correct and important — **the prompt rule
demonstrably does not hold, 1 case in 3.**

But the specific content was fine. The model quoted **₹15,000 funeral
expenses under s.76(7)**, which is written into the Code itself, is
`verified_primary`, and does not depend on either missing notification. It
was legally correct and useful.

**My rule was the thing that was wrong**, not the output. RULE 4 suppressed
*all* figures whenever *any* chunk in the set was a blocker — far too blunt.
Under Check 2 this answer passes correctly, and the figures that actually
matter still cannot get through.

Worth stating plainly so nobody "fixes" this by making the model more
cautious about quoting law it should be quoting.

---

## Corpus change this requires

`01_compensation_ss_code_2020.md` contains a `worked_example` chunk with
**₹15,59,850** in it — a computed illustration for developers. Under Check 2
that figure is verbatim in the context and would therefore **pass**, which is
exactly wrong.

**Remove the arithmetic from the indexed chunk.** The worked example belongs
in the legal partner's materials, not in the vector store. Once it is gone,
no unverified rupee amount exists anywhere in the corpus, and Check 2 alone
is sufficient — no figure-specific rules needed.

This is the simpler architecture: **keep unsafe numbers out of the corpus,
then require every number in the output to come from the corpus.**
