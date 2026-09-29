# Chunk metadata schema and retriever filter rules

The problem this solves: **a retrieval-confidence gate cannot tell the
difference between "no good answer" and "a very good answer from a repealed
statute".** A chunk of the Factories Act 1948 scores *high* similarity on "what
was the factory required to do". The gate passes it. The LLM is handed it as
authoritative context. The bot cites a repealed Act with confidence.

Similarity scoring cannot fix this, because the chunk genuinely is relevant. It
is just no longer law. Only metadata filtering fixes it.

---

## Field definitions

Every chunk inherits its document's frontmatter, plus per-chunk overrides.

| Field | Type | Values | Purpose |
|---|---|---|---|
| `doc_id` | str | any | Groups chunks by source document |
| `chunk_id` | str | `{doc_id}::{name}` | Stable identity for audit and citation |
| `citation_label` | str | any | **Exact string the bot may cite.** Never LLM-generated |
| `status` | enum | `in_force` · `repealed` · `draft` · `design_doc` · `unknown` | **The primary safety filter** |
| `in_force_from` | date | ISO | Lets you answer about incidents before a commencement date |
| `repealed_on` | date | ISO | Set with `status: repealed` |
| `supersedes` / `superseded_by` | str | any | Lets the bot redirect rather than dead-end |
| `source_type` | enum | `primary` · `secondary` · `directory` · `derived` | Gates whether a chunk may support a section citation |
| `sphere` | enum | `national` · `central` · `state` | Central Rules are not Punjab Rules |
| `jurisdiction` | str | `india` · `punjab` · `punjab_ludhiana` | Where the law applies |
| `verification` | enum | `verified_primary` · `verified_secondary` · `derived` · `UNVERIFIED` · `UNVERIFIED_BLOCKER` | Per-fact confidence |
| `review_required` | bool | true or false | Legal partner must sign off before this reaches a user |
| `retrieved_on` | date | ISO | Staleness tracking |
| `recheck_by` | date | ISO | Especially for `directory` chunks |
| `language` | enum | `en` · `hi` · `pa` | Language of the chunk |
| `index` | bool | default `true` | `false` means design or planning documents |

### 🔴 Authoring rule: one `status` and one `sphere` per FILE

`ingest.py` reads `status` and `sphere` from **document frontmatter only**. There
is no per-chunk override for either. Only `verification` has one.

A `status: repealed` line written inside a chunk body is **inert prose**. The
chunk embeds as whatever the document says, and a repealed chunk inside an
`in_force` document **will be served to a family as current law.**

This is not hypothetical. It happened on 18 August 2026: a Factories Act 1948
redirect chunk was placed inside `05_employer_duties_oshwc.md` with
`status: repealed` in its body. It ingested as `in_force`, retrieved at rank
**1** with the strongest similarity in the whole test suite (0.773), and RULE 1
never fired. In the same file, a `sphere: central` chunk ingested as `national`
and displaced the correct s.85 contractor answer.

**If a chunk needs a different `status` or `sphere`, give it its own file.**
This costs one file and removes a whole class of silent failure. It is also why
`06_factories_act_repealed.md` and `07_oshwc_central_rules.md` exist as separate
files rather than sections.

### Authoring rule: lead with how a family asks, then the law

Retrieval testing showed statute-verbatim chunks ranking *below* plain-prose
chunks, because a grieving person's phrasing resembles ordinary language and not
gazette text. `s76_death_formula`, the single most important chunk in the
corpus, sat at rank **7** and never entered the retrieval window on its own
flagship question.

Adding an opening paragraph in the register families actually use (*"Families
ask: my husband died in a factory accident, what are we owed?"*) moved it from
**7 to 1** (0.658 to 0.776), and pulled it into two other questions where it had
been absent. There was no code change and no `TOP_K` increase.

**Every chunk opens with the question as a family would ask it, then gives the
law.** The plain-language opening is load-bearing for retrieval, not decoration.
Do not "tidy" it away.

### Authoring rule: grounding includes the citation header

The output validator checks answers against the retrieved context, and each
chunk is injected with its `citation_label` as a header. Act names live in that
header, not in the chunk text, so **grounding includes the headers**. A test
harness that builds context from chunk text alone will wrongly report Act names
as ungrounded.

### Authoring rule: write numbers in both forms

The validator compares numerals literally. A quantity that exists in the corpus
only as words ("fifty per cent", "seven days", "forty-eight hours") cannot ground
the same quantity written as digits, and a correct answer is refused on its
phrasing. Write both forms, for example *"fifty per cent (50%)"*. Do not teach
the validator that words and numerals are equivalent, because that would destroy
the property that makes the figure check work: a *computed* figure cannot appear
verbatim anywhere.

### Why `source_type` matters independently of `status`

The original FIR source was a blog post. It was `status: in_force` in the sense
that it described current-ish practice, but it was `source_type: secondary` and
it got five section numbers wrong. **Secondary sources must never be the basis of
a citation**, even when they are current.

---

## Retriever filter rules

Apply in order. Each is a hard gate, evaluated **before** the similarity
threshold.

```
RULE 1  Repealed law is never operative advice.
  DROP chunks where status == 'repealed'
  UNLESS the query carries an explicit historical intent
         (incident_date < repealed_on).
  If a repealed chunk is the ONLY match, hand off to a human. Do not answer.

RULE 2  Design docs never reach the LLM.
  DROP chunks where index == false.

RULE 3  Citations require primary sources.
  If the drafted answer contains a section citation,
  every supporting chunk must be source_type == 'primary'.
  Otherwise strip the citation, or hand off.

RULE 4  Blockers cannot produce numbers.
  If any supporting chunk has verification == 'UNVERIFIED_BLOCKER',
  the answer may describe STRUCTURE but must not contain
  a rupee amount or a computed figure.

RULE 5  Sphere must match.
  For a Ludhiana query, DROP sphere == 'central' chunks
  unless the establishment is confirmed central-sphere.
  If only central-sphere chunks match, say the state position
  is unconfirmed and hand off.

RULE 6  Contacts are never generated.
  Contact chunks are not sent to the LLM at all.
  They are looked up and string-substituted,
  gated on a human having dialled the number.

RULE 7  Then, and only then, apply the similarity threshold.
```

Rule 1 is the one that would have caught the Factories Act problem. Rule 3 is
the one that would have caught the FIR blog post.

Rules 1, 2 and 5 are implemented in `ingest.apply_filters()`. Rules 3 and 4 are
implemented in `ingest.answer_constraints()`, which decides whether the model
may cite sections or state figures. Rules 6 and 7 are enforced in
`query.resolve()`, which withholds every `source_type: directory` chunk from the
model and applies the similarity floor last. Contacts reach a family only through
the verified constant appended by `query.with_contact()`.

---

## Answer-time provenance

Every substantive answer should log, and be able to show a reviewer:

```json
{
  "case_id": "...",
  "query": "...",
  "chunks_used": ["ss_code_2020_ch7::s76_death_formula"],
  "citation_labels": ["Code on Social Security, 2020, s.76"],
  "min_status": "in_force",
  "min_verification": "verified_primary",
  "rules_triggered": [],
  "handoff": false
}
```

This is what makes the legal partner's review of 15 to 20 transcripts actually
auditable. Without provenance, the reviewer is grading prose. With it, they are
grading sources, which is the thing that matters and is far faster to check.

---

## Status of the original source material

This table records the audit of the original collected sources. The files
themselves are kept outside the repository. The corpus that replaced them is in
`knowledge_base/`.

| Source file | `status` | `source_type` | Action taken |
|---|---|---|---|
| `employee compensation act 1923.md` | `repealed` | `secondary` | **Deleted.** Not the Act, has obsolete figures and omits factory workers from coverage |
| `Factories Act 1948.md` | `repealed` (`repealed_on: 2025-11-21`) | `primary` | Kept, tagged and excluded from operative advice |
| `OSHWC Code 2026.md` | `in_force` | `primary` | Renamed to 2020, then indexed |
| `OSH_WC_Rules central.md` | `in_force`, `sphere: central` | `primary` | Corrupt Devanagari stripped, sphere tagged and indexed |
| `First Information Report.md` | `repealed`-citing | `secondary` | **Deleted.** Replaced by `02_fir_bnss_2023.md` |
| `Chatbot Factory Workers Safety.md` | `design_doc` | `derived` | `index: false` |
| `factory_safety_bot_pipeline.md` | `design_doc` | `derived` | `index: false` |
