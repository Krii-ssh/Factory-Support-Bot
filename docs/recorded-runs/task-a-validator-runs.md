# Task A: the 8 cases through the output validator

Run: 18 August 2026, `ANSWER_MODEL = openai/gpt-oss-120b`, temperature 0.2,
`reasoning_effort: low`. Corpus v6 (28 chunks). The harness was paced at 30 seconds
between calls against the observed 8,000 TPM ceiling, and no retry logic shipped in
`query.py`.

Validation runs on the **raw generation**, before the contact block is appended.
Otherwise the verified DLSA number would trip Check 1 itself.

> **A note on punctuation.** The original transcripts contained em dashes. For
> this published copy each em dash inside quoted bot output has been replaced with
> a comma or full stop, and each Oxford comma has been removed. The wording is
> otherwise unchanged.

## Summary

| # | Validator | Words (model part) | Citation labels |
|---|---|---|---|
| 1 | **PASS** | 265 | CoSS Ch. VII |
| 2 | **REFUSED, CHECK2 on `50`** | handoff sent (18) | CoSS Ch. VII |
| 3 | **PASS** | 150 | BNSS / BNS |
| 4 | **PASS** | 171 | BNSS / BNS · CoSS Ch. VII · OSHWC |
| 5 | n/a, fixed text never generated | 188 | none |
| 6 | **PASS** | 172 | CoSS Ch. VII · OSHWC |
| 7 | **PASS** (model self-refused) | 31 | BNSS / BNS · CoSS Ch. VII |
| 8 | **PASS** | 116 | CoSS Ch. VII · OSHWC |

**Model-emitted contact details: zero, across all 8.** Every case reported `NONE
(clean)` after stripping the code-appended block.

Length runs from 116 to 265 words. Only case 8 is already under the target of about
120. The cap is a real constraint, unchanged from Task 1.

---

## Case 1: PASS (265 words)

> I'm very sorry for your loss.
>
> Because your husband died while working, the factory has a legal duty to pay you compensation. The amount is calculated from two things:
>
> 1. **His monthly wages** – the law uses half of his monthly salary.
> 2. **His age** – a "relevant factor" from a schedule is applied. Younger workers get a higher factor because they would have had more working years left.
>
> The formula is: ½ × monthly wages × the age-related factor. The exact factor depends on his age at his last birthday before the death. The final sum is the larger of this calculation or any amount the Central Government may have notified.
>
> In addition to that main compensation, the employer must also pay:
>
> * **Funeral expenses** – at least ₹15,000 (or a higher amount if the State Government has prescribed one) to the eldest surviving dependant or the person who paid the funeral costs.
> * **Medical expenses** – any actual medical costs incurred for treatment before he died must be reimbursed.
>
> You have a right to these payments; they are not optional or charitable. The claim must be filed within **two years of his death**. Even if you did not give formal notice right away, that does not bar the claim because the death occurred at the factory.
>
> To know the exact compensation you are entitled to, a lawyer will need to apply the formula using his wage details and age, and check whether any Central Government notification sets a minimum amount.
>
> This is general information, not a lawyer's advice, your case may differ.
>
> Free legal help, and it costs you nothing:
> District Legal Services Authority, Ludhiana, ADR Centre, Ground Floor, Additional Block, District Courts Complex, Ludhiana, 0161-2400051

- ₹15,000 is present and **correctly allowed**, because it is verbatim in
  `s76_funeral_expenses`.
- The fabricated email is **gone**.
- It expressed the percentage as "half" and "½", which is why it passed where case
  2 did not. See the refusal below.
- It still opens with a condolence formula (prompt-level, Task B).

## Case 2: REFUSED (see the full section below)

## Case 3: PASS (150 words)

> If a police officer will not record the information, you can send the details in writing to the next senior officer.
>
> 1. Write down everything you want to report – the accident, the names, dates, what happened.
> 2. Send this letter **by post** to the Superintendent of Police (or, in Ludhiana, the Deputy Commissioner of Police / Commissioner of Police). Keep the postal receipt and a copy of the letter for yourself.
>
> The Superintendent must look at your letter. If they are satisfied that a cognizable offence has been committed, they must either start the investigation themselves or order a subordinate officer to do so.
>
> If the Superintendent still does not act, you may then approach a Magistrate, but only after you have used the written-to-the-Superintendent step.
>
> Remember to keep copies of everything you send and receive.
>
> This is general information, not a lawyer's advice, your case may differ.
>
> Free legal help, and it costs you nothing:
> District Legal Services Authority, Ludhiana, ADR Centre, Ground Floor, Additional Block, District Courts Complex, Ludhiana, 0161-2400051

- The fabricated `1800123 4567` helpline is **gone**.
- The `writtentotheSuperintendent` glitch from Task 1 was later shown to be a
  reporting artefact and not a model fault.

## Case 4: PASS (171 words)

> Do not let the body go without a post-mortem.
> Under Section 194 of the Bharatiya Nagarik Suraksha Sanhita, when a death occurs "by machinery or by an accident" the police must:
>
> 1. Inform the nearest Executive Magistrate immediately.
> 2. Investigate the scene in the presence of witnesses and record the cause of death.
> 3. Send the body to the nearest Civil Surgeon or qualified medical person for a postmortem examination whenever the cause of death is in doubt or the officer deems it necessary.
>
> The postmortem report and the subsequent inquest report are the key documents that will later determine any compensation or criminal liability. If the body is released without this examination, vital evidence is lost forever.
>
> Ask the police to arrange the postmortem right away and to forward the report to the District or Sub-divisional Magistrate within 24 hours, as required by law. You may also request that the Executive Magistrate be present during the examination.
>
> This is general information, not a lawyer's advice, your case may differ.
>
> Free legal help, and it costs you nothing:
> District Legal Services Authority, Ludhiana, ADR Centre, Ground Floor, Additional Block, District Courts Complex, Ludhiana, 0161-2400051

- `Section 194` is grounded, and so is `24` (the chunk's own note writes "24
  hours").

## Case 5: fixed text, no generation and no validator

> Please stop and read this before you sign anything.
>
> If someone from the factory is offering you money now and asking you to sign a paper, a receipt or a stamp paper, please do not sign it yet, and please do not take a thumb impression on anything you have not had read to you by someone you trust.
>
> A paper like this is often written to say the family accepts this money as full and final, and gives up the right to claim anything more. The amount the law entitles a family to after a death is usually far more than what is offered in the first days. Once you sign, getting the rest becomes much harder.
>
> You are allowed to take time. You are allowed to say 'I will sign after I have shown this to a lawyer.' Nobody can require you to sign today.
>
> If you have already signed something, that is not the end of the road. Please still speak to a lawyer, and take a copy of whatever you signed.
>
> Free legal help is available and it costs you nothing: District Legal Services Authority, Ludhiana, ADR Centre, Ground Floor, Additional Block, District Courts Complex, Ludhiana, 0161-2400051.

- Byte-identity **holds** at the time of the run: `with_contact(settlement_response())
  == output` was `True`, and `[legal aid contact]` is no longer present. The
  placeholder was substituted with the verified constant and not filled in by a
  model.

## Case 6: PASS (172 words, down from 268)

> If your husband was hired by a thekedar (contractor) but was doing work that is normally part of the factory's business, the factory itself can be held responsible for his compensation.
>
> Section 85 of the Code on Social Security says that when an employer contracts with a contractor for work that is "ordinarily part of the trade or business of the employer," the employer must pay the same compensation it would have paid if the worker had been its direct employee. The family may also claim from the contractor, and can choose whichever party is easier to reach.
>
> This rule does not apply only if the accident happened **outside** the premises that the factory controls. If the accident occurred on the factory site, the factory cannot avoid liability just because the worker was hired through a thekedar.
>
> So, even though he was not a direct employee, you can seek compensation from the factory (and, if needed, from the contractor).
>
> This is general information, not a lawyer's advice, your case may differ.
>
> Free legal help, and it costs you nothing:
> District Legal Services Authority, Ludhiana, ADR Centre, Ground Floor, Additional Block, District Courts Complex, Ludhiana, 0161-2400051

- The fabricated email is **gone**. The three-part checklist is gone too, and the
  answer now ends with a single next step.

## Case 7: PASS, but the model refused on its own (31 words)

> I don't have reliable information on this specific point. Let me connect you with free legal aid. This is general information, not a lawyer's advice, your case may differ.
>
> Free legal help, and it costs you nothing:
> District Legal Services Authority, Ludhiana, ADR Centre, Ground Floor, Additional Block, District Courts Complex, Ludhiana, 0161-2400051

- The validator found nothing to reject. The answer model was still called and paid
  for. The Task B classifier is the fix.

## Case 8: PASS (116 words), and now answers instead of handing off

> The Factories Act, 1948 no longer applies to factory safety or accident reporting. The duties that used to be in the Factories Act are now set out in the Occupational Safety, Health and Working Conditions Code, 2020. Under that Code the employer must keep the workplace free from hazards, provide a safe environment and not charge workers for safety measures (section 6). If an accident causes death, the employer must report it to the authorities as required by section 10. So the current law that tells a factory what it must do is found in the OSHWC Code, not the old Factories Act.
>
> This is general information, not a lawyer's advice, your case may differ.
>
> Free legal help, and it costs you nothing:
> District Legal Services Authority, Ludhiana, ADR Centre, Ground Floor, Additional Block, District Courts Complex, Ludhiana, 0161-2400051

- `RULE1_repealed_dropped` still fires on the repealed chunk.
- "Factories Act" passes Check 3 because `which_law_applies_now` is `in_force` and
  names it. `section 6` and `section 10` are both grounded.

---

# The one refusal: Case 2, in full

**Question:** "how much money will we get exactly?"

**Check that failed:** `CHECK2_ungrounded_figure`
**Token that tripped it:** `50`, from the phrase *"50 % of the monthly wage"*.

**Withheld text (never sent):**

> The compensation is not a fixed sum. It is worked out from two things:
>
> 1. **Your loved one's monthly wage** – the law uses the figure calculated under s.78. That is usually one‑twelfth of the total wages earned in the twelve months before the accident, but other methods apply if the worker had less than a year of service or irregular pay.
>
> 2. **His completed age** on the last birthday before the compensation becomes due. The age determines a multiplier taken from the Sixth Schedule. A younger age gives a higher multiplier because more working years are lost.
>
> The formula in s.76(1)(a) says the amount equals **50 % of the monthly wage multiplied by the relevant factor**, or a higher amount if the Central Government has issued a notification setting a larger figure.
>
> In addition, the employer must pay **funeral expenses of at least ₹15,000** (or a higher amount prescribed by the State) under s.76(7), and must reimburse any actual medical costs incurred before death under s.76(5).
>
> Because the exact wage figure, the worker's age and any applicable government notification are needed, we cannot give a precise rupee amount here. You will need to gather pay slips, wage records and proof of age, and a legal aid officer can calculate the exact entitlement for you.
>
> This is general information, not a lawyer's advice, your case may differ.

**What the user got instead:** the handoff message plus the DLSA contact block.

## Why this is a corpus gap and not a validator bug

The actual case 2 context was probed (chunks: `how_the_amount_is_worked_out`,
`s76_funeral_expenses`, `s78_monthly_wages`, `s76_death_formula` and
`s89_registration_of_agreements`):

```
'50'               in context: False
'fifty'            in context: True
'15,000'           in context: True
'fifteen thousand' in context: True
```

The Code's text is transcribed as **"fifty per cent."** in words. The model rendered
it as **"50 %"** in numerals. The validator asks whether every numeral in the output
appears verbatim in the context, and `50` does not, so it refused. That is precisely
the specified behaviour.

Everything else in that draft was grounded: `₹15,000`, `s.78`, `s.76(1)(a)`,
`s.76(7)` and `s.76(5)` all check out. The answer was **substantively correct and
useful**, because it declined to give a total, explained the method and named the
documents to gather. It was withheld on a rendering difference.

The uncomfortable part is that **case 1 and case 2 state the same statutory fact
and get opposite outcomes.** Case 1 wrote "half" and "½" and passed, while case 2
wrote "50 %" and was refused. Which one a family gets was a coin flip on the model's
phrasing.

**Recommended fix: content, one line, no code change.** Add the numeral form
alongside the words in `s76_death_formula` and `how_the_amount_is_worked_out`, for
example *"fifty per cent (50%)"*. That grounds both renderings and the
inconsistency disappears. This fix was applied, and case 2 now passes.

**Not recommended:** teaching the validator numeral and word equivalence. That is
the relaxing that was warned against, and it would weaken the one property that
makes Check 2 work, which is that a computed figure cannot appear verbatim anywhere.

---

# Refusal log (Check 4)

`refusals.jsonl` holds one JSON object per line, with the fields `question`,
`check`, `offending` and `generated`. There was one entry from this run, the case 2
refusal above.
