---
doc_id: oshwc_code_2020_duties
title: "What the factory was legally required to do — OSHWC Code, 2020"
citation_label: "Occupational Safety, Health and Working Conditions Code, 2020 (Act 37 of 2020)"
status: in_force
in_force_from: "2025-11-21"
supersedes: "The Factories Act, 1948 (repealed 21 Nov 2025)"
sphere: national
source_type: primary
jurisdiction: india
language: en
retrieved_on: "2026-08-13"
verification: verified_primary
review_required: false
---

# What the factory was legally required to do

> **Authoring note — read before editing this file.**
> Day-1 retrieval testing showed that chunks written as verbatim statute
> rank *below* chunks written in plain language, because a grieving family's
> phrasing resembles ordinary prose, not gazette text. **Every chunk here
> therefore opens with how a family actually asks the question, then gives
> the law.** Do not "clean this up" by leading with the statute — the
> plain-language opening is load-bearing for retrieval, not decoration.

---

## chunk: employer_duty_safe_workplace

*Families ask: was the factory supposed to keep him safe? Whose fault is it?
Could this have been prevented? Did they do anything wrong? Were there no
safety measures? What was the company supposed to do?*

**Yes — the employer carries a positive legal duty of safety, and it is not
conditional on the worker being careful.**

**Section 6(1), OSHWC Code, 2020** — every employer shall:

- **(a)** "ensure that workplace is free from hazards which cause or are
  likely to cause injury or occupational disease to the employees";
- **(d)** "provide and maintain, as far as is reasonably practicable, a
  working environment that is safe and without risk to the health of the
  employees";
- **(g)** ensure **no charge is levied on any employee** for anything
  provided for safety and health at the workplace — including medical
  examination;
- **(h)** in relation to a **factory**, "ensure and be responsible for the
  safety and health of employees, workers and other persons who are on the
  work premises of the employer, **with or without his knowledge**".

> Clause (h) is worth knowing. "With or without his knowledge" means the
> factory cannot escape responsibility by claiming it did not know a
> particular person was on the premises — which is the standard defence when
> a contract worker dies.

---

## chunk: employer_duty_specific_factory

*Families ask: the machine had no guard. There was no training. He was never
given equipment. The exit was blocked. Is that allowed?*

**Section 6(2), OSHWC Code, 2020** — specifically for a factory, the
employer's duties include:

- **(a)** "the provision and maintenance of plant and systems of work in the
  workplace that are safe and without risk to health";
- **(b)** arrangements ensuring safety in "the use, handling, storage and
  transport of articles and substances";
- **(c)** "the provision of such information, instruction, **training** and
  supervision as are necessary to ensure the health and safety of all
  employees at work";
- **(d)** maintenance of all places of work in a safe condition, and safe
  **means of access and egress**;
- **(e)** provision and monitoring of a safe working environment.

> Each of these is a specific, checkable failure. "There was no training" and
> "the emergency exit was locked" are not vague grievances — they map onto
> s.6(2)(c) and s.6(2)(d). This is the chunk that turns a family's account
> into something a lawyer can use.

---

## chunk: employer_duty_notify_accident

*Families ask: does the factory have to report the death? They are hiding it.
Nobody has been told. They said they would handle it quietly.*

**Section 10(1), OSHWC Code, 2020 — Notice of certain accidents.**

Where an accident occurs in an establishment "**which causes death**, or
which causes any bodily injury by reason of which the person injured is
prevented from working for a period of forty-eight hours or more", then in
relation to a **factory**, the **employer or manager** "shall send notice
thereof to such authorities, in such manner and within such time, as may be
prescribed by the appropriate Government."

In figures: the injury threshold is **48 hours**. Under s.73 of the Code on
Social Security a fatal accident must also be reported within **7 days**.

> Concealment is itself a breach. If nothing was reported, that is a
> documented failure that sits alongside whatever caused the death — and it
> is often easier to prove.
>
> Related duty under a different Code: **s.73 of the Code on Social
> Security** requires the employer to report a fatal accident to the
> competent authority **within seven days**. Two separate reporting duties,
> two separate failures if neither happened.

---

---

## chunk: which_law_applies_now

*Families, volunteers and local advocates ask: what does the Factories Act
say? Isn't the factory covered by the Factories Act 1948? What about Section
88? Which law applies to a factory accident now?*

**The law changed on 21 November 2025.** The Factories Act, 1948 no longer
applies. Factory safety and accident reporting are now governed by the
**Occupational Safety, Health and Working Conditions Code, 2020**, which
repealed and replaced it.

What this means in practice: the employer's duties are now in **section 6**
of the Code, and the duty to report an accident causing death is in
**section 10**. Both are set out above. The protections did not disappear —
they moved.

| People still name | Now governed by |
|---|---|
| Factories Act s.7A — duties of the occupier | **OSHWC Code, 2020, s.6** |
| Factories Act s.88 — notice of accidents | **OSHWC Code, 2020, s.10** |

> **Why this chunk exists, and why it is here rather than in `06_`.**
>
> Day 2 testing found that when the repealed Factories Act chunk was
> correctly dropped by RULE 1, the model had **no remaining text explaining
> that the Act had been repealed** — so it saw a question about a statute its
> context never mentioned, and refused to answer. Retrieval succeeded;
> generation handed off.
>
> The repeal is itself **current law** — s.143 of the Code is in force. So
> the redirect belongs in an `in_force` document, where it survives RULE 1.
> `06_` keeps only the repealed material that must never be served.

---

## Related files

The Factories Act redirect and the Central Rules content **used to live in
this file** and were moved out, because `ingest.py` reads `status` and
`sphere` from document frontmatter only — held here they ingested as
`in_force` / `national` and were served wrongly. See `06_`'s note.

- **`06_factories_act_repealed.md`** — the repealed Factories Act 1948
  redirect (`status: repealed`)
- **`07_oshwc_central_rules.md`** — Rule 7 / FORM-XI notification duties
  (`sphere: central`)

---

## Sources

- Occupational Safety, Health and Working Conditions Code, 2020 (Act 37 of
  2020) — gazette text in the project folder (`OSHWC Code 2026.md`,
  **misnamed; it is the 2020 Code**), ss. 6, 10, 143
