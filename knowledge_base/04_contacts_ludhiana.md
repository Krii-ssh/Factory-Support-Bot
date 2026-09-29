---
doc_id: contacts_ludhiana
title: "Ludhiana / Punjab referral contacts"
citation_label: "Referral directory — Ludhiana"
status: in_force
in_force_from: null
sphere: state
source_type: directory
jurisdiction: punjab_ludhiana
language: en
retrieved_on: "2026-08-13"
verification: mixed
review_required: true
recheck_by: "2026-11-13"
index: false        # contacts are NOT embedded — see note below
---

> **`index: false` as of 13 Aug 2026.** Day-1 testing showed contact chunks
> polluting retrieval badly: "what is the weather in Ludhiana" matched three
> of them (the word "Ludhiana" recurs throughout), and a directory chunk
> ranked #3 on the contractor-liability question, which would have suppressed
> a correct s.85 citation because `source_type: directory` is not `primary`.
>
> This file was always meant to live in SQLite, not the vector store —
> `metadata_schema.md` RULE 6 says so. De-indexing it enforces that at the
> source rather than filtering after the fact. Until the SQLite table exists
> (Day 3), the bot substitutes a single hardcoded legal-aid contact into the
> `[legal aid contact]` placeholder.

# Ludhiana referral contacts

> 🔴 **NOTHING IN THIS FILE SHOULD REACH A USER UNTIL A HUMAN HAS DIALLED
> IT.** Contact data decays fast, several Punjab government sites block
> automated retrieval, and a grieving family sent to a dead number at 9pm is
> a worse outcome than a bot that says "I'll have someone call you."
>
> Treat this as a to-verify list, not a directory. Set
> `verified_by_call: true` per entry once someone has actually phoned it.

---

## chunk: dlsa_ludhiana
`verification: verified_secondary` · `verified_by_call: false`

**District Legal Services Authority (DLSA), Ludhiana** — free legal aid.

- **Address:** ADR Centre, Ground Floor, Additional Block, District Courts
  Complex, Ludhiana
- **Phone:** 0161-2400051
- **Applications to:** The Secretary, District Legal Services Authority,
  Ludhiana
- **Web:** https://ludhiana.dcourts.gov.in/

Source: DLSA Ludhiana office notice (March 2025), hosted on the district
courts CDN.

> Free legal aid under the Legal Services Authorities Act is available as of
> right to several categories including women, children, SC/ST persons,
> industrial workmen, and persons below the prescribed income limit. **The
> widow of a factory worker will normally qualify** — but confirm the current
> Punjab income ceiling and the documents required before the bot promises
> eligibility.

**To verify before shipping:** whether 0161-2400051 is answered, its hours,
whether there is a front-office/legal-aid-clinic number that is better for a
distressed first-time caller, and whether Punjabi and Hindi are spoken.

---

## chunk: nalsa_helpline
`verification: UNVERIFIED` · `verified_by_call: false`

**NALSA national legal services helpline — 15100.**

> ⚠️ Widely published, but I did **not** confirm it from an official source
> in this pass, nor confirm that it is live and answered in Punjab.
> **Verify by calling before use.** A national three-digit helpline is the
> single most valuable thing the bot can give someone at 2am, which is
> exactly why it must not be wrong.

---

## chunk: esic_ludhiana
`verification: verified_secondary` · `verified_by_call: false`

**ESIC Sub-Regional Office, Ludhiana** — for the ESI branch of the fork
(dependants' benefit, funeral expenses).

- **Web:** https://sroludhiana.esic.gov.in/
- **Branch office locator:** https://sroludhiana.esic.gov.in/branchs/rosro_index
- Reports place the office on Gill Road, Industrial Area, Ludhiana.

> Address and phone **not** confirmed — esic.gov.in blocked automated
> retrieval. Needs a human to pull the current address, phone and the correct
> Branch Office for a given factory.
>
> Because ESI attaches a worker to a **specific Branch Office**, the bot
> cannot give one universal address. Best design: give the SRO as the entry
> point and let ESIC route them.

---

## chunk: punjab_labour_department
`verification: UNVERIFIED` · `verified_by_call: false`

**Punjab Labour Department** — for the competent authority handling
employee's compensation claims, and the Inspector-cum-Facilitator.

- **e-Labour Punjab portal:** https://pblabour.gov.in/
- **Contact page:** https://pblabour.gov.in/Static/ContactInformation

> ⚠️ pblabour.gov.in blocked automated retrieval. The **Assistant / Deputy
> Labour Commissioner, Ludhiana** address and phone must be collected
> manually. Reports place an Assistant Labour Commissioner office on Gill
> Road, Ludhiana — unconfirmed.
>
> **Also unresolved: who the "competent authority" for compensation claims
> in Punjab now is under the Code on Social Security.** Under the repealed
> Act it was the Commissioner for Workmen's Compensation. The Code renames
> the office. Punjab has notified *draft* Social Security (Punjab) Rules
> (Dec 2025) but these were not final at last check. **Until this is
> settled, the bot must not name an office for filing a compensation
> claim** — route to DLSA instead and let a lawyer direct them.

---

## chunk: still_to_source

**Not yet collected — all required before launch:**

- Chief Inspector-cum-Facilitator, Punjab (the officer named in Rule 7 of the
  OSH&WC Central Rules; Punjab equivalent needed)
- Competent Authority for employee's compensation, Punjab — office and
  address (see above)
- Punjab Pollution Control Board, Ludhiana regional office — for the
  chemical/gas-exposure flow (out of MVP scope, but in the original doc)
- Ludhiana Police Commissionerate — DCP office address for the s.173(4)
  BNSS escalation letter
- Office of the Executive Magistrate / SDM Ludhiana — relevant to the s.194
  BNSS inquest
- Trade union contacts: CITU Ludhiana, HMS Ludhiana, and the Textile-Hosiery
  Kamgar Union — these are often the fastest real-world route to help and
  the most likely to answer a phone at night
- Any NGO or labour-rights organisation in Ludhiana willing to take handoffs

> The union contacts deserve emphasis. Your original project doc identified
> community trust as a prerequisite, and a union rep who picks up is worth
> more to a family at midnight than a government office that opens at 10am.

---

## Design note — how the bot should handle contacts

Do **not** embed contacts as ordinary RAG chunks. Two reasons:

1. **They decay on a different clock than the law.** Statute changes
   annually; phone numbers change constantly. Mixing them into the same
   vector store means the whole corpus inherits the shortest shelf life.
2. **They must never be paraphrased.** An LLM that rewrites an address is a
   catastrophe. Contacts should be looked up from a **structured table
   (SQLite)** keyed by district and inserted into the response by string
   substitution — never generated.

Recommended shape:

```sql
CREATE TABLE contacts (
  id TEXT PRIMARY KEY,
  kind TEXT,              -- legal_aid | esic | labour | police | union | helpline
  district TEXT,
  name TEXT,
  address TEXT,
  phone TEXT,
  hours TEXT,
  languages TEXT,
  verified_by_call INTEGER DEFAULT 0,
  verified_on TEXT,
  source_url TEXT
);
```

Gate the referral step on `verified_by_call = 1`. If nothing in the district
is verified, the bot says a human will follow up rather than reading out an
unverified number.

---

## Sources

- [DLSA Ludhiana office notice (March 2025)](https://cdnbbsr.s3waas.gov.in/s3ec03cfcce0621b49c983991ead4c3d4d/uploads/2025/03/2025030570.pdf)
- [Punjab State Legal Services Authority — DLSA list](https://pulsa.punjab.gov.in/en/organization/district-legal-services-authority/)
- [ESIC Sub-Regional Office, Ludhiana](https://sroludhiana.esic.gov.in/)
- [e-Labour Punjab](https://pblabour.gov.in/)
- [Ludhiana district helplines](https://ludhiana.nic.in/helpline/)
