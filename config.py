#!/usr/bin/env python3
"""
One place that loads .env, imported by everything that needs a credential.

It used to live in whatsapp.py, which meant the classifier tests only saw a key
if one happened to be exported in the shell, so a machine configured entirely
through .env skipped eighteen of the twenty-two routing cases and reported
success.

It also resolves the two writable paths, the vector store and the case
database: because on a hosted instance they must live on a mounted disk
rather than next to the code, and having two modules each guess at that is how
they end up disagreeing.
"""

from __future__ import annotations

import os
from pathlib import Path

ENV_FILE = Path(__file__).parent / ".env"
_loaded = False


def load_env(path: Path = ENV_FILE, *, force: bool = False) -> None:
    """
    Read .env into os.environ, once per process.

    A value already in the environment wins, which is the usual convention and
    the reason a stale `setx GROQ_API_KEY` silently beat a working key in .env
    and returned 401 from some shells and not others. If that happens again,
    delete the environment variable rather than reversing this precedence, 
    the alternative hides genuine deployment config.

    utf-8-sig because Notepad on Windows writes a BOM, which would otherwise end
    up inside the first key name and make it unreadable.
    """
    global _loaded
    if _loaded and not force:
        return
    _loaded = True
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip("'\"")
        # An empty environment variable carries no information, so it does not
        # get to shadow a real value in .env, otherwise `GROQ_API_KEY=` in a
        # shell silently disables the key without ever saying so.
        if key and value and not os.environ.get(key):
            os.environ[key] = value


def key_source(name: str) -> str:
    """Where a value came from. Used by /health so a mismatch is visible."""
    if name not in os.environ:
        return "missing"
    if not ENV_FILE.exists():
        return "environment"
    for line in ENV_FILE.read_text(encoding="utf-8-sig").splitlines():
        k, _, v = line.strip().partition("=")
        if k.strip() == name and v.strip().strip("'\""):
            return "environment (overriding .env)" if os.environ[name] != v.strip().strip("'\"") else ".env"
    return "environment"


# --------------------------------------------------------------------------
# Writable paths
# --------------------------------------------------------------------------
#
# Both default to sitting next to the code, which is how every local run and
# every recorded measurement to date worked: so a developer who sets nothing
# sees no change at all.
#
# On Render they are pointed at a mounted disk instead. The free tier has no
# disk, which would have meant the index rebuilding on every wake and the case
# counter restarting, so two different families could be handed the same
# reference number. On the Standard instance the disk is mounted at /var/data
# and both of these move onto it:
#
#     CHROMA_PATH=/var/data/chroma
#     CASES_DB_PATH=/var/data/cases.db
#
# The vector store in particular must NOT be rebuilt on each deploy: it is
# built once, from the shell, by the same embedder that will query it. Index
# and query embedder disagreeing is silent and produces wrong distances rather
# than an error.


def _resolved(env_name: str, default_name: str) -> Path:
    load_env()
    raw = (os.environ.get(env_name) or "").strip()
    return Path(raw) if raw else Path(__file__).parent / default_name


CHROMA_PATH = _resolved("CHROMA_PATH", "chroma")
CASES_DB_PATH = _resolved("CASES_DB_PATH", "cases.db")
