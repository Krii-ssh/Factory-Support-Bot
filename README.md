# Factory Accident Support Bot

![Python](https://img.shields.io/badge/python-3.14-blue)
![Licence](https://img.shields.io/badge/licence-MIT-green)

A WhatsApp assistant for families of factory accident victims in Ludhiana,
Punjab. It helps a grieving family understand their legal rights, avoid being
pressured into a bad settlement and reach real legal aid.

It answers **only** from a curated corpus of verified, in-force law, and hands
off to a human whenever it is not certain. In a legal crisis a confidently
wrong answer is worse than no answer, and nearly every design decision in this
repository follows from that one rule.

> **Not for real families yet.** This is a research prototype. It has not been
> reviewed by a lawyer, the compensation calculator is deliberately switched
> off and it gives general information, not legal advice. See
> [Before anything reaches a family](#before-anything-reaches-a-family).

## Contents

- [Why it is built this way](#why-it-is-built-this-way)
- [How a message is handled](#how-a-message-is-handled)
- [Measured results](#measured-results)
- [Quick start](#quick-start)
- [Tests](#tests)
- [Project layout](#project-layout)
- [Documentation](#documentation)
- [Status](#status)
- [Before anything reaches a family](#before-anything-reaches-a-family)
- [Contributing and security](#contributing-and-security)
- [Licence](#licence)

## Why it is built this way

The obvious safety mechanisms for a retrieval-augmented bot do not work, and
each of the following was found by measurement rather than assumption:

- **A similarity threshold cannot tell scope.** "What is the weather in
  Ludhiana" scored 0.653, higher than three legitimate questions including "how
  much exactly will we get" at 0.598. Scope is a classification problem, so it
  is handled by a classifier.
- **A similarity threshold cannot tell law from repealed law.** A chunk of the
  repealed Factories Act retrieved at rank 1 with the highest score in the
  whole test suite (0.786). It is genuinely relevant. It is simply no longer
  law. Legal status is therefore checked with hard metadata gates before any
  similarity score is considered.
- **A safety rule in a prompt is a request, not a guarantee.** With the rules
  in the prompt alone, the model invented contact details in 3 of 6 answers,
  including a fake legal aid helpline. A deterministic output validator now
  checks every answer before it is sent, and contact details are appended by
  code so that a phone number never passes through the model.

Each mechanism was replaced with something deterministic. The full account is
in [docs/progress-summary.md](docs/progress-summary.md).

## How a message is handled

The order of these steps is the safety design, not an implementation detail.

```
incoming message
  -> intent classification    keyword pre-empt (offline), then an LLM classifier
  -> settlement pressure      fixed, pre-approved text; never reaches retrieval
  -> out of scope / status    handoff to legal aid; retrieval and the model are never called
  -> retrieve top-K           ChromaDB with all-MiniLM-L6-v2, run locally
  -> hard metadata gates      repealed law, wrong sphere and design documents dropped
  -> similarity floor         a floor against nonsense, not a relevance gate
  -> answer model             Groq, openai/gpt-oss-120b
  -> output validator         no contact details; every figure and citation must
                              appear verbatim in the retrieved law
  -> verified contact block   appended by code, after validation
```

A few properties worth knowing:

- **Settlement pressure never touches the network.** The one irreversible harm
  is a family signing away their claim, so that intent is caught by an offline
  keyword list before the classifier runs. The vocabulary lives in
  [settlement_keywords.txt](settlement_keywords.txt) so a Punjabi or Hindi
  speaker can extend it without touching code.
- **Every message is answered on its own, with no conversation history.** The
  model must see nothing but retrieved, verified law. Feeding earlier turns
  back in would put unverified text into the context an answer is built from.
- **Every answer carries its provenance:** the route taken, the chunks used,
  the rules that fired and the intent label. A reviewer grades sources rather
  than prose.
- **Every refusal is logged** to `refusals.jsonl` as evidence of a gap in the
  corpus, not counted as a success.

## Measured results

Measured under `sentence-transformers`. Scores do not transfer between
embedders.

| Result | Value |
|---|---|
| Repealed Factories Act chunk | rank 1 at **0.786**, dropped by the metadata gate |
| Weather question against a real one | **0.653** against **0.598** (off-topic scores higher) |
| Fabricated contacts, prompt rules only | **3 of 6** answers |
| Fabricated contacts, with the validator | **0** |
| Intent confusion matrix | **22 of 22**, zero misroutes |
| Pipeline cases | **8 of 8** |
| Answer length | 87 to 144 words, down from 165 to 268 |

## Quick start

### Offline layers

Parsing, the metadata gates, intent routing (keyword layer), rate limiting and
message splitting need nothing beyond the Python standard library:

```bash
python ingest.py --dry-run
python test_gate.py
python test_classify.py
python test_ratelimit.py
python test_whatsapp.py
python test_meta.py
```

### Full stack

The pinned versions in `requirements.txt` were measured on Python 3.14. Install
them into a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and add a [Groq](https://console.groq.com) API
key. Never commit `.env`.

```bash
python ingest.py          # embed the corpus into ./chroma
python query.py --test    # run the 8 recorded cases through the CLI
```

Without a Groq key the pipeline still runs end to end and reports exactly where
it stopped.

### Web chat

```bash
python -m uvicorn server:app --port 8000
```

Open <http://localhost:8000>. The panel beside each answer shows which law was
used and which safety rules fired. On Windows, `run_demo.bat` picks an
interpreter that has `chromadb` installed, starts the server and opens the
browser. `/health` reports whether credentials are the right shape and where
each key came from.

### WhatsApp

The Meta Cloud API adapter is the working path. The Twilio adapter is kept as a
fallback, but a Twilio trial account cannot send free-form text at all (error
21654). Set the four `WHATSAPP_*` values in `.env`, expose port 8000 over HTTPS
and register `<public-url>/meta` as the webhook. The step-by-step guide is
[docs/whatsapp-setup.md](docs/whatsapp-setup.md). To host it, see
[docs/deployment-render.md](docs/deployment-render.md).

Two behaviours of this layer are deliberate. The webhook acknowledges
immediately and answers out of band, because the pipeline can take longer than
a webhook is allowed to. Each sender's messages are also handled in order, so a
settlement warning cannot be overtaken by the answer to a follow-up question.

### Two things that will bite you

- **Re-run `ingest.py` after any corpus edit.** It rebuilds the index rather
  than upserting, on purpose: a chunk deleted from the corpus for a safety
  reason must actually leave the index.
- **Similarity scores do not transfer between embedders.** Chroma's bundled
  ONNX fallback truncates at 128 tokens, which leaves about two thirds of this
  corpus unembedded, so `MIN_SIMILARITY` is calibrated per embedder. Use
  `sentence-transformers`. The measurements are in `ingest.embedder()`.

## Tests

Each test file prints `PASS` or `FAIL` per check and exits non-zero on failure.
There is no pytest dependency.

| File | Covers |
|---|---|
| `test_gate.py` | The seven retrieval gate rules |
| `test_classify.py` | Routing, plus a confusion matrix (18 of 22 cases need a Groq key and are skipped without one, not passed) |
| `test_ratelimit.py` | Rate limiting, retry and typed transport failure |
| `test_whatsapp.py` | Twilio signature verification and message splitting |
| `test_meta.py` | Meta webhook parsing, signatures and delivery receipts |
| `test_server.py` | The webhook end to end (needs the full stack) |

The first five run in continuous integration on every push.

## Project layout

```
knowledge_base/                  the curated corpus (index: false files are never embedded)
  01_compensation_ss_code_2020.md   Code on Social Security, Ch. VII and Sixth Schedule
  02_fir_bnss_2023.md               BNSS and BNS: FIR, s.194 inquest
  03_esi_fork_and_settlement.md     settlement flow and fixed warning text
  04_contacts_ludhiana.md           referral directory, to be verified by phone
  05_employer_duties_oshwc.md       OSHWC Code 2020
  06_factories_act_repealed.md      repealed, kept to explain the repeal
  07_oshwc_central_rules.md         Central sphere, dropped for Ludhiana
  08_intent_classification.md       routing spec
  09_output_validation.md           validator spec
  10_esi_or_compensation.md         the ESI versus compensation fork

config.py            loads .env and resolves the writable paths
ingest.py            chunker, metadata, gate rules, Chroma writer
classify.py          intent classification and routing
query.py             retrieval, prompt assembly, output validator, CLI
groq_client.py       shared transport: rate limiting, retry, typed failure
tracker.py           SQLite case tracker (provenance, never message text)
server.py            FastAPI app: web chat, /meta and /whatsapp webhooks
meta_whatsapp.py     Meta Cloud API transport (preferred)
whatsapp.py          Twilio transport (fallback)
chat.html            the web chat surface
settlement_keywords.txt   trigger vocabulary: edit this, not the code

demo/                static replay of the recorded runs (open demo.html)
deck/                generator for the 10-slide project deck
docs/                setup guides, design notes, the legal sign-off checklist
render.yaml          Render blueprint
run_demo.bat         one-click launcher for Windows
```

## Documentation

| Document | What it is for |
|---|---|
| [docs/progress-summary.md](docs/progress-summary.md) | The whole story in one page. Start here. |
| [docs/status.md](docs/status.md) | The original brief against what has been delivered |
| [docs/metadata-schema.md](docs/metadata-schema.md) | Chunk fields and the seven retrieval rules |
| [docs/legal-partner-checklist.md](docs/legal-partner-checklist.md) | What a lawyer must sign off |
| [docs/setup-guide.md](docs/setup-guide.md) | First-time setup on Windows, for someone new to Python |
| [docs/whatsapp-setup.md](docs/whatsapp-setup.md) | Meta credentials, tunnel, webhook and troubleshooting |
| [docs/deployment-render.md](docs/deployment-render.md) | Hosting on Render |
| [docs/engineering-log.md](docs/engineering-log.md) | Dated log of what was measured and what went wrong |
| [docs/recorded-runs/](docs/recorded-runs/) | The bot's actual answers before and after the validator |
| [demo/demo.html](demo/demo.html) | Interactive replay of the recorded runs, no dependencies |

## Status

Working and verified: the knowledge base, retrieval, the metadata gates, the
output validator, the settlement warning flow, intent routing and the case
tracker. The settlement warning has been delivered to a real handset through
the Meta Cloud API, routed entirely offline.

Not built, or blocked:

| Item | State |
|---|---|
| Compensation calculator | Off, enforced in code. The Code delegates the minimum amount (s.76(1)(a)) and the wage ceiling (s.76(3)) to Central Government notifications that are not in the Act. Until they are found the bot explains the method and refuses to state a total. |
| Citing the settlement provision | Waits for a lawyer to confirm s.89 with s.74(7). Until then the warning cites nothing. |
| Hindi and Punjabi answers | The validator checks the English answer. Machine translation would put unchecked text in front of a family. |
| Voice | Not built. Voice input through Whisper would be safe. Voice output would not be. |
| Document generation | Deliberately not built. A document a family files is a larger liability step than an answer. |
| Hosted deployment | A Render blueprint exists. It has not been deployed. |

## Before anything reaches a family

1. Clear the two remaining `UNVERIFIED_BLOCKER` entries in
   `01_compensation_ss_code_2020.md`: the notified minimum under s.76(1)(a) and
   the wage ceiling under s.76(3).
2. Get a lawyer to confirm s.89 (with s.74(7)) as the basis for the settlement
   warning.
3. Phone every contact in `04_contacts_ludhiana.md` and record the result.
4. Have a native Punjabi or Hindi speaker extend `settlement_keywords.txt`.
5. Run the full confusion matrix in `test_classify.py` against a live key.
6. Have a legal partner review 15 to 20 transcripts. This is a hard
   prerequisite.

## Contributing and security

Read [CONTRIBUTING.md](CONTRIBUTING.md) first. The safety properties are the
point of the project, so a change that weakens one to make a demo smoother will
not be accepted. To report a vulnerability, see [SECURITY.md](SECURITY.md).

## Licence

Released under the [MIT Licence](LICENSE). The licence covers the code and
documentation. It does not make the bot's output legal advice, and the legal
texts in `knowledge_base/` remain subject to their own status as public
government publications.
