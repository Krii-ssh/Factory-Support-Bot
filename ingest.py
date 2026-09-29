#!/usr/bin/env python3
"""
Knowledge-base ingest for the factory-accident support bot.

Parses YAML frontmatter + `## chunk: <name>` markers, attaches per-chunk
metadata, strips corrupt Devanagari, and writes to ChromaDB.

    python ingest.py --dry-run              # parse + report, no deps needed
    python ingest.py --src knowledge_base   # real ingest (needs chromadb)

Design rule this enforces: no chunk enters the store without `status` and
`source_type`. A chunk that cannot be classified is refused, not defaulted.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from dataclasses import dataclass, field, asdict
from pathlib import Path

import config

# --------------------------------------------------------------------------
# Controlled vocabularies. Unknown values are rejected, never coerced.
# --------------------------------------------------------------------------

STATUS = {"in_force", "repealed", "draft", "design_doc", "unknown"}
SOURCE_TYPE = {"primary", "secondary", "directory", "derived"}
SPHERE = {"national", "central", "state"}
VERIFICATION = {
    "verified_primary",
    "verified_secondary",
    "derived",
    "mixed",
    "UNVERIFIED",
    "UNVERIFIED_BLOCKER",
}

REQUIRED = ("doc_id", "status", "source_type", "citation_label")

EMBED_MODEL = "all-MiniLM-L6-v2"


def embedder():
    """
    all-MiniLM-L6-v2, however it is available on this machine.

    Prefers sentence-transformers. Falls back to the ONNX build chromadb ships
    with, so the pipeline still runs without a torch install.

    NOTE: the two are NOT score-equivalent, and the gap is worse than this
    docstring used to claim. It said the ONNX build truncates at 256 tokens.
    It truncates at 128: read straight off the model's own tokenizer.json in
    ~/.cache/chroma/onnx_models/all-MiniLM-L6-v2/onnx/, which carries
    `truncation: {max_length: 128}`. Measured 13 Sep 2026.

    The consequence, measured over the 31 indexed chunks:

        28 of 31 chunks (90%) are longer than the 128-token window
        median chunk 302 tokens, longest 1162 (9.1x the window)
        66% of the corpus is never embedded at all

    s76_death_formula: the chunk the flagship compensation question depends
    on: is 14% visible. s89_registration_of_agreements is 11% visible.

    That is why the scores collapse rather than merely shift: case 1 measured
    0.776 under sentence-transformers against 0.545 under ONNX, case 2 0.598
    against 0.216.

    It also breaks the safety gate's margin. Over 20 plain-language in-scope
    questions the lowest ONNX score was 0.2058 against a 0.20 floor, a margin
    of 0.006, where sentence-transformers has 0.048 (0.598 over 0.55). Nothing
    was refused at 0.20, but any corpus edit or unusual phrasing pushes a real
    question under the line.

    This is why the deployment runs sentence-transformers on a paid instance
    rather than the ONNX fallback on the free tier. **Do not re-run that
    experiment**: it is recorded here so nobody has to.

    So MIN_SIMILARITY is calibrated per embedder and does not transfer. Every
    score in the task write-ups was measured under sentence-transformers; do not
    compare a fallback number against them.
    """
    from chromadb.utils import embedding_functions

    try:
        return embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBED_MODEL
        )
    except Exception:
        return embedding_functions.DefaultEmbeddingFunction()


def using_fallback_embedder() -> bool:
    """
    Safe to call where chromadb is not installed: there is no retrieval to
    calibrate in that case, so it reports the primary embedder rather than
    making an import of this module fail.
    """
    try:
        return type(embedder()).__name__ != "SentenceTransformerEmbeddingFunction"
    except Exception:
        return False

# Signature of the broken ToUnicode CMap in the OSH&WC Rules gazette PDF.
# These are not typos: the source PDF maps glyphs to the wrong codepoints,
# so every Devanagari run in that file is unrecoverable garbage.
GARBLE_MARKERS = ("जन", "जध", "जल", "प्रकाजित", "संजिता", "अजधसूचना")
DEVANAGARI = re.compile(r"[ऀ-ॿ]")


# --------------------------------------------------------------------------


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    name: str
    text: str
    citation_label: str
    status: str
    source_type: str
    sphere: str = "national"
    jurisdiction: str = "india"
    verification: str = "UNVERIFIED"
    language: str = "en"
    in_force_from: str | None = None
    repealed_on: str | None = None
    retrieved_on: str | None = None
    recheck_by: str | None = None
    review_required: bool = False
    index: bool = True
    warnings: list[str] = field(default_factory=list)

    def metadata(self) -> dict:
        """Chroma accepts only str/int/float/bool/None in metadata."""
        d = asdict(self)
        d.pop("text")
        d.pop("warnings")
        return {k: v for k, v in d.items() if v is not None}


def parse_frontmatter(raw: str) -> tuple[dict, str]:
    """Minimal YAML frontmatter parser: flat key: value only, no deps."""
    if not raw.startswith("---"):
        return {}, raw
    end = raw.find("\n---", 3)
    if end == -1:
        return {}, raw
    block, body = raw[3:end], raw[end + 4 :]

    meta: dict = {}
    for line in block.splitlines():
        line = line.split(" #", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, _, val = line.partition(":")
        val = val.strip().strip('"').strip("'")
        key = key.strip()
        if val in ("true", "false"):
            meta[key] = val == "true"
        elif val in ("null", "~", ""):
            meta[key] = None
        else:
            meta[key] = val
    return meta, body


def strip_corrupt_devanagari(text: str) -> tuple[str, bool]:
    """
    Drop Devanagari runs from documents whose source encoding is broken.

    Only triggers when the garble signature is present, so clean Hindi in
    other files survives untouched.
    """
    if not any(m in text for m in GARBLE_MARKERS):
        return text, False
    cleaned = DEVANAGARI.sub("", text)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip(), True


def split_chunks(body: str) -> list[tuple[str, str]]:
    """Split on `## chunk: <name>` markers; fall back to one chunk per doc."""
    parts = re.split(r"^##\s+chunk:\s*(\S+)\s*$", body, flags=re.M)
    if len(parts) == 1:
        return [("body", body.strip())]
    out = []
    for i in range(1, len(parts), 2):
        name, text = parts[i], parts[i + 1].strip()
        if text:
            out.append((name, text))
    return out


def per_chunk_verification(text: str, default: str) -> str:
    """
    Resolve a chunk's verification level.

    Safety ordering matters here: a chunk may open with
    `verification: verified_primary` and still contain an
    UNVERIFIED_BLOCKER warning about one figure inside it
    (e.g. the s.76 chunk: formula verified, minimum amount not).
    The blocker must win, or the figure gate silently fails open.
    """
    if "UNVERIFIED_BLOCKER" in text:
        return "UNVERIFIED_BLOCKER"
    m = re.search(r"`?verification:\s*([A-Za-z_]+)`?", text)
    if m and m.group(1) in VERIFICATION:
        return m.group(1)
    return default


def load(src: Path) -> tuple[list[Chunk], list[str]]:
    chunks: list[Chunk] = []
    errors: list[str] = []

    for path in sorted(src.glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(raw)

        missing = [k for k in REQUIRED if not meta.get(k)]
        if missing:
            errors.append(f"{path.name}: missing required frontmatter {missing}")
            continue
        if meta["status"] not in STATUS:
            errors.append(f"{path.name}: bad status {meta['status']!r}")
            continue
        if meta["source_type"] not in SOURCE_TYPE:
            errors.append(f"{path.name}: bad source_type {meta['source_type']!r}")
            continue
        if meta.get("sphere", "national") not in SPHERE:
            errors.append(f"{path.name}: bad sphere {meta.get('sphere')!r}")
            continue

        if meta.get("index") is False:
            print(f"  skip (index:false) {path.name}")
            continue

        body, was_garbled = strip_corrupt_devanagari(body)

        for name, text in split_chunks(body):
            text = unicodedata.normalize("NFC", text)
            c = Chunk(
                chunk_id=f"{meta['doc_id']}::{name}",
                doc_id=meta["doc_id"],
                name=name,
                text=text,
                citation_label=meta["citation_label"],
                status=meta["status"],
                source_type=meta["source_type"],
                sphere=meta.get("sphere", "national"),
                jurisdiction=meta.get("jurisdiction", "india"),
                verification=per_chunk_verification(
                    text, meta.get("verification", "UNVERIFIED")
                ),
                language=meta.get("language", "en"),
                in_force_from=meta.get("in_force_from"),
                repealed_on=meta.get("repealed_on"),
                retrieved_on=meta.get("retrieved_on"),
                recheck_by=meta.get("recheck_by"),
                review_required=bool(meta.get("review_required", False)),
            )
            if was_garbled:
                c.warnings.append("devanagari_stripped")
            if c.status == "repealed":
                c.warnings.append("repealed_law")
            if c.verification == "UNVERIFIED_BLOCKER":
                c.warnings.append("blocker")
            chunks.append(c)

    return chunks, errors


# --------------------------------------------------------------------------
# Retrieval gate: the rules from docs/metadata-schema.md, in code.
# --------------------------------------------------------------------------


def apply_filters(
    hits: list[Chunk],
    *,
    historical: bool = False,
    confirmed_central_sphere: bool = False,
) -> tuple[list[Chunk], list[str]]:
    """Hard gates, applied BEFORE any similarity threshold."""
    triggered: list[str] = []
    kept = []
    for c in hits:
        if c.status == "repealed" and not historical:
            triggered.append(f"RULE1_repealed_dropped:{c.chunk_id}")
            continue
        if not c.index:
            triggered.append(f"RULE2_design_doc_dropped:{c.chunk_id}")
            continue
        if c.sphere == "central" and not confirmed_central_sphere:
            triggered.append(f"RULE5_central_sphere_dropped:{c.chunk_id}")
            continue
        kept.append(c)
    return kept, triggered


def answer_constraints(kept: list[Chunk]) -> dict:
    """What the LLM is allowed to do given the surviving chunks."""
    if not kept:
        return {"handoff": True, "reason": "no_chunks_after_filters"}
    return {
        "handoff": False,
        "may_cite_sections": all(c.source_type == "primary" for c in kept),
        "may_state_figures": not any(
            c.verification == "UNVERIFIED_BLOCKER" for c in kept
        ),
        "requires_review": any(c.review_required for c in kept),
        "citation_labels": sorted({c.citation_label for c in kept}),
    }


# --------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="knowledge_base", type=Path)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--manifest", default="chunk_manifest.json", type=Path)
    ap.add_argument("--collection", default="factory_bot_kb")
    args = ap.parse_args()

    if not args.src.is_dir():
        print(f"error: {args.src} is not a directory", file=sys.stderr)
        return 2

    chunks, errors = load(args.src)

    for e in errors:
        print(f"REFUSED  {e}", file=sys.stderr)

    print(f"\nparsed {len(chunks)} chunks from {args.src}")
    by_status: dict[str, int] = {}
    by_verif: dict[str, int] = {}
    for c in chunks:
        by_status[c.status] = by_status.get(c.status, 0) + 1
        by_verif[c.verification] = by_verif.get(c.verification, 0) + 1
    print("  by status:      ", dict(sorted(by_status.items())))
    print("  by verification:", dict(sorted(by_verif.items())))

    blockers = [c.chunk_id for c in chunks if c.verification == "UNVERIFIED_BLOCKER"]
    if blockers:
        print(f"\n  {len(blockers)} BLOCKER chunk(s), answers from these")
        print("  may describe structure but must not state figures:")
        for b in blockers:
            print(f"    - {b}")

    args.manifest.write_text(
        json.dumps(
            [{**c.metadata(), "warnings": c.warnings} for c in chunks],
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(f"\nwrote manifest -> {args.manifest}")

    if args.dry_run:
        print("dry run, nothing embedded")
        return 1 if errors else 0

    try:
        import chromadb
    except ImportError:
        print(
            "\nchromadb not installed. Install with:\n"
            "  pip install chromadb sentence-transformers --break-system-packages",
            file=sys.stderr,
        )
        return 2

    # Absolute, so ingest and query always agree on where the store lives no
    # matter which directory either was started from. Resolved by config, so
    # setting CHROMA_PATH moves the store for BOTH without them drifting apart.
    client = chromadb.PersistentClient(path=str(config.CHROMA_PATH))

    # Say which encoder built the index, and where.
    #
    # embedder() falls back silently when sentence-transformers is missing.
    # That is correct for a laptop without torch, and wrong for the server: a
    # failed torch install would build the whole index with the 128-token ONNX
    # model and raise nothing, leaving 66% of the corpus unembedded and the
    # safety gate calibrated against distances it will never see again. The
    # only symptom would be a bot that hands off to legal aid more than it
    # should. So the run states it, and an index built on the server is
    # checkable after the fact.
    fallback = using_fallback_embedder()
    print(f"store    -> {config.CHROMA_PATH}")
    print(f"embedder -> {type(embedder()).__name__}"
          f"{'  <-- FALLBACK' if fallback else ''}")
    if fallback:
        print(
            "\n!! Built with chroma's bundled ONNX model, not "
            "sentence-transformers.\n"
            "!! It truncates at 128 tokens: 28 of 31 chunks are longer, and\n"
            "!! 66% of the corpus will not be embedded. MIN_SIMILARITY is\n"
            "!! calibrated per embedder - see embedder() above.\n"
            "!! If this is the server, sentence-transformers failed to "
            "install.",
            file=sys.stderr,
        )

    # Rebuild rather than upsert. Upsert never deletes, so a chunk removed from
    # the corpus stays in the index and stays retrievable, and the chunks this
    # project removes are removed for safety reasons (the worked example with a
    # quotable rupee figure, the FAQ that omitted factory workers). The corpus
    # is the source of truth and 28 chunks re-embed in seconds, so the index is
    # discarded and rebuilt from it every time.
    try:
        client.delete_collection(args.collection)
    except Exception:
        pass
    coll = client.create_collection(
        args.collection, embedding_function=embedder()
    )
    coll.add(
        ids=[c.chunk_id for c in chunks],
        documents=[c.text for c in chunks],
        metadatas=[c.metadata() for c in chunks],
    )
    print(f"embedded {len(chunks)} chunks into '{args.collection}'")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
