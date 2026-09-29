# Checklist for the legal partner and knowledge-base validator

A short list. Everything here blocks something specific from shipping, and it is
ordered by what it unblocks.

---

## 1. 🔴 Blocks the calculator: the two notifications

The Code on Social Security, 2020 deliberately delegates both figures. Neither
is in the Act, so no amount of reading the gazette will settle them.

**(a) Minimum death compensation: notification under s.76(1)(a).**
s.76(1)(a) reads "...or an amount as may be notified by the Central Government
from time to time, whichever is more." The repealed 1923 Act wrote ₹1,20,000
into the statute. **The Code writes no figure at all.**

- Has a notification been issued under s.76(1)(a)? What is the amount, and from
  what date?
- **If none has been issued**, does the floor simply not operate, so that only
  the formula applies? Or does something carry the old figure forward (for
  example s.164 savings or the General Clauses Act)?

**(b) Wage ceiling: notification under s.76(3).**
s.76(3): "The Central Government may, by notification, specify for the purposes
of sub-section (1), such monthly wages in relation to an employee as it may
consider necessary." This is the successor to s.4(1B) of the repealed Act, under
which ₹15,000 a month was the last notified cap.

- Has a notification been issued under s.76(3)? What figure, and from what date?
- If none, is the employee's **actual** monthly wage used uncapped?

> Until both are answered the bot describes the *structure* of the entitlement
> but states **no rupee figure**. This is enforced in code, not just in the
> prompt.

---

## 2. 🟡 Blocks the settlement-warning citation

**There is no successor to EC Act s.17 in the Code.** This is confirmed, not
merely unfound. There are zero occurrences of "null and void", and "relinquish"
appears only in the Chapter IV gratuity context. The blanket voiding provision
is gone.

The Code instead protects through **s.89 (Registration of agreements)**:

- **s.89(1) proviso (c):** the competent authority may **refuse to record** a
  settlement for **inadequacy of the sum** or where it was **obtained by fraud or undue influence or other improper means**, and may order restitution of
  sums already paid. It is expressly framed around agreements with **a woman or
  a person under a legal disability**.
- **s.89(1) proviso (a):** a seven-day notice period before recording.
- **s.89(3):** if no memorandum is sent, the **employer remains liable for the
  full compensation**, with deduction capped at half of what was paid.
- **s.74(7)(b):** an agreement made *in accordance with the Chapter* bars a civil
  suit for damages.

**Questions for the legal partner:**

1. Is s.89 (with s.74(7)) the correct basis for warning a family not to sign?
2. Is a **quick cash settlement at the factory, never sent to the competent
   authority**, ineffective to discharge liability? In other words, is s.89(3)
   the right thing to rely on?
3. **What do we tell a family who has already signed?** This is the most common
   real-world case and the question the project cannot answer. The current
   message says only "that is not the end of the road. Please still speak to a
   lawyer, and take a copy of whatever you signed."
4. May the bot cite s.89? **Until the answer is yes, it cites nothing.**

---

## 2b. Worked example, for your reference and not the bot's

This illustration was **removed from the bot's knowledge base** on 18 August
2026, because any figure sitting in the corpus becomes quotable to a family as
though it were their entitlement. It lives here instead. Please sanity-check the
method:

> Deceased aged 30, monthly wages ₹15,000.
> 50% of ₹15,000 = ₹7,500. Relevant factor at age 30 (Sixth Schedule) = 207.98.
> ₹7,500 × 207.98 = **₹15,59,850**. Add funeral expenses of not less than ₹15,000
> under s.76(7).
> Compare against the notified minimum under s.76(1)(a) (see item 1(a)) and pay
> whichever is higher.

Two questions: is the method right, and does a wage ceiling under s.76(3) cap the
₹15,000 input before the multiplication?

**Figures from the repealed regime, recorded here and deliberately nowhere
else.** These are held out of the bot's knowledge base entirely, because the
output validator permits any figure appearing in retrieved context. An obsolete
amount sitting in a chunk would have been quotable to a family as their
entitlement, and would have passed every safety check.

- Minimum death compensation written into the repealed 1923 Act: **₹1,20,000**
  (₹1,40,000 for permanent total disablement).
- Last notified monthly wage ceiling for computation under the repealed Act:
  **₹15,000**.

**Neither may be quoted to anyone** until the legal partner confirms whether an
equivalent has been notified under s.76(1)(a) and s.76(3). They are here solely
so that the previous position is known.

---

## 3. Sign-off on plain-language renderings

The bot's user-facing text is not a translation of the statute. It is a
plain-language rendering for a grieving and possibly non-literate reader. Please
check these specifically:

- The **settlement-warning message** (`03_esi_fork_and_settlement.md`), including
  the "thumb impression" line and the already-signed path.
- The **s.194 BNSS post-mortem urgency** message (`02_fir_bnss_2023.md`). We are
  telling families not to let the body go without a post-mortem, and if that
  framing is wrong it is very wrong.
- The **contractor (thekedar)** message: "the factory can still be responsible"
  (s.85).

---

## 4. Confirm, quickly

- **s.85(4):** the accident must be on or about premises the employer controls.
  Does this materially limit the thekedar case in practice?
- **ESI bar on double recovery:** the section of the Code carrying forward s.53
  of the ESI Act, 1948. We state the principle uncited.
- **ESI dependants' benefit:** the current rate and the share split among widow,
  children and parents. We currently say only "a monthly payment", with no
  numbers.
- **Competent authority in Punjab:** who now performs the old Commissioner for
  Workmen's Compensation function, and where they sit for Ludhiana.
- **DLSA eligibility:** does a factory worker's widow qualify as of right, and
  what does she need to bring?

---

## Already settled, no action needed

| Item | Position |
|---|---|
| Death formula | s.76(1)(a): 50% × monthly wages × relevant factor, or the notified amount, whichever is more |
| Relevant factors | Sixth Schedule verified from the gazette, with **age 31 = 205.95** |
| Funeral expenses | s.76(7): not less than ₹15,000, **in addition** to compensation |
| Medical expenses | s.76(5): actual expenditure reimbursed by the employer |
| Wage calculation | s.78: one-twelfth of the preceding 12 months (plus alternatives) |
| Limitation | s.82: **two years from the date of death**, and a defective notice is not a bar where death occurs on the premises (s.82(2)(a)) |
| Contractor liability | s.85(1): the principal employer is liable as if directly employing |
| Employer's fatal-accident report | s.73: within **seven days** to the competent authority |
| Default in payment | s.77(3): interest, plus damages, if unpaid within one month |
| FIR escalation | **s.173(4) BNSS** (not s.154(3) CrPC) |
| Inquest and post-mortem | **s.194 BNSS**: intimation to the Executive Magistrate and a report within 24 hours |
| Likely FIR section | **BNS s.106(1)**: death by a rash or negligent act, up to 7 years |
