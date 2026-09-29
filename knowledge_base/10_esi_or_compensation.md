---
doc_id: esi_or_compensation
title: "ESI or employee's compensation — which route applies"
citation_label: "Code on Social Security, 2020 — Chapter IV (ESI) and Chapter VII (Employee's Compensation)"
status: in_force
in_force_from: "2025-11-21"
sphere: national
source_type: primary
jurisdiction: india
language: en
retrieved_on: "2026-08-18"
verification: verified_secondary
review_required: true
---

# ESI or employee's compensation

> **Why this file exists.** The ESI fork was specified as the *first* branch
> point in the death flow, but the specification lives in
> `03_esi_fork_and_settlement.md`, which is `index: false` — so the bot had
> **no ESI content in the store at all** and would answer every compensation
> question down the Chapter VII route.
>
> Rather than build a stateful triage flow, the fork is expressed here as
> retrievable content. A compensation question now surfaces it naturally, and
> the answer tells the family to establish coverage before going anywhere.
> Simpler, and it fails safe.
>
> **No benefit rates appear here** — the dependants' benefit rate and the
> share split are still unverified. See the legal partner checklist.

---

## chunk: which_route_esi_or_compensation

*Families ask: where do we go to claim? Which office? What is the process for
getting compensation? My neighbour got a monthly payment but we were told
about a lump sum — why?*

**There are two different systems, and which one applies decides everything —
which office, which form, and whether the money comes as a lump sum or a
monthly payment.** It is not a choice; coverage decides it.

- **If he was covered by ESI** — the family claims **dependants' benefit**
  from ESIC. This is paid as a **monthly payment**, not a lump sum. ESIC also
  pays funeral expenses.
- **If he was not covered by ESI** — the family claims **compensation from
  the employer** under Chapter VII of the Code on Social Security. This is a
  **lump sum**, calculated from his wages and age, plus at least ₹15,000 for
  funeral expenses under s.76(7).

**A family covered by ESI cannot also claim employee's compensation for the
same death.** Going to the wrong office can cost months.

> Most registered factories in Ludhiana are ESI-covered, so this is the
> common case, not an edge case. Establish coverage first.

---

## chunk: how_to_tell_if_esi_covered

*Families ask: what is ESI? Was he covered? How do we know? We don't know
anything about ESI.*

**Nobody expects you to know the word "ESI". These questions usually settle
it:**

1. **Did he have an ESI card, or a Pehchan card?** This is the clearest sign.
2. **When he was ill, did you go to the ESI dispensary or ESI hospital?**
   Families often remember this even when they don't remember a card.
3. **Was money cut for ESI on his pay slip?**
4. **Were there 10 or more workers in the factory?**
5. **Did he earn about ₹21,000 a month or less?** That is the wage limit for
   ESI coverage.

Any "yes" to the first two points strongly suggests he was covered.

**If you are not sure, do not guess.** The ESI office can check using his
name and the factory's name. Getting this wrong sends the family to the wrong
office with the wrong papers.

> Design note: uncertainty here must produce a handoff, not a branch. "I
> don't know" is the most common answer to all five questions and must not be
> pushed into either route.

---

## chunk: contractor_worker_still_covered

*Families ask: he worked through a thekedar, not directly for the factory —
does he still get anything? The factory says he was not their worker.*

**Yes — being hired through a contractor does not remove the factory's
responsibility.**

Under **section 85(1)** of the Code on Social Security, where a factory
contracts out work that is **ordinarily part of its own trade or business**,
the factory is liable to pay compensation to a worker employed on that work
**as if that worker had been directly employed by it**.

Under **s.85(3)** the family may instead recover from the contractor,
whichever is actually reachable. Under **s.85(4)** this does not apply where
the accident happened away from premises the factory controls.

> "He wasn't our worker" is the standard first response from a factory after
> a contract worker dies. It is not the end of the matter. Keep any proof of
> the work — an ID card, wage records, photographs at the workplace, the
> names of co-workers.

---

## Sources

- Code on Social Security, 2020 (Act 36 of 2020), ss. 76, 85 — gazette text
  in the project folder
- ESI wage limit ₹21,000/month — [Ministry of Labour & Employment, Additional
  FAQs on Labour Codes (16.03.2026)](https://www.labour.gov.in/static/uploads/2026/03/a4ccf4c6d97c4f1f36a6d83f8c64213d.pdf)
