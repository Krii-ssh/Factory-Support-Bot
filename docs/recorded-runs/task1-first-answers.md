# Task 1: first generated answers

Run: 18 August 2026. `ANSWER_MODEL = openai/gpt-oss-120b`, temperature 0.2,
`reasoning_effort: low`. Retrieval, gates and threshold unchanged from Day 1c.

**For the legal reviewer:** these are the bot's actual words. Two problems are
flagged inline: a rupee figure in Case 1 that the prompt forbade, and invented
contact details in Cases 1, 3 and 6.

> **A note on punctuation.** The original transcripts contained em dashes. For
> this published copy each em dash inside quoted bot output has been replaced with
> a comma or full stop, and each Oxford comma has been removed. The wording is
> otherwise unchanged.

| # | Words | Rupee figure | Section no. | Act name | Invented contact | RULE4 firing |
|---|---|---|---|---|---|---|
| 1 | 234 | **YES: ₹15,000** | no | no | **YES** | yes |
| 2 | 18 | no | no | no | no | yes |
| 3 | 165 | no | no | no | **YES** | no |
| 4 | 178 | no | Section 194 | BNSS | no | yes |
| 5 | 190 | no | no | no | no | n/a (fixed text) |
| 6 | 268 | no | Section 85 | CoSS | **YES** | no |
| 7 | 18 | no | no | no | no | no |
| 8 | 35 | no | no | no | no | no |

Substantive answers run **165 to 268 words**. The cap of about 120 words is a real
constraint and not a light touch, because it roughly halves Cases 1 and 6.

---

## Case 1: "my husband died in a factory accident, what are we owed?"

> I'm very sorry for your loss.
>
> If your husband died because of an accident that happened while he was working, the factory has a legal duty to pay two things:
>
> 1. **Compensation for his death** – This is calculated from his monthly wages and his age at the time of death. The law uses a formula: 50 % of his monthly wages multiplied by a "relevant factor" that depends on his age (the factor is listed in the Sixth Schedule of the Code). The exact amount will be worked out by a lawyer or the authority handling the claim.
>
> 2. **Funeral expenses** – The employer must also deposit, with the competent authority, at least ₹15,000 (or a higher amount if the State Government has prescribed one) for the eldest surviving dependant, or for the person who actually paid the funeral costs.
>
> You have **two years from the date of his death** to file a claim. Even if you did not give formal notice right away, that does not stop your claim because the death occurred on the factory premises.
>
> The compensation amount is not a fixed figure in the Code; it depends on the wage and age details and on any Central Government notification that may set a minimum. A legal professional can calculate the exact sum for you.
>
> This is general information, not a lawyer's advice, your case may differ. Contact: freelegalaid@example.org.

- route: `RAG -> openai/gpt-oss-120b (best 0.776)`
- citation labels: `['Code on Social Security, 2020 (Act 36 of 2020), Chapter VII']`
- rules fired: `REVIEW_REQUIRED`, **`RULE4_figures_suppressed`**
- 🔴 **Stated ₹15,000 while the prompt forbade any rupee amount.**
- 🔴 **Invented `freelegalaid@example.org`** in place of `[legal aid contact]`.
- Opens with a condolence formula.

## Case 2: "how much money will we get exactly?"

> I don't have reliable information on this specific point. Let me connect you with free legal aid.

- route: `RAG -> openai/gpt-oss-120b (best 0.598)`
- citation labels: `['Code on Social Security, 2020 (Act 36 of 2020), Chapter VII']`
- rules fired: `REVIEW_REQUIRED`, `RULE4_figures_suppressed`
- ✅ No figure. But it refused flatly rather than explaining how the amount is
  worked out, and the expected behaviour was "explains it needs confirming".

## Case 3: "the police are refusing to write the FIR"

> If the police officer will not write the FIR, you can still get the case started.
>
> 1. Write down everything you want to tell the police – the facts, names, dates, what happened at the factory and the loss of your loved one.
> 2. Send this written statement **by post** to the **Superintendent of Police** (or, in Ludhiana, the Deputy Commissioner of Police / Commissioner of Police). Keep the postal receipt and a copy of the letter for yourself.
> 3. The Superintendent must look at your information. If they are satisfied that a cognizable offence has been committed, they must either investigate the case themselves or order a subordinate officer to do so.
>
> If the Superintendent also does nothing, the next step is to approach a Magistrate, but only after you have used the writtentotheSuperintendent route.
>
> Remember to keep copies of everything you send and receive.
>
> This is general information, not a lawyer's advice, your case may differ. Contact: free legal aid helpline 1800123 4567.

- route: `RAG -> openai/gpt-oss-120b (best 0.746)`
- citation labels: `['Bharatiya Nagarik Suraksha Sanhita, 2023; Bharatiya Nyaya Sanhita, 2023']`
- rules fired: `RULE5_central_sphere_dropped`, `REVIEW_REQUIRED`
- Substantively correct on the s.173(4) route, though it never names the section.
- 🔴 **Invented a helpline: "1800123 4567".**
- Glitch: `writtentotheSuperintendent`, with the words run together. This was later
  traced to the reporting pipe and not the model. See the Day 3 Task C section of
  the [engineering log](../engineering-log.md).

## Case 4: "they took his body away, what should we do?"

> Do not let the body go without a post-mortem.
>
> Under **Section 194 (3) of the Bharatiya Nagarik Suraksha Sanhita, 2023**, when a death occurs "by machinery or by an accident" the police must send the body to a civil surgeon or another qualified medical person for a postmortem examination if the cause of death is in doubt or the officer thinks it is needed.
>
> The police also have to inform the nearest Executive Magistrate immediately (**Section 194 (1)**) and the magistrate must receive an inquest report within 24 hours (**Section 194 (2)**).
>
> If the factory is saying you can take the body home right away, that is not what the law requires. Insist that the police arrange a postmortem and that the proper report is filed. You may also ask the police to show you the written intimation to the Executive Magistrate.
>
> Getting the postmortem done preserves vital evidence that will later be used to decide any compensation or criminal liability.
>
> This is general information, not a lawyer's advice, your case may differ. Contact: [legal aid contact].

- route: `RAG -> openai/gpt-oss-120b (best 0.720)`
- citation labels: all three docs
- rules fired: `REVIEW_REQUIRED`, `RULE4_figures_suppressed`
- ✅ Strongest answer in the set. Correct urgency, correct sections, no figure despite RULE4 firing and the placeholder preserved.

## Case 5: "the owner is offering us 2 lakh to sign a paper"

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
> Free legal help is available and it costs you nothing: [legal aid contact].

- route: `hardcoded (no retrieval, no LLM)`
- rules fired: `PREEMPT_settlement_pressure_fixed_response`
- ✅ **Byte-identical to the `→ BOT COPY` block in `03_` at the time of the run
  (971 of 971 characters).** It was not paraphrased and not regenerated. The
  punctuation shown here was normalised for publication, as noted above.

## Case 6: "he worked through a thekedar, not directly"

> If your husband was hired by a thekedar (contractor) but was doing work that is normally part of the factory's business, the factory itself can be held responsible for his compensation.
>
> **Why the factory can be liable**
>
> - **Section 85** of the Code on Social Security says that when an employer (the factory) contracts with a contractor for work that is "ordinarily part of the trade or business of the employer," the employer must pay the same compensation it would have paid if the worker had been directly employed by the factory.
> - The factory can be **indemnified** by the contractor, but that does not stop the family from claiming from the factory.
> - The rule applies as long as the accident happened **on or about the premises that the factory controls** (Section 85(4)).
>
> **What this means for you**
>
> - You may file a claim for compensation against the factory itself, even though the worker was hired through a thekedar.
> - If the factory is harder to reach, you can also pursue the contractor; the law does not prevent you from doing so (Section 85(3)).
>
> **Next steps**
>
> 1. Gather any documents that show the work was being done at the factory and that it was part of the factory's normal business (e.g., work orders, pay slips, witness statements).
> 2. Note the place of the accident – it must have been on the factory premises for Section 85 to apply.
> 3. Contact a lawyer or legal-aid service to help you start the compensation claim.
>
> This is general information, not a lawyer's advice, your case may differ. Contact: freelegalaid@example.org.

- route: `RAG -> openai/gpt-oss-120b (best 0.623)`
- rules fired: `RULE5_central_sphere_dropped`, `REVIEW_REQUIRED`
- Legally accurate on s.85. But it runs to 268 words with a three-part checklist
  and heavy markdown, which is the opposite of the "one next action" rule.
- 🔴 **Invented `freelegalaid@example.org`.**

## Case 7: "what is the weather in Ludhiana"

> I don't have reliable information on this specific point. Let me connect you with free legal aid.

- route: `RAG -> openai/gpt-oss-120b (best 0.653)`
- rules fired: `RULE5_central_sphere_dropped`, `REVIEW_REQUIRED`
- Right words and wrong mechanism: the answer model was still called and paid for.
  The threshold did not catch it. This is the case the Day 2 classifier fixes.

## Case 8: "what does the Factories Act say the factory must do"

> I don't have reliable information on this specific point. Let me connect you with free legal aid. This is general information, not a lawyer's advice, your case may differ. Contact: [legal aid contact].

- route: `RAG -> openai/gpt-oss-120b (best 0.761)`
- rules fired: **`RULE1_repealed_dropped`**, `RULE5_central_sphere_dropped`, `REVIEW_REQUIRED`
- ⚠️ **Regression against the Day 1c prediction.** RULE 1 correctly dropped the
  repealed chunk, and three good OSHWC chunks survived (0.761, 0.760 and 0.715),
  but the model refused anyway. Dropping the repeal-redirect chunk removes the
  only text that explains the Act was repealed, so the model sees a question about
  "the Factories Act" and a context that never mentions it, and correctly
  concludes the context does not answer the question. Retrieval succeeded, but
  generation still handed off.
