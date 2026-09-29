---
doc_id: ss_code_2020_ch7
title: "Code on Social Security, 2020 — Chapter VII (Employee's Compensation)"
citation_label: "Code on Social Security, 2020 (Act 36 of 2020), Chapter VII"
status: in_force
in_force_from: "2025-11-21"
supersedes: "Employees' Compensation Act, 1923 (repealed 21 Nov 2025)"
sphere: national
source_type: primary
jurisdiction: india
language: en
retrieved_on: "2026-08-13"
primary_source: "Code on Social Security, 2020 (Act 36 of 2020), consolidated text as on 21 November 2025 — gazette PDF supplied by project owner"
verification: mixed          # see per-chunk verification flags below
review_required: true
---

# Chapter VII — Employee's Compensation (Code on Social Security, 2020)

> **Verified against the gazette text (as on 21 Nov 2025) on 13 Aug 2026.**
>
> The Sixth Schedule is now confirmed from the primary source. **Two items
> remain `UNVERIFIED_BLOCKER`** — both because the Code deliberately leaves
> the figure to a Central Government notification that is not part of the
> Code. They cannot be resolved from this document, by design.
>
> The calculator stays off until those notifications are located.

---

## chunk: ch7_structure
`verification: verified_primary`

Chapter VII of the Code on Social Security, 2020 runs from section 73 to
section 90:

| s. | Title |
|---|---|
| 73 | Reports of fatal accidents and serious bodily injuries |
| 74 | Employer's liability for compensation |
| 75 | Compensation in case of death of or injury in plantation |
| 76 | Amount of compensation |
| 77 | Compensation to be paid when due and damages for default |
| 78 | Method of calculating monthly wages for purposes of compensation |
| 79 | Review |
| 80 | Commutation of half-monthly payments |
| 81 | Distribution of compensation |
| 82 | Notice and claim |
| 83 | Special provisions relating to accidents occurring outside Indian territory |
| 84 | Medical examination |
| 85 | Contracting |
| 86 | Remedies of employer against stranger |
| 87 | Insolvency of employer |
| 88 | Power to require from employers statements regarding fatal accidents |
| 89 | Registration of agreements |
| 90 | Reference to competent authority |

This replaces the Employees' Compensation Act, 1923, repealed with effect
from 21 November 2025.

---

## chunk: s74_employer_liability
`verification: verified_primary`

*Families ask: does the factory have to pay us anything at all? They are
saying it was his own mistake. They say they are not responsible. Do we have
any right to money?*

**Yes — if he was hurt or killed by an accident that happened because of his
work and while he was at work, the factory has a legal duty to pay. It is a
right, not a favour.**

**Section 74 — Employer's liability for compensation.**

"If personal injury is caused to an employee by accident arising out of and
in the course of his employment, the employer shall be liable to pay
compensation in accordance with the provisions of this Chapter."

The test has two limbs and both must be met: the accident must arise **out
of** the employment (caused by a risk of the job) and **in the course of**
the employment (during working time/at the workplace).

> Plain-language rendering for the bot: *"If your husband was hurt or killed
> by an accident that happened because of his work, and while he was at
> work, the factory owner has a legal duty to pay compensation. This is not
> charity and it is not optional — it is his family's legal right."*

---

## chunk: s76_death_formula
`verification: UNVERIFIED_BLOCKER` — formula verified; minimum amount unresolved

*Families ask: my husband died in a factory accident, what are we owed? How
much compensation will we get? What money is the family entitled to after a
death at work? How is the amount decided? My son was killed at the factory —
what can we claim?*

**Compensation for a death at work is worked out from two things: how much he
earned each month, and how old he was.** Younger workers get a higher
multiplier, because the law is compensating for more lost working years. The
factory owes this whether or not anyone is prosecuted, and it is separate
from the funeral money.

In figures: the death calculation uses **50% (fifty per cent)** of monthly
wages; permanent total disablement uses **60% (sixty per cent)**.

The legal basis:

**Section 76(1)(a) — Amount of compensation. Death case.** *(verbatim)*

> "(1) Subject to the provisions of this Chapter, the amount of compensation
> shall be,—
> (a) where death results from the injury, an amount equal to **fifty per
> cent. of the monthly wages of the deceased employee multiplied by the
> relevant factor** or an amount as may be notified by the Central Government
> from time to time, **whichever is more**;
> (b) where permanent total disablement results from the injury, an amount
> equal to **sixty per cent.** of the monthly wages of the injured employee
> multiplied by the relevant factor or an amount as may be notified by the
> Central Government from time to time, whichever is more:
> Provided that the Central Government may, by notification, from time to
> time, enhance the amount of compensation specified in clauses (a) and (b)."

**Explanation** (verbatim): "relevant factor", in relation to an employee
means the factor specified in column (3) of the Sixth Schedule against the
corresponding entry in column (2), specifying the number of years which are
the same as the completed years of the age of the employee on his last
birthday immediately preceding the date on which the compensation fell due.

> ⚠️ `UNVERIFIED_BLOCKER #1` — **STILL BLOCKED, and now we know why.**
>
> Unlike the repealed 1923 Act — which wrote a minimum into the statute
> itself — **the Code contains no minimum figure at all.** It is entirely
> delegated: "an amount as may be notified by the Central Government from
> time to time."
>
> This cannot be resolved from the Code, by design. What is needed is the
> **Central Government notification issued under s.76(1)(a)**. The old Act's
> figure is recorded in the legal partner's checklist, deliberately not here.
>
> There is a real legal question for the lawyer, not just a lookup: **if no
> such notification has been issued**, then arguably only the formula applies
> and there is no floor. Nothing in the Code says the old figure carried
> over.
>
> ⚠️ **No rupee amount appears in this chunk on purpose.** The output
> validator permits any figure that is verbatim in retrieved context — so an
> obsolete amount written here would have been quotable to a family as their
> entitlement, and would have passed every check.
>
> The statutory **percentage** is a deliberate exception, added 19 Aug 2026.
> It is written in both forms — "fifty per cent (50%)" — because the Code
> spells it in words while the model renders it in numerals, and the
> validator compares literally. Task A case 2 was refused on exactly that
> mismatch while case 1 passed by writing "half", so the same statutory fact
> produced opposite outcomes depending on the model's phrasing.
>
> **This grounds the token `50`, not a rupee figure.** `50` cannot satisfy
> `50,000` or `₹1,50,000` — the validator requires a standalone match — so
> the blocker on the compensation total is untouched. The percentage is
> `verified_primary` from the gazette; the two notified amounts remain
> blocked.

---

## chunk: s76_funeral_expenses
`verification: verified_primary` — confirmed at **s.76(7)**

**Section 76(7) — funeral expenses.**

Where the injury results in death, the employer shall — **in addition to the
compensation under sub-section (1)** — deposit with the competent authority
a sum of **not less than fifteen thousand rupees**, or such amount as may be
prescribed by the State Government, for payment to the **eldest surviving
dependant**, or where the employee had no dependant or was not living with
them, to the person who actually incurred the funeral expenditure.

Note also **s.76(5)**: the employer must reimburse the **actual medical
expenditure** incurred for treatment of injuries caused during employment —
relevant where the worker survived some hours or days before dying.

> Plain-language rendering: *"Separately from the main compensation, the
> factory must pay at least ₹15,000 towards funeral costs. This is a
> separate amount — accepting it does not mean you have accepted the
> compensation."*

This is a useful early, concrete, low-risk fact for the bot: it is small,
verifiable, and gives a grieving family an immediate factual foothold.

---

## chunk: s78_monthly_wages
`verification: verified_primary`

**Section 78 — Method of calculating monthly wages.**

In figures: **12 months**, **1/12th**, **30 times**, **14 days**.

Three methods, in order of applicability:

1. **12 months or more of continuous service** — one-twelfth (1/12th) of the
   total wages earned in the twelve (12) months immediately preceding the
   accident.
2. **Less than one month of service** — the average monthly amount earned
   during the preceding twelve months by an employee doing similar work for
   the same employer, or if no such employee exists, for an employee doing
   similar work in the same district.
3. **Any other case** — thirty times the total wages earned during the last
   continuous period of service, divided by the number of days in that
   period.

Service is treated as **continuous** if a break did not exceed fourteen
days.

> This section matters more than it looks. Families almost never know the
> "monthly wage" figure the law wants. Many Ludhiana workers are paid
> partly in cash, on piece rate, or through a contractor. **The bot should
> ask what the family actually knows (weekly cash, per-piece rate, what was
> promised) and then say the wage figure must be established from records —
> not invent a number.**

---

## chunk: sixth_schedule_factors
`verification: verified_primary` — ✅ **RESOLVED 13 Aug 2026**

**THE SIXTH SCHEDULE** — *[See sections 75, 76(1) and 152(1)]*
**Factors for working out lump sum equivalent of compensation amount in case
of permanent disablement and death.**

Column (2) = completed years of age on the last birthday of the employee
immediately preceding the date on which the compensation fell due.
Column (3) = factor.

> ✅ **Blocker #2 cleared.** Transcribed directly from the gazette text of
> Act 36 of 2020 (as on 21 Nov 2025). The Code's Sixth Schedule **does**
> reproduce the values of the repealed Act's Schedule IV — confirmed, not
> assumed.
>
> ✅ **Age 31 dispute resolved: the correct factor is `205.95`.** India Code
> was right; the 205.98 figure carried by Tilak Marg is wrong. Anyone
> building from that secondary source would have overstated a 31-year-old's
> compensation slightly — small, but it would have been a visible error in a
> document filed with a competent authority.

| Age (completed years) | Factor | Age | Factor |
|---|---|---|---|
| Not more than 16 | 228.54 | 41 | 181.37 |
| 17 | 227.49 | 42 | 178.49 |
| 18 | 226.38 | 43 | 175.54 |
| 19 | 225.22 | 44 | 172.52 |
| 20 | 224.00 | 45 | 169.44 |
| 21 | 222.71 | 46 | 166.29 |
| 22 | 221.37 | 47 | 163.07 |
| 23 | 219.95 | 48 | 159.80 |
| 24 | 218.47 | 49 | 156.47 |
| 25 | 216.91 | 50 | 153.09 |
| 26 | 215.28 | 51 | 149.67 |
| 27 | 213.57 | 52 | 146.20 |
| 28 | 211.79 | 53 | 142.68 |
| 29 | 209.92 | 54 | 139.13 |
| 30 | 207.98 | 55 | 135.56 |
| 31 | 205.95 | 56 | 131.95 |
| 32 | 203.85 | 57 | 128.33 |
| 33 | 201.66 | 58 | 124.70 |
| 34 | 199.40 | 59 | 121.05 |
| 35 | 197.06 | 60 | 117.41 |
| 36 | 194.64 | 61 | 113.77 |
| 37 | 192.14 | 62 | 110.14 |
| 38 | 189.56 | 63 | 106.52 |
| 39 | 186.90 | 64 | 102.93 |
| 40 | 184.17 | 65 or more | 99.37 |

---

## chunk: how_the_amount_is_worked_out
`verification: UNVERIFIED_BLOCKER` — structure only; no arithmetic in this chunk

*Families ask: how do they decide the amount? Who calculates it? What do they
need from us to work it out? Why is my neighbour's family getting a different
amount?*

**The amount is not a fixed sum — it is calculated from his own wages and his
own age.** Two families from the same accident can receive very different
amounts for that reason.

What the calculation needs:

1. **His monthly wage**, established under s.78 — normally one-twelfth
   (1/12th) of the previous twelve months' (12 months') total wages.
2. **His completed age** on his last birthday before the compensation fell
   due, which sets the multiplier from the Sixth Schedule.

Half — **50%** — of his monthly wage is multiplied by that multiplier. The
younger he was, the higher the multiplier, because more working years were
lost. For permanent total disablement rather than death the share is **60%**.

**Funeral expenses under s.76(7) are separate and additional**, and do not
depend on this calculation.

> ⚠️ **No worked arithmetic appears in this chunk, deliberately.**
>
> A computed illustration used to live here. It was removed on 18 Aug 2026
> because the output validator (see `09_output_validation.md`) permits any
> figure that appears verbatim in retrieved context — so an example in the
> corpus would have been quotable to a family as though it were their
> entitlement.
>
> **No unverified rupee amount may exist anywhere in this corpus.** That is
> what makes the validator's grounding check sufficient on its own. The
> worked example now lives in the legal partner's materials.
>
> The two missing notifications (blockers #1 and #3) mean no total can be
> stated to anyone yet in any case.

> ⚠️ `UNVERIFIED_BLOCKER #3` — **STILL BLOCKED, and now we know the exact
> mechanism.**
>
> **Section 76(3)** (verbatim): *"The Central Government may, by
> notification, specify for the purposes of sub-section (1), such monthly
> wages in relation to an employee as it may consider necessary."*
>
> So the capping power **exists** and sits at s.76(3) — the successor to
> s.4(1B) of the repealed Act. But like the minimum, **the Code carries no
> figure**; it depends on a notification that is not part of this document.
>
> What is needed: the **notification under s.76(3)**. Until it is found, the
> bot must not apply a ceiling *or* assume there is none — both are guesses,
> and for a better-paid worker they differ by a factor of three or more. The
> old threshold figure is in the legal partner's checklist, not here, for the
> same reason as blocker #1.

---

## chunk: s73_fatal_accident_report
`verification: verified_secondary`

**Section 73 — Reports of fatal accidents.**

Where an accident causes death or serious bodily injury, the employer must,
**within seven days (7 days)**, send a report to the competent authority
setting out the circumstances attending the death or serious bodily injury. A
State Government may substitute a different authority.

> Useful to the family as a *lever*: if no report was filed, that is a
> documented failure by the employer that a lawyer can use.

---

## chunk: s77_payment_and_default
`verification: verified_secondary` — text not retrieved verbatim

**Section 77 — Compensation to be paid when due and damages for default.**

Compensation is payable as soon as it falls due. Where the employer is in
default beyond **one month (1 month)** from the date it fell due, the
competent authority may order recovery of the amount **plus interest**, and
where the default is without justification, **additional damages by way of
penalty**.

> ⚠️ The exact prescribed period and the interest/penalty rates were not
> retrieved verbatim. Do not quote a rate or a number of days until
> confirmed.

---

## chunk: s85_contractor_liability
`verification: verified_primary` — ✅ **corrects an earlier error in this file**

**Section 85 — Contracting.** *(the thekedar case — now resolved)*

> ⚠️ **Correction.** An earlier draft of this file described s.85 as the bar
> on parallel civil suits. That was wrong — it came from a secondary source.
> The gazette text shows s.85 is **principal-employer liability for
> contractor's workers**, which is far more useful here. The civil-suit bar
> is at **s.74(7)**, below.

s.85(1) (verbatim, condensed): where an employer contracts with a contractor
for the execution of work "**which is ordinarily part of the trade or
business of the employer**", the employer **shall be liable to pay to any
employee employed in the execution of the work any compensation which he
would have been liable to pay if that employee had been immediately employed
by him**. Compensation is calculated on the wages under the immediate
employer.

s.85(2): the principal employer is entitled to be indemnified by the
contractor.
s.85(3): nothing prevents the employee from recovering **from the contractor
instead**.
s.85(4): does not apply where the accident occurred **elsewhere than on or
about the premises** the employer controls.

> **This resolves the biggest practical gap in the Ludhiana context.** A
> worker engaged through a thekedar, killed on the factory premises doing
> work that is ordinarily the factory's business, has a claim **against the
> factory itself** — the factory cannot hide behind the contractor. And under
> s.85(3) the family may pursue whichever is actually reachable.
>
> The contractor case no longer needs blanket human handoff. It still needs
> care on the s.85(4) premises point.

---

## chunk: s74_7_civil_suit_bar
`verification: verified_primary`

**Section 74(7) — no double route.** No right to compensation arises if the
employee has instituted a **civil suit for damages** in a civil court for the
same accident; and no suit for damages is maintainable if (a) a compensation
claim has been made before a competent authority, or (b) **an agreement has
been made between the employee and employer providing for payment of
compensation in accordance with this Chapter.**

> Note limb (b): a settlement made *in accordance with the Chapter* closes
> off the civil route. Read this together with s.89 below — the two together
> are what the settlement-warning flow actually turns on.

---

## chunk: s82_limitation
`verification: verified_primary`

*Families ask: it has been a year already, is it too late? We never filed
anything at the time. Nobody told us we had to give notice. How long do we
have to claim? Can we still do something now?*

**You have two years — 2 years — from the date of death, and if he died on
the factory premises, the fact that nobody gave formal notice at the time
does not defeat your claim.**

**Section 82 — Notice and claim.** No claim is entertained unless notice of
the accident was given as soon as practicable **and the claim is preferred
within two years of the occurrence of the accident or, in case of death,
within two years from the date of death.**

**s.82(2)(a)** — want of, or any defect or irregularity in, the notice is
**not a bar** where the claim is in respect of the death of an employee from
an accident **which occurred on the premises of the employer**, or where the
employee was working under the employer's control, and died there or without
leaving the vicinity.

> Both halves matter. **Two years is a hard deadline** the bot should surface
> early — families often surface months later. And s.82(2)(a) means the
> typical factory death — on the premises — is **not** defeated by the family
> having failed to give formal notice. That is a reassurance worth giving.

---

## chunk: s89_registration_of_agreements
`verification: verified_primary` — **the settlement-protection provision**

**Section 89 — Registration of agreements.**

s.89(1): where a lump sum payable as compensation **has been settled by
agreement**, or where compensation is settled as payable **to a woman or a
person under a legal disability**, the employer must send a memorandum to the
competent authority, who records it **only "on being satisfied as to its
genuineness."**

Provisos:
- **(a)** no memorandum recorded **before seven days** after notice to the
  parties;
- **(c)** where it appears the agreement "**ought not to be registered by
  reason of the inadequacy of the sum or amount, or by reason of the
  agreement having been obtained by fraud or undue influence or other
  improper means**", the competent authority **may refuse to record it** and
  may make such order, **including as to any sum already paid**, as it thinks
  just.

s.89(3): where the memorandum is **not sent** as required, **the employer
remains liable to pay the full amount of compensation** under the Chapter,
and may not deduct more than half of any amount already paid.

> 🟡 **Strong candidate for the settlement-warning flow's legal basis — but
> keep the bot message uncited until your legal partner confirms.**
>
> The Code took a **different approach** from the repealed s.17. There is no
> blanket "relinquishment is null and void" provision anywhere in the Code
> (confirmed: zero occurrences of "null and void", and "relinquish" appears
> only in the gratuity context at Chapter IV). Instead the Code uses
> **registration-based scrutiny**: a settlement can be refused registration
> for **inadequacy** or **undue influence**, and an **unregistered settlement
> does not discharge the employer's full liability**.
>
> In practical effect this is *at least as protective* as s.17, and the
> "inadequacy" ground in proviso (c) is expressly tied to agreements with **a
> woman** — which is exactly the widow being pressured at the factory gate.
>
> The lawyer's question is no longer "where did s.17 go?" It is: **does
> s.89, read with s.74(7)(b), mean a quick cash settlement is
> voidable/ineffective — and what exactly should we tell a family who has
> already signed?**

---

## Blocker summary

| # | Blocker | Status |
|---|---|---|
| 1 | Notified **minimum** death compensation | 🔴 **Still blocked** — Code delegates it entirely; need the notification under s.76(1)(a) |
| 2 | Sixth Schedule + age-31 factor | ✅ **Cleared** — verified from gazette; age 31 = 205.95 |
| 3 | **Wage ceiling** on the s.76 input | 🔴 **Still blocked** — power exists at s.76(3); need the notification |
| — | Successor to EC Act s.17 | 🟡 **Likely s.89** (+ s.74(7)) — for legal partner to confirm; bot stays uncited |
| — | Contractor / thekedar liability | ✅ **Cleared** — s.85, principal employer liable |

---

## Sources

- [Code on Social Security, 2020 (Act 36 of 2020) — India Code](https://www.indiacode.nic.in/bitstream/123456789/16823/1/aA2020-36.pdf)
- [Arrangement of Clauses, Chapter VII — PRS India](https://prsindia.org/files/bills_acts/bills_parliament/2020/Code%20On%20Social%20Security,%202020.pdf)
- [Section 76 — Amount of compensation](https://kanoongpt.in/bare-acts/the-code-on-social-security-2020/chapter-vii-section-76-04f0c26e608a395a)
- [Section 78 — Method of calculating monthly wages](https://www.indianconstitution.in/2021/10/section-78-code-on-social-security-2020.html)
- [Schedule IV factors — India Code](https://upload.indiacode.nic.in/schedulefile?aid=AC_CEN_6_0_00041_192308_1523344685594&rid=751)
- [Schedule IV factors — Tilak Marg (cross-check)](https://tilakmarg.com/acts/employees-compensation-act-1923-schedules-iii-and-iv/)
- [Labour code enforcement dates — SCC Online](https://www.scconline.com/blog/post/2025/11/26/enforcement-dates-of-labour-codes-legal-news/)
