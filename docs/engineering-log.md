# Engineering log

A dated record of what was built, what was measured and what went wrong, kept in
the order it happened. The original numbers are preserved so that the before and
after is visible, and mistakes are corrected in place with a note rather than
quietly edited.

Two cautions for a reader arriving cold. File names are as they were on the day
(for example `webhook.py` became `server.py` and `trigger_vocabulary.txt` became
`settlement_keywords.txt`). And the log was written to the project owner, so it
refers to their decisions where it says "your call".

> **Day 3 (20 August 2026): read [the Day 3 section](#day-3-whatsapp-webhook-text-only-and-case-tracker) first.**
> The knowledge base was revised three times in response to the Day 1 findings.
> All are now resolved: splitting the knowledge base so that each file carries
> one `status` and one `sphere` gave the repealed and central-sphere chunks their
> own frontmatter, and RULE 1 and RULE 5 now fire against real data. Case 7
> remains open by design.

---

# Day 1: retrieval core, what shipped, what was measured and what worried me

Delivered: `query.py`, a regenerated `chunk_manifest.json` (26 chunks) and the
knowledge base embedded into `./chroma`.

```bash
python query.py "my husband died in a factory accident, what are we owed?"
python query.py --test
```

`test_gate.py` still passes, with all 14 assertions.
*(Correction, Day 1c: it has **13** assertions and not 14. See the Day 1c
correction note.)*

**The LLM call was the one thing that could not be exercised.** `GROQ_API_KEY`
was not set anywhere on the machine (shell, user scope, machine scope or a
`.env`). Everything up to and including the assembled prompt was verified, and the
call itself returned a visible placeholder instead of an answer.

---

## The threshold, and why it cannot do the job it was assigned

**Chosen: `MIN_SIMILARITY = 0.55`.** It is cosine similarity, derived from
Chroma's squared-L2 distance (`sim = 1 - d/2`, and the MiniLM vectors were
confirmed to be unit-norm).

I calibrated it by measuring all 8 cases plus off-topic probes. The result is the
main thing to report: **the good questions and the nonsense questions occupy the
same similarity band, and the nonsense ones sit higher.**

| Question | Best similarity | Should |
|---|---|---|
| what does the Factories Act say (case 8) | **0.669** | refuse |
| where is the bus stand in Ludhiana | **0.659** | refuse |
| what is the weather in Ludhiana (case 7) | **0.653** | refuse |
| what was the cricket score last night | **0.636** | refuse |
| they took his body away (case 4) | 0.641 | **answer** |
| he worked through a thekedar (case 6) | 0.623 | **answer** |
| how much money exactly (case 2) | 0.598 | **answer** |

The lowest must-answer score is 0.598 and the highest must-refuse score is 0.669.
The bands are **inverted**, so no threshold satisfies both. Set it above 0.598 and
the bot starts refusing grieving families before it starts refusing the weather.

I tried the two standard rescues before accepting this. Neither works:

| Statistic | min(answer) | max(refuse) | Result |
|---|---|---|---|
| top similarity | 0.598 | 0.669 | overlaps |
| gap (top minus corpus mean) | 0.056 | 0.139 | overlaps |
| z-score ((top minus mean) divided by std) | 1.72 | 2.85 | overlaps |

The relative measures are *worse*. "What is the weather in Ludhiana" has the
single highest z-score of anything tested (2.85), because it locks onto one chunk
that happens to say "Ludhiana" and is uniformly unlike everything else, which is
exactly the shape of a confident match.

And because the overlap is in **rank order**, no rescaling of the distance fixes
it. Cosine, dot product and raw L2 all rank case 7 above case 2.

So `MIN_SIMILARITY` shipped as a **floor against total nonsense and not a
relevance gate.** The code comment is honest about that. The real fix is the Day 2
intent classifier, which is the right tool: the question "is this about a factory
accident at all?" is a classification problem, and it could not be turned into a
distance problem.

---

## The 8 cases

| # | Behaved correctly? | What actually happened |
|---|---|---|
| 1 | **partly, see below** | Answers from s.76(7) funeral and s.74 liability. Figures **not** suppressed. |
| 2 | ✅ | Both blocker chunks retrieved and `RULE4_figures_suppressed` fired |
| 3 | ✅ | `bnss_173_4_sp_escalation` retrieved at rank 2 |
| 4 | ✅ | `bnss_194_inquest` at rank 1 |
| 5 | ✅ | Hardcoded, with no retrieval and no LLM. Also fires on romanised Hindi and Gurmukhi |
| 6 | ✅ | `s85_contractor_liability` at rank 1 |
| 7 | ❌ | Reaches the LLM. The threshold cannot catch it, see above |
| 8 | ✅ **but not for the obvious reason** | See below |

### Case 1 was the biggest surprise

The expected behaviour was "no rupee figure (blocker chunks)". It did not do that,
and the reason is not the gate, which is fine. **`s76_death_formula` ranked 7th
for that question, so with `TOP_K = 5` it never entered the window and the figure
gate never armed.**

The bot answered from `s76_funeral_expenses` (rank 1) and `s74_employer_liability`
(rank 2) instead. So it explained the employer's duty and the ₹15,000 funeral
minimum, both `verified_primary` and both safe to state, but it never reached the
actual death-compensation structure, which is what the question was asking about.

The near-miss is worth understanding. The death-formula chunk is verbatim statute
("fifty per cent. of the monthly wages... multiplied by the relevant factor"). The
funeral chunk carries a plain-language rendering ("the factory must pay at least
₹15,000 towards funeral costs"). **A widow's phrasing matches the plain-language
rendering and not the statute.** The chunks written for humans retrieve better
than the chunks transcribed from the gazette.

Two fixes, both one-liners:

- `TOP_K = 7` in `query.py`. This pulls the blocker in and arms the figure gate.
  It is the safe direction and costs a little context noise.
- Add a `> Plain-language rendering:` block to `s76_death_formula`, the way s.74
  and s.76(7) already have one, and re-run `ingest.py`. This is the better fix and
  it improves every death-compensation query, not just this one.

`TOP_K` was left at 5 because 5 was the specification, and because deciding which
chunks constitute a correct answer to a compensation question is a call for the
project owner and not for the implementer.

### Case 8 passes by absence and not by the gate

The bot does not answer from the Factories Act, but **there is no Factories Act
chunk in the corpus.** `knowledge_base/` held four files and the repealed Act was
never ingested. So RULE 1 never fires. It cannot fire, because there is nothing
for it to drop.

The bot answers about the Code on Social Security instead, which is current law
and correct, but it does not tell the family "that Act was repealed in 2025, here
is what replaced it", which is the genuinely useful answer.

The gate itself is sound. `test_gate.py` proves that a `status: repealed` chunk
gets dropped and logged. But that is a synthetic chunk, so **the rule that matters
most was, on that day, exercised only by its unit test.** If the Factories Act is
ever added to the knowledge base, RULE 1 will catch it. Until then, case 8 passes
for a weaker reason than it looks.

---

## One thing added that was not asked for

`metadata_schema.md` RULE 6 says contact chunks are never sent to the LLM. They are
looked up and string-substituted, gated on `verified_by_call`. `apply_filters()`
does not implement that rule, and Day 1 had no SQLite.

That left unverified phone numbers reachable by the LLM, against a file whose first
line says that nothing in it should reach a user until a human has dialled it.
Case 7 retrieved three contact chunks, and case 5 retrieved the NALSA helpline.

So `query.py` drops `source_type == "directory"` after `apply_filters()` and logs
`RULE6_contact_chunk_withheld:<chunk_id>`. It is three lines, in `query.py` only,
and `apply_filters()` was not touched.

It turned out to matter for a second reason. Contact chunks are
`source_type: directory`, so a single one surviving flips `may_cite_sections` to
False for the whole answer. Without this filter, **case 6 could not have cited
s.85**, because a directory chunk ranked third would have suppressed it. The rule
buys correct citations as well as safety.

It is trivially movable into `ingest.py` if that is preferred.

---

## Smaller things worth knowing

- **`03_esi_fork_and_settlement.md` is correctly skipped** by `index: false`, and
  is confirmed absent from the manifest. The settlement text is read out of that
  file at runtime instead of being pasted into `query.py`, so the legal reviewer
  edits one place and it cannot drift. It is also unreachable by retrieval by
  construction, because the only path to it is the keyword pre-empt.
- **The keyword check over-triggers, as intended.** It covers "sign", "paper",
  "settlement", "thumb", "full and final", "receipt" and "affidavit", plus
  romanised forms (`dastkhat`, `kagaz`, `samjhauta`, `angutha`, `razinama`),
  Devanagari and Gurmukhi. It fires on "he asked me to sign the FIR paper", which
  is a false positive worth keeping.
- **Python 3.14.5** was on the machine. The whole stack has cp314 wheels
  (chromadb 1.5.9, sentence-transformers 5.7.0, torch 2.13.0+cpu), so there were
  no source builds, but the install took about 15 minutes.
- **Windows console encoding:** `query.py` calls
  `sys.stdout.reconfigure(encoding="utf-8")`, without which ₹, dashes and Gurmukhi
  crash or turn into mojibake on the default code page. `ingest.py` does not do
  this, which is why its output shows `�` for em dashes.
- **`review_required` fires on every RAG answer**, because all three indexed
  documents carry it. It is logged as
  `REVIEW_REQUIRED_legal_partner_signoff_pending` on every substantive answer,
  which is correct but means the flag currently carries no signal. It will start
  discriminating once the legal partner clears files individually.

---

## What was not built

WhatsApp, Bhashini, voice, SQLite, document generation, the intent classifier, a
web UI and retry, caching or async. That was as specified.

## Housekeeping

There were two copies of the project. `factory_bot_kb_day1/` was the **v1**
extraction, and its `01` and `03` knowledge base files were the older versions.
`factory_bot_kb_v2.zip` was extracted over it, which matches the day's brief
(edited `01` and `03`, a stale manifest, plus `LEGAL_PARTNER_CHECKLIST.md`). The v1
originals are still in `factory_bot_kb_day1.zip` if needed.

---

# Day 1b addendum

Re-run against the revised knowledge base (`factory_bot_kb_v3.zip`, extracted 18
August 2026). **No code changed.** `./chroma` was deleted before re-embedding, so
none of the de-indexed contact chunks survive. This was verified directly: the
collection holds 26 ids and zero `contacts_ludhiana::*`.

Ingest now skips **two** files (`03_` and `04_`). The chunk count is **26**, the
same number as before by coincidence: 5 contact chunks left and 5 OSHWC chunks
arrived.

```
by doc_id:  ss_code_2020_ch7 13 · bnss_2023_fir_death 8 · oshwc_code_2020_duties 5
blockers:   ss_code_2020_ch7::s76_death_formula
            ss_code_2020_ch7::worked_example      (unchanged)
```

`test_gate.py` **all pass**, with no regression. It was run despite the condition
that it should only run if all three cases behaved, because it is free and because confirming the gate is intact is what localises the failure below.

## The 8 cases, after

| # | Best similarity | Top 3 chunk_ids | Rules fired |
|---|---|---|---|
| 1 | **0.776** | `s76_death_formula` · `s74_employer_liability` · `s76_funeral_expenses` | REVIEW · **RULE4_figures_suppressed** |
| 2 | 0.598 | `s76_funeral_expenses` · `s78_monthly_wages` · `s76_death_formula` | REVIEW · **RULE4_figures_suppressed** |
| 3 | 0.710 | `bnss_173_fir_registration` · `bnss_173_4_sp_escalation` · `bnss_175_3_magistrate` | REVIEW |
| 4 | 0.641 | `bnss_194_inquest` · `s76_death_formula` · `employer_duty_notify_accident` | REVIEW · RULE4_figures_suppressed |
| 5 | n/a | none (pre-empted) | PREEMPT_settlement_pressure_fixed_response |
| 6 | 0.626 | **`employer_duty_inform_family_central_rules`** · `s85_contractor_liability` · `s78_monthly_wages` | REVIEW |
| 7 | 0.653 | `s78_monthly_wages` · `employer_duty_inform_family_central_rules` · `what_the_family_should_secure` | REVIEW |
| 8 | **0.773** | **`factories_act_repealed_redirect`** · `employer_duty_safe_workplace` · `employer_duty_notify_accident` | REVIEW |

There was no `RULE6_contact_chunk_withheld` anywhere. The filter now finds nothing
to drop, exactly as predicted. It stays in as the second line of defence.

## The three questions

### 1. Does `s76_death_formula` enter the top 5 on case 1? Yes, at rank 1

| | Rank | Similarity |
|---|---|---|
| before | 7 | 0.658 |
| after | **1** | **0.776** |

It did not merely enter the window, it took the top of it: +0.118, past four
chunks that previously beat it. `RULE4_figures_suppressed` now fires on case 1.
**`TOP_K` stays at 5**, because the content fix made the code change unnecessary,
which was the point.

The effect generalises. `s76_death_formula` also appears at rank 3 on case 2 and
rank 2 on case 4, having been absent from both before, and case 4 now suppresses
figures as a result. This was the cheapest and highest-leverage of the three
fixes.

### 2. Does case 7 fall below 0.55? No, it is unchanged at 0.653

The hypothesis does not hold. Case 7's best similarity is **0.6533 before and
0.6533 after**, identical to four decimal places, because its top hit was never a
contact chunk. It was and remains `s78_monthly_wages`, a statute chunk unaffected
by de-indexing.

De-indexing removed contact chunks from case 7's raw list (they held ranks 1, 3
and 5), but `RULE6` was already excluding those from the threshold decision on Day
1, so the number the threshold actually sees never moved. Doing it at source is
still right, because it gives a cleaner corpus with no reliance on a downstream
filter, but it has no bearing on this question.

**The threshold remains cosmetic.** 0.653 sits comfortably above the 0.55 floor,
case 7 still reaches the LLM, and the inverted-band problem is intact. The lowest
must-answer score is still 0.598 (case 2), so any threshold that catches the
weather question refuses a real one first. Case 7 needs the Day 2 intent
classifier. It is better stated flatly than dressed up.

### 3. Does case 8 retrieve the repealed chunk, and does RULE 1 drop it? It retrieves, and it does not drop

`factories_act_repealed_redirect` retrieves at **rank 1 with similarity 0.773**,
the strongest single retrieval in the whole suite. The redirect content works.

**RULE 1 does not fire.** `rules fired` on case 8 shows only `REVIEW`.

The cause is not the gate. **`ingest.py` does not support per-chunk `status` or
`sphere` overrides.** `load()` reads both from document frontmatter only
(`ingest.py:190-193`), and only `verification` has a per-chunk resolver
(`per_chunk_verification`, `ingest.py:136-151`). The `status: repealed` line in the
chunk body is inert prose. This was confirmed in the manifest:

```
factories_act_repealed_redirect            status='in_force'  repealed_on=None
employer_duty_inform_family_central_rules  status='in_force'  sphere='national'
```

Re-running the same gate over the same retrieved chunks with only the status
corrected, and no other change, gives:

```
rules fired : ['RULE1_repealed_dropped:oshwc_code_2020_duties::factories_act_repealed_redirect']
survivors   : employer_duty_safe_workplace · employer_duty_notify_accident
              s74_employer_liability · employer_duty_specific_factory
handoff=False   may_cite_sections=True   OSHWC s.6 content present: True
```

So the second half answers cleanly: **yes, with the repealed chunk dropped the
OSHWC s.6 content still surfaces and the question gets a correct answer and not a
handoff.** Four chunks survive and citations stay permitted. The design is right,
and the tag never reaches the store.

It is worth stating plainly that, at that point, the chunk was servable as
`in_force`, `verified_primary`, at rank 1, with `may_cite_sections=True`. The
chunk's own text says the Act was repealed and redirects to s.6 and s.10, so an
answer drawn from it would probably still be correct, because the content defends
itself. But the gate was not defending it, and the gate was the reason the chunk
was added.

## What got worse

**Case 6 regressed.** `employer_duty_inform_family_central_rules` took rank 1
(0.626), displacing `s85_contractor_liability` to rank 2 (0.623). That chunk is
the **Central** Rules, tagged `sphere: central` in the body for precisely this
reason, and RULE 5 could not drop it, for the same root cause. So the thekedar
answer now led with rules that do not bind a Ludhiana factory.

The same simulation, with the sphere corrected:

```
rules fired : ['RULE5_central_sphere_dropped:...employer_duty_inform_family_central_rules']
top survivor: ss_code_2020_ch7::s85_contractor_liability
```

That chunk also sits at rank 2 on case 7, inflating an off-topic query.

**Net:** the ingest limitation costs one silently served repealed chunk, one
misapplied sphere and one displaced correct answer. It was the highest-value thing
to fix next, above anything in `query.py`.

## The fix that was not made

The code had not changed and this was a re-run, so `ingest.py` was not touched.
The change is about 6 lines in `load()`, mirroring the `per_chunk_verification`
pattern already there: resolve `status` and `sphere` per chunk from the body,
validate against the existing `STATUS` and `SPHERE` vocabularies and fall back to frontmatter. `repealed_on` has to come along with `status`, or RULE 1's
`historical=True` path has no date to compare against.

It is worth deciding deliberately rather than fast, because it changes what "a
chunk's status" means across the whole corpus, and `per_chunk_verification`
carries a comment about safety ordering (the blocker must win) that a status
resolver needs its own answer to.

There was a no-code alternative: split the repealed redirect and the
central-sphere rule into their own files with correct frontmatter. The current
ingest handles that perfectly today, and it costs one file each.

## Standing items, unchanged from Day 1

- **`GROQ_API_KEY` was still not set** in any scope, and there was no `.env`. Every
  route above is verified through prompt assembly, and no answer text had ever been
  generated. Everything in the tables is retrieval and gate behaviour, which is the
  part carrying the safety properties.
- `review_required` still fires on every RAG answer, because all indexed documents
  carry it, so the flag still carries no signal.

---

# Day 1c addendum

Re-run against `factory_bot_kb_v4.zip` (extracted 18 August 2026). `ingest.py` was
verified byte-identical, so the file split is doing all the work. `./chroma` was
deleted before re-embedding.

**The chunk count went from 26 to 27.** `03_` and `04_` are still skipped.

```
by doc_id:  ss_code_2020_ch7 13 · bnss_2023_fir_death 8
            oshwc_code_2020_duties 3 · oshwc_central_rules_2026 2
            factories_act_1948_repealed 1
by status:  in_force 26 · repealed 1     <- first repealed chunk ever in the store
```

Blockers are unchanged: `s76_death_formula` and `worked_example`.

## The fix, confirmed from the manifest

This is read out of `chunk_manifest.json` and not the source files:

```
factories_act_1948_repealed::factories_act_repealed_redirect
    status='repealed'   repealed_on='2025-11-21'   warnings=['repealed_law']

oshwc_central_rules_2026::employer_duty_inform_family      sphere='central'
oshwc_central_rules_2026::form_xi_notice_of_accident       sphere='central'
```

`ingest.py`'s own `repealed_law` warning fired, which it had never done before.
`05_` retains only its three s.6 and s.10 chunks, with no duplication of the moved
content.

## The 8 cases, after

| # | Best similarity | Top 3 surviving chunk_ids | Rules fired |
|---|---|---|---|
| 1 | 0.776 | `s76_death_formula` · `s74_employer_liability` · `s76_funeral_expenses` | REVIEW · RULE4_figures_suppressed |
| 2 | 0.598 | `s76_funeral_expenses` · `s78_monthly_wages` · `s76_death_formula` | REVIEW · RULE4_figures_suppressed |
| 3 | 0.746 | `bnss_173_4_sp_escalation` · `bnss_173_fir_registration` · `bnss_175_3_magistrate` | **RULE5_central_sphere_dropped** · REVIEW |
| 4 | 0.720 | `bnss_194_inquest` · `s76_death_formula` · `s73_fatal_accident_report` | REVIEW · RULE4_figures_suppressed |
| 5 | n/a | none (pre-empted) | PREEMPT_settlement_pressure_fixed_response |
| 6 | 0.623 | `s85_contractor_liability` · `s78_monthly_wages` · `employer_duty_specific_factory` | **RULE5_central_sphere_dropped** · REVIEW |
| 7 | 0.653 | `s78_monthly_wages` · `what_the_family_should_secure` · `ch7_structure` | **RULE5_central_sphere_dropped** · REVIEW |
| 8 | 0.761 | `employer_duty_safe_workplace` · `employer_duty_notify_accident` · `s74_employer_liability` | **RULE1_repealed_dropped** · **RULE5_central_sphere_dropped** · REVIEW |

RULE 5 now fires on four separate cases against real data, and RULE 1 fires on
one. Neither had ever fired outside the unit test.

## The three questions

### Case 8: RULE 1 fires against the real store, and s.6 surfaces

```
rules fired : ['RULE1_repealed_dropped:factories_act_1948_repealed::factories_act_repealed_redirect',
               'RULE5_central_sphere_dropped:oshwc_central_rules_2026::form_xi_notice_of_accident',
               'REVIEW_REQUIRED_legal_partner_signoff_pending']
```

No `rule1_demo.py` and no patching was needed, so that scratch script is now
obsolete and can be deleted.

The repealed chunk retrieved at **rank 1 with similarity 0.786**, the single
strongest retrieval in the suite and ahead of everything. It is dropped anyway,
which is exactly the property that similarity scoring alone could never deliver
and the reason the metadata gate exists.

**And the question still gets a correct answer and not a handoff.** Three chunks
survive:

| Surviving chunk | Similarity |
|---|---|
| `oshwc_code_2020_duties::employer_duty_safe_workplace` (s.6) | 0.761 |
| `oshwc_code_2020_duties::employer_duty_notify_accident` (s.10) | 0.760 |
| `ss_code_2020_ch7::s74_employer_liability` | 0.715 |

`handoff=False` and `may_cite_sections=True`, and the citation labels carry the
**OSHWC Code, 2020**, which is the current law. The repealed Act's label appears
nowhere in the provenance. This is the case 8 behaviour asked for on Day 1, now
achieved by the gate and not by the Act's absence from the corpus.

### Case 6: `s85_contractor_liability` is back at rank 1, and RULE 5 fires

```
rules fired : ['RULE5_central_sphere_dropped:oshwc_central_rules_2026::form_xi_notice_of_accident', ...]
top survivor: ss_code_2020_ch7::s85_contractor_liability  (0.623, rank 1)
```

Both halves are yes. s.85 is rank 1 in the **raw** retrieval as well as after
filtering, and `form_xi_notice_of_accident` sits at rank 2 (0.621) and is dropped.
The Day 1b regression is cleared: the thekedar answer no longer leads with Central
Rules that do not bind a Ludhiana factory.

s.85's own score is unchanged at 0.6230. It did not get better. The thing
displacing it got removed.

### Case 1: `s76_death_formula` held rank 1, unmoved

| | Rank | Similarity |
|---|---|---|
| Day 1 | 7 | 0.658 |
| Day 1b | 1 | 0.7757 |
| Day 1c | **1** | **0.7757** |

The score is identical to four decimals. Two more files competing for the same
queries moved it not at all, because neither new file contains death-compensation
content, so there was nothing to compete with. `RULE4_figures_suppressed` still
fires.

### Case 7: the flat line, on the record

**0.6533 on the third measurement, identical every time.**

| | Best similarity |
|---|---|
| Day 1 | 0.6533 |
| Day 1b | 0.6533 |
| Day 1c | 0.6533 |

The top hit is `s78_monthly_wages` in all three runs. Nothing done to the
knowledge base across three revisions has moved this number, because nothing done
to it addressed the cause. The question is off-topic, and off-topic is not a
retrieval property. It stays above the 0.55 floor and still reaches the LLM.

RULE 5 did drop `form_xi_notice_of_accident` (0.635) from case 7's context, so the
query is now answered from a slightly cleaner set, but the threshold decision is
unchanged because the top hit was never the dropped chunk.

The Day 2 intent classifier remains the only thing that will move this.

## Side effects of the plain-language openings

The three chunks given openings all improved, and two changed rank:

| Chunk | Before | After | Rank |
|---|---|---|---|
| `bnss_173_4_sp_escalation` (case 3) | 0.703 | **0.746** | 2 to **1** |
| `bnss_194_inquest` (case 4) | 0.641 | **0.720** | 1 to 1, +0.079 |
| `s82_limitation` (case 1) | 0.699 | 0.702 | 5 to 5 |

Case 3 now leads with the escalation chunk itself and not the general registration
chunk, so a family asking "the police are refusing" gets s.173(4) first. Case 4's
margin over the next chunk widened from 0.023 to 0.102, so the post-mortem urgency
chunk now dominates its query instead of narrowly leading it.

The pattern from Day 1b holds across every chunk it has been applied to. It is the
highest-yield authoring change available, and `metadata-schema.md` now documents
it.

## Correction

Day 1 above says `test_gate.py` passes "all 14 assertions". **It has 13.** There
are 13 `check()` invocations, 13 PASS lines and `ALL PASS`. The 14 was an
arithmetic error on Day 1 that propagated into the Day 1c brief. Nothing
regressed, and 13 is the correct total, with all 13 passing.

## Standing items

- **`GROQ_API_KEY` still not set** in any scope, and no `.env`. Everything above is
  retrieval and gate behaviour, verified through prompt assembly. No answer text
  had been generated in any run.
- `review_required` still fires on every RAG answer. All indexed documents carry
  it, so the flag still carries no signal.
- `MIN_SIMILARITY = 0.55` and `TOP_K = 5` were untouched, as instructed.

---

# Day 2: generation, output validator and intent classifier

Corpus v7, 28 chunks. `ingest.py` was byte-identical throughout Day 2, because
every fix that day was content or post-generation code. `test_gate.py` **13 of 13,
run**.

## Models: both originals were retired

Neither model named in the brief exists any more. `GET /v1/models` returns 13
models and **no Llama chat models at all**.

| Role | Specified | Shipped |
|---|---|---|
| answer | `llama-3.3-70b-versatile` (retired, 404) | `openai/gpt-oss-120b` |
| classifier | `llama-3.1-8b-instant` (retired, 404) | `openai/gpt-oss-20b` |

**Observed TPM is 8,000 and not the documented 12,000**, verbatim from the 429:
`Limit 8000, Used 7536, Requested 2648`. It is per model, so the classifier has its
own bucket. At about 2,000 tokens per answer that is 3 to 4 answer calls per
minute. Every harness that day was paced, and no retry logic shipped in `query.py`.

Both gpt-oss models are reasoning models. `reasoning_effort: "low"` cuts reasoning
tokens about 5x (122 to 26 on a two-sentence answer) with no visible quality cost.

### The bug that had been invisible for two days

Groq sits behind Cloudflare, which rejects urllib's default User-Agent with
**403 "error code: 1010"** before the request reaches the API. Any explicit
User-Agent passes. Every "GROQ_API_KEY not set" run to date had been masking this,
and the first run with a real key hit it immediately.

## What the model actually said, first time (Day 2 Task 1)

The full transcript is in
[recorded-runs/task1-first-answers.md](recorded-runs/task1-first-answers.md). The
headline:

**The model fabricated contact details in 3 of 6 generated answers**:
`freelegalaid@example.org` twice and a helpline `1800123 4567` once. This was
against a corpus whose contacts file opens with *"nothing in this file should reach
a user until a human has dialled it."*

It also stated a rupee figure in a case where the prompt forbade it, 1 time in 3.
Both failures shared one cause: **the prompt asked the model to refrain, and the
model is only mostly obedient.** That is good enough to look fine in testing and not
good enough to trust.

## The output validator (Task A)

The validator is deterministic and uses no LLM, and it runs on the raw generation
**before** the contact block is appended. Otherwise the verified DLSA number trips
Check 1 itself.

| Check | Rejects |
|---|---|
| 1 | any email, URL or run of 7 or more digits |
| 3 | any section number or Act name not in the retrieved context |
| 2 | any numeral not verbatim in the retrieved context |
| 4 | logs every refusal to `refusals.jsonl` |

Contacts are now **appended by string concatenation** from one verified constant
(DLSA Ludhiana). The `[legal aid contact]` placeholder is gone from the system
prompt, because a blank in a template is an invitation to fill it in.

**Result: zero model-emitted contacts across all 8 cases.** Both fabricated
addresses and the invented helpline are gone.

### Two bugs found in the validator itself

- **A trailing comma was swallowed into the number token.** `\d[\d,]*` extracted
  `2023,` from "…Sanhita, 2023, the police…" and then failed to ground it. This was
  a general false-refusal generator, caught only because the unit test used the real
  Case 4 text and not a synthetic string. It was fixed by requiring the match to end
  on a digit.
- **Check ordering made the refusal log lie.** Check 2 ran first, so an invented
  `Section 999` was logged as an ungrounded *figure* and not an ungrounded
  *citation*. Both refuse, so there was no safety difference, but Check 4 exists so
  that a refusal says what kind of gap you have, and it was naming the wrong one.
  Check 3 now runs first.

A third fault was in the **test harness** and not the validator: contexts built from
chunk `.text` alone reported Act names as ungrounded. The Act names live in
`citation_label`, which is injected as a per-chunk header. **Grounding includes the
headers.** That is now an authoring rule in `metadata-schema.md`.

### The one refusal, and what it taught

Case 2 was refused on the token `50`. The model wrote "50 % of the monthly wage"
while the corpus transcribed the Code as **"fifty per cent."** in words. The draft
was otherwise entirely grounded and substantively correct.

The sharp part is that **case 1 and case 2 stated the same statutory fact and got
opposite outcomes**, decided by whether the model happened to write "half" or
"50 %". That is a coin flip.

That one token turned out to mark a class. More than 20 quantities existed in the
corpus only as words: "seven days", "forty-eight hours", "twenty-four hours",
"thirty times" and "fourteen days". Each was a latent false refusal waiting for a
differently phrased question. All now carry both forms.

After the corpus fix, **case 2 passes**: `50` grounds, the answer was 229 words at
the time, there were no new refusals and case 1 kept passing.

> The fix was content and not code. Teaching the validator numeral and word
> equivalence would have destroyed the property that makes Check 2 work at all,
> which is that a *computed* figure cannot appear verbatim anywhere.

## The intent classifier (Task B)

The pipeline is: **keyword check, classifier, retrieval, pre-generation gate,
generation, validator, append contact, send.**

The keyword check runs first and independently, because it cannot time out and a
missed settlement warning is unrecoverable. The trigger terms moved out of code into
`trigger_vocabulary.txt` (later renamed `settlement_keywords.txt`): 71 plain terms,
one per line, in English, romanised, Devanagari and Gurmukhi, with a header asking a
native speaker to extend it. Latin terms match on word boundaries and Indic terms
match anywhere.

At this point, a classifier failure or an unrecognised label routed to **handoff,
never to `death_case`**. That decision was later reversed. The fallback is now the
main answer flow, because a handoff on a transport blip silences a family who asked
a real question, and retrieval and the gates refuse safely on their own.

### Confusion matrix: 31 inputs

This is the effective routing label (keyword OR classifier). Raw-classifier-only was
identical on all 31, so the table serves for both.

| Expected \ got | settle | body | fir | death | status | oos |
|---|---|---|---|---|---|---|
| settlement_pressure | **6** | · | · | · | · | · |
| body_postmortem | · | **4** | · | · | · | · |
| fir_police | · | · | **3** | · | · | · |
| death_case | · | · | · | **10** | · | · |
| case_status | · | · | · | · | **1** | · |
| out_of_scope | · | · | · | 1 | · | **6** |

| Group | Score |
|---|---|
| Day 1 cases (8) | 8 of 8 |
| Boundary cases (13) | 13 of 13 |
| **Required total (21)** | **21 of 21, both must-be-perfect cells clean** |
| Held out, not in the prompt (10) | 9 of 10 |

**A caveat on the required 21.** The spec puts the 13 boundary cases in the
classifier prompt as few-shot examples *and* asks for a matrix over them, so 13 of
the 21 measure recall of the prompt and not generalisation. That is why the held-out
set exists.

### The held-out miss lands in a cell that must be perfect

`"is there any pension scheme for widows in punjab"` was classified **`death_case`**
and should have been `out_of_scope`. Government-scheme questions are named as
out_of_scope in the spec, and the indexed corpus has nothing on widow pensions (the
ESI dependants' benefit material is in `03_`, `index: false`).

On the required 21 the cell is perfect. On unseen input it is not. This is precisely
the failure the spec predicts, that *"models bias toward being helpful and will
stretch to fit a label"*, and "widows" plus "punjab" reads as death-adjacent. It was
not fixed by tuning. The honest reading is that the out_of_scope boundary needs more
held-out probes before launch, and probably a few more negative examples in the
prompt.

The blast radius is small. It routes to RAG, retrieval finds nothing about pensions
and the gate refuses safely. That is a wrong handoff and not a wrong answer.

### Case 7: the token saving, confirmed

`call_groq` was instrumented and the weather question was run end to end:

```
answer-model calls made : 0
route : handoff (out_of_scope), no retrieval and no answer call
```

Day 1's threshold could never catch this (0.653, above three legitimate questions).
Day 2 Task 1 showed the model refusing on its own, which gave the right words but
still made the call and still paid for it. Now it is routed before generation.
**Three days of measurement, one line of routing.**

The threshold is untouched at `MIN_SIMILARITY = 0.55` and stays what it always was:
a floor against nonsense and not a relevance gate.

### Belt and braces, unused this run

The classifier got all 6 settlement inputs right on its own, and the keyword check
fired independently on 3 of them and was never needed as a rescue. It stays, because
it is the path that survives a network failure, which is the scenario it was built
for.

## Answer length and register

This is prompt-level by design, because the failure is cosmetic and not dangerous.
It was measured and not gated:

| Case | Before (words) | After (words) |
|---|---|---|
| 1 | 236 | **118** |
| 4 | 171 | **74** |
| 6 | 172 | **103** |

All three are under the cap of about 120 words, all have the condolence opener gone
and all give a single next action instead of a checklist. Case 1 now leads with the
entitlement and closes on the post-mortem as the urgent step, which is what the spec
asked for and what the corpus says matters most in the first hours.

## Standing items

- `review_required` still fires on every RAG answer. All indexed documents carry it,
  so the flag still carries no signal.
- ~~The `writtentotheSuperintendent` token-mashing glitch appeared in Case 3 under
  gpt-oss-120b.~~ **Wrong, and corrected on Day 3.** The model emitted U+202F and
  U+2011 correctly, and the reporting pipe dropped them. See the Day 3 Task C
  section.
- `trigger_vocabulary.txt` needs a native Punjabi or Hindi speaker. The romanised
  spellings people actually type on a phone are not guessable from a desk.

---

# Day 3: WhatsApp webhook (text only) and case tracker

Corpus v8, **31 chunks**. `ingest.py` was still byte-identical, and `test_gate.py`
passed 13 of 13. `review_required` now discriminates as intended:

```
ss_code_2020_ch7  True    oshwc_code_2020_duties      False
bnss_2023_fir     True    factories_act_1948_repealed False
esi_or_compensation True  oshwc_central_rules_2026    False
```

The new ESI content is in the store (3 chunks) and is already surfacing. It appeared
in the retrieved set for the post-mortem question during the live webhook run.

## The milestone was not reached that day

**There were no WhatsApp credentials on the machine.** `WHATSAPP_TOKEN`,
`WHATSAPP_PHONE_NUMBER_ID`, `META_APP_SECRET` and `WHATSAPP_VERIFY_TOKEN` were unset
in every scope, and there was no `.env`. Reaching a real handset also needs a
publicly routable HTTPS URL registered with Meta, which the machine did not have.

So the settlement warning had **not** arrived on a real phone. That was the stated
milestone and it was the one thing not delivered. It was reached later, on 3
September 2026, once a Meta app and a tunnel existed.

What was done instead was the closest verifiable thing: `uvicorn` running
`webhook.py`, driven over real HTTP with the exact JSON envelopes the WhatsApp Cloud
API delivers, with outbound sends logged and not posted. Every layer except Meta's
own transport was exercised.

## What the live run did

```
GET  /webhook  correct verify token -> 200 "CHALLENGE_ACCEPTED"
GET  /webhook  wrong verify token   -> 403 "forbidden"
```

| Inbound | Intent | Route | Answer model called |
|---|---|---|---|
| "the owner is offering us 2 lakh to sign a paper" | settlement_pressure | keyword pre-empt | **no** |
| "they took his body away, what should we do?" | body_postmortem | RAG, best 0.722, validator PASS | yes |
| *(audio note)* | unsupported_media | fixed reply | **no** |
| "what is the weather in Ludhiana" | out_of_scope | handoff | **no** |
| duplicate of message 1 | none | ignored as duplicate | **no** |
| message stamped 30h old | none | **not replied to** | **no** |

The settlement reply went out first, with no retrieval and no model call of any
kind, carrying the case reference:

> Please stop and read this before you sign anything. […] Free legal help is
> available and it costs you nothing: District Legal Services Authority, Ludhiana,
> ADR Centre, Ground Floor, Additional Block, District Courts Complex, Ludhiana,
> 0161-2400051.
>
> Your reference number is LDH-1001. Keep it, because it helps us find your case.

The tracker recorded all four turns with full provenance and no message text:

```
settlement_pressure / answered   llm_called=False  PREEMPT_..._(keyword)
unsupported_media   / declined   media_type=audio
body_postmortem     / answered   llm_called=True
    chunk_ids: bnss_194_inquest, s73_fatal_accident_report,
               s76_death_formula, esi_or_compensation::contractor_worker_still_covered
    rules: RULE5_central_sphere_dropped, REVIEW_REQUIRED, RULE4_figures_suppressed
out_of_scope        / handoff    llm_called=False
```

## Task C, and a correction to what was reported on Day 2

I reported `writtentotheSuperintendent` as "token-mashing from gpt-oss-120b".
**That was wrong, and it would have sent the project owner looking in the wrong
place.**

The model's output was fine. `refusals.jsonl` is written to disk by Python without
passing through a console, and inspecting its codepoints shows the model emitted:

```
U+2011 NON-BREAKING HYPHEN      ...'is usually one‑twelfth of th'...
U+202F NARROW NO-BREAK SPACE    ...'equals **50 % of the mont'...
```

Both were intact. It was the PowerShell reporting pipe dropping them, which turned
`written to the Superintendent` into `writtentotheSuperintendent` and
`one‑twelfth` into `onetwelfth`. This was a display fault in the test harness and not
a product fault.

Normalising is still right, for a different reason than the one first given: U+202F
and U+2011 render inconsistently across WhatsApp clients and are read oddly by
text-to-speech. `normalise_output()` folds narrow and no-break spaces to a plain
space and non-breaking hyphens to `-`, and collapses runs of spaces and blank lines.
Em dashes, curly quotes and ₹ are deliberately left alone.

It runs **before** validation so that the checks see exactly the bytes the user gets.
I initially wrote in the code comment that this closed a hole where an exotic space
could hide a phone number from Check 1. **It does not**, because Python's `\s`
already matches U+202F. Both were tested, and the comment is corrected.

## What is stubbed, and what is simply absent

| Item | State |
|---|---|
| Bhashini, voice and text-to-speech | **absent by instruction**, with no branch and no stub |
| Outbound send | written, gated behind DRY RUN until credentials exist |
| Signature verification | implemented, and inert until `META_APP_SECRET` is set |
| `case_status` | still routes to handoff, per instruction, and the tracker is record-only |
| `cases.victim_name`, `factory_name` and `incident_date` | **columns exist and nothing populates them.** No extraction step exists yet |

That last row is the honest gap in Task B. The schema is as specified, but until
something asks the family for those details, or a human enters them, they stay null.
Every case is currently identified only by its WhatsApp number.

## Three things added that were not asked for

- **An immediate 200, with processing in a background task.** The pipeline takes
  seconds, and Meta re-delivers anything it considers slow, which would mean sending
  a grieving family the same message twice.
- **Duplicate-delivery suppression** (a bounded set of message ids). This is belt
  and braces on the same problem, and it was confirmed working when the driver
  re-sent message 1.
- **`X-Hub-Signature-256` verification.** Without it the endpoint accepts anything
  anyone posts to it. It was optional only because the secret was unset, and the app
  logs a warning at boot saying not to expose it publicly until it is.

## Two operational findings

**Cold start was about 16 seconds.** The first message after boot loads
all-MiniLM-L6-v2 (checking HuggingFace, then loading weights) before it can
retrieve. Meta is unaffected, because the 200 goes back immediately, but the
*family* waits sixteen seconds for the first reply of the day. Pre-warming the
encoder at startup would fix it, and it was left out as out of scope. It was fixed
later: `server.py` now loads the encoder at startup, and `query.py` constructs it at
import time.

**Replies were not ordered.** Background tasks run concurrently, so during the run
the audio reply overtook the post-mortem reply, which was still loading the model.
For one person sending two messages quickly, answers can arrive out of order. A
per-number lock is the obvious fix and it was left to be decided deliberately and not
at the end of a day. It was added later: `server.py` now holds one lock per sender.

## The 24-hour rule

On Day 3 this was enforced two ways in `webhook.py`. There was **no function that
could start a conversation**, so there was no template path, no nudge and nothing to
call. And every inbound message was checked against its own timestamp, so the
30-hour-old test message was logged and dropped without a reply.

The first property still holds, because `server.py` only ever replies to an inbound
message. The timestamp check did not carry over into `server.py` or
`meta_whatsapp.py`. If a stale message is ever delivered late, the bot will answer
it, and Meta will refuse the send if the 24-hour window has closed.
