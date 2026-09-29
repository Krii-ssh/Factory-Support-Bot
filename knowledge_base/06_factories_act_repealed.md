---
doc_id: factories_act_1948_repealed
title: "The Factories Act, 1948 — REPEALED"
citation_label: "The Factories Act, 1948 (repealed w.e.f. 21 November 2025)"
status: repealed
in_force_from: "1948-09-23"
repealed_on: "2025-11-21"
superseded_by: "oshwc_code_2020_duties"
sphere: national
source_type: primary
jurisdiction: india
language: en
retrieved_on: "2026-08-13"
verification: verified_primary
review_required: false
---

# The Factories Act, 1948 — repealed

> **Why this is its own file.**
>
> `ingest.py` reads `status` and `sphere` from **document frontmatter only** —
> there is no per-chunk override for either. A `status: repealed` line written
> inside a chunk body is inert prose, and a repealed chunk sitting in an
> `in_force` document **will be embedded as current law and served to a
> family.** That is exactly what happened on the first attempt: this content
> lived inside `05_employer_duties_oshwc.md` and retrieved at rank #1 with the
> strongest score in the whole suite, with RULE 1 never firing.
>
> **Rule going forward: one `status` and one `sphere` per file.** If a chunk
> needs different values, it needs its own file. This costs nothing and
> removes an entire class of silent failure — no code change required.

---

## chunk: factories_act_repealed_redirect

*Families, volunteers and local advocates ask: what does the Factories Act
say? What about Section 88? Isn't the factory covered by the Factories Act
1948? What are the owner's obligations under the Factories Act?*

**The Factories Act, 1948 was repealed with effect from 21 November 2025** by
section 143(1)(a) of the Occupational Safety, Health and Working Conditions
Code, 2020. It no longer operates.

Provisions people commonly name, and where they now live:

| Repealed | Current equivalent |
|---|---|
| s.7A — general duties of the occupier | **s.6, OSHWC Code, 2020** |
| s.88 — notice of certain accidents | **s.10, OSHWC Code, 2020** |
| s.88A — notice of dangerous occurrences | **s.10, OSHWC Code, 2020** |
| s.92 — general penalty for offences | OSHWC Code, 2020, penalties chapter |

> The Factories Act remains the famous one — it is what people have heard of,
> what older advocates trained on, and what news reports still cite. The bot
> must **recognise** the name and move to the current provision. It must never
> answer *from* it.
>
> An incident that occurred **before 21 November 2025** may still engage the
> repealed Act. That is what the gate's `historical=True` path and the
> `repealed_on` date above are for. Do not use that path without a lawyer.

---

## Sources

- Occupational Safety, Health and Working Conditions Code, 2020, s.143(1)(a)
  — gazette text in the project folder (`OSHWC Code 2026.md`, misnamed; it is
  the 2020 Code), repeal list at line 4056
- [Labour code enforcement dates — SCC Online](https://www.scconline.com/blog/post/2025/11/26/enforcement-dates-of-labour-codes-legal-news/)
