# Contributing

Thank you for looking at this project. It is a safety-critical prototype, so the
bar for changes is set by one rule:

> In a legal crisis, a confidently wrong answer is worse than no answer.

Read the [README](README.md) and [docs/progress-summary.md](docs/progress-summary.md)
first. They explain why the pipeline is ordered the way it is.

## What will not be accepted

A change is declined if it weakens a safety property to make something easier or
smoother. In particular:

- **Do not switch on the compensation calculator.** It is off until the two
  Central Government notifications under s.76(1)(a) and s.76(3) are located and a
  lawyer confirms them. It is enforced in code on purpose.
- **Do not let the model write contact details, or state a figure or citation that
  is not verbatim in the retrieved law.** The output validator exists because
  prompt rules alone failed in 3 of 6 answers.
- **Do not translate answers into Hindi or Punjabi with a machine.** The validator
  checks English, so a translation would put unchecked text in front of a family.
- **Do not add conversation history to the model's context.** Each message is
  answered on its own so that only retrieved, verified law reaches the model.
- **Do not loosen the retrieval gates or the similarity handling** without a
  measurement showing why. Scores are embedder-specific and do not transfer.
- **Do not put real case data in the repository.** That means WhatsApp numbers,
  message text, `cases.db`, `refusals.jsonl` and any credential.

## Changing the knowledge base

- Every chunk needs `status` and `source_type`. A chunk that cannot be classified
  is refused and never defaulted.
- One `status` and one `sphere` per file. A chunk that needs a different one gets
  its own file. See [docs/metadata-schema.md](docs/metadata-schema.md).
- Open each chunk with the question as a family would ask it, then give the law.
- Write quantities in both forms, for example "fifty per cent (50%)", so that the
  validator can ground either rendering.
- Re-run `python ingest.py` after any edit. It rebuilds the index so that a deleted
  chunk really leaves it.
- Cite primary sources only, and record where each fact was verified.

## Code conventions

- Comments explain *why*, with the measurement that motivated them. Please do not
  strip them.
- Use section dividers (`# ---- Name ----`) in any module over about 150 lines.
- Prefer a few lines of standard library to a new dependency.
- No emoji in Python. They are fine in the Markdown docs.
- Tests print `PASS` or `FAIL` per check and exit non-zero on failure. There is no
  pytest dependency.

## Before you open a pull request

Run the offline tests. All five must pass:

```bash
python test_gate.py
python test_classify.py
python test_ratelimit.py
python test_whatsapp.py
python test_meta.py
```

`test_classify.py` skips the cases that need a Groq key. If your change touches
routing, run it with a key and include the confusion matrix in the pull request.
If your change touches retrieval or the validator, run `python query.py --test`
and say what moved.

## Writing documentation

Documentation is written in British English, with no em dashes and no Oxford
commas. Keep a plain, direct tone, and say clearly when something is blocked or
unverified rather than working around it.

## Reporting a security problem

Please do not open a public issue. See [SECURITY.md](SECURITY.md).
