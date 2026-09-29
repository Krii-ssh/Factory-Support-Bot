#!/usr/bin/env python3
"""
Case tracker. Two tables, per the original pipeline document.

    py -3.14 tracker.py             # every case, with a turn count
    py -3.14 tracker.py LDH-1001    # one case, with full provenance

The case ID is the part a family sees, but it is the smaller half of why this
exists. The larger half is `case_events`: the intent label, the route taken,
whether the validator refused, and the chunk_ids that produced the answer.
That is the record a legal partner grades in the Day-4 sign-off, and grading
sources is both faster and more meaningful than grading prose.

Two privacy rules are enforced here rather than left to the caller:

  * `note` carries PROVENANCE, never message content. Nobody needs a
    transcript of what a grieving family typed at two in the morning, and a
    log that holds one becomes a liability the moment it is copied anywhere.
  * `victim_name`, `factory_name` and `incident_date` exist in the schema and
    are deliberately never populated. They pair with document generation,
    which is not built. Extracting personal details with no consumer for them
    is collecting data because the column is there.

The WhatsApp number is stored because a reply cannot be sent without it.
"""

from __future__ import annotations

import json
import re
import sqlite3
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path

import config

# Resolved by config. Defaults to sitting next to the code; set CASES_DB_PATH
# to put it on a mounted disk, which is what keeps the case-ID counter, and
# therefore the reference number a family was given, alive across a restart.
DB_PATH = config.CASES_DB_PATH

# Every write goes through one lock.
#
# Found by test, not by reasoning: two DIFFERENT senders messaging at the same
# moment both read COUNT(*) as the same number, both built "LDH-1001", and the
# second INSERT died on the UNIQUE constraint - taking the whole background
# thread with it, so that family got no reply at all. A second thread died on
# "database is locked" writing an event.
#
# The per-sender lock in server.py cannot help here: the colliding writes come
# from different senders, which is exactly the case it deliberately allows to
# run in parallel. Writes are tiny and rare, so serialising all of them costs
# nothing measurable.
_write_lock = threading.RLock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS cases (
    case_id         TEXT PRIMARY KEY,
    whatsapp_number TEXT NOT NULL,
    victim_name     TEXT,
    factory_name    TEXT,
    incident_date   TEXT,
    created_at      TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS case_events (
    case_id    TEXT NOT NULL,
    stage      TEXT NOT NULL,
    status     TEXT NOT NULL,
    note       TEXT,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(case_id)
);
CREATE INDEX IF NOT EXISTS idx_cases_number ON cases(whatsapp_number);
CREATE INDEX IF NOT EXISTS idx_events_case  ON case_events(case_id);
"""

CASE_ID_RE = re.compile(r"\bLDH[-\s]?(\d{3,6})\b", re.I)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# --------------------------------------------------------------------------
# Connection
# --------------------------------------------------------------------------


def connect(path: Path = DB_PATH) -> sqlite3.Connection:
    """
    A fresh connection per call.

    check_same_thread is off because the server answers messages on background
    threads, and sqlite's default refuses a connection used from a thread other
    than the one that opened it. Each caller opening its own connection is the
    simpler half of that fix; this flag covers the case where one is passed
    across.
    """
    conn = sqlite3.connect(path, check_same_thread=False, timeout=10.0)
    conn.row_factory = sqlite3.Row
    # Wait for a competing writer instead of raising "database is locked"
    # immediately. _write_lock covers threads in this process; this covers a
    # second process, such as the CLI being run while the server is up.
    conn.execute("PRAGMA busy_timeout = 10000")
    conn.executescript(SCHEMA)
    return conn


# --------------------------------------------------------------------------
# Writing
# --------------------------------------------------------------------------


def get_or_create_case(conn, whatsapp_number: str) -> tuple[str, bool]:
    """
    Returns (case_id, created_now).

    One open case per number, which is wrong for a family with two claims and
    right for every case seen so far. Revisit when a second claim actually
    appears rather than guessing at the shape now.
    """
    with _write_lock:
        row = conn.execute(
            "SELECT case_id FROM cases WHERE whatsapp_number = ? "
            "ORDER BY created_at DESC LIMIT 1",
            (whatsapp_number,),
        ).fetchone()
        if row:
            return row["case_id"], False

        # Short enough to say down a phone line in Punjabi or Hindi, and to
        # write on the back of a hand. A UUID would be unusable for the people
        # who need it most.
        #
        # Retried rather than assumed unique: COUNT(*) is not a safe id source
        # if another process inserts between the count and the insert, and a
        # collision that escapes here kills the thread and the family's reply
        # with it.
        for _ in range(50):
            n = conn.execute("SELECT COUNT(*) AS c FROM cases").fetchone()["c"]
            case_id = f"LDH-{1001 + n}"
            try:
                conn.execute(
                    "INSERT INTO cases (case_id, whatsapp_number, created_at) "
                    "VALUES (?, ?, ?)",
                    (case_id, whatsapp_number, _now()),
                )
                conn.commit()
                return case_id, True
            except sqlite3.IntegrityError:
                continue
        raise RuntimeError("could not allocate a case id")


def log_event(conn, case_id: str, stage: str, status: str,
              note: dict | None = None) -> None:
    with _write_lock:
        conn.execute(
            "INSERT INTO case_events (case_id, stage, status, note, updated_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (case_id, stage, status,
             json.dumps(note, ensure_ascii=False) if note else None, _now()),
        )
        conn.commit()


def _intent_of(answer) -> str:
    """
    Pull the label out of the provenance rather than out of a second classifier
    call. resolve() records it as INTENT_<label>:<how>, so it is already there.
    """
    for rule in getattr(answer, "rules", []) or []:
        if rule.startswith("INTENT_"):
            return rule[len("INTENT_"):].split(":", 1)[0]
    return "unknown"


def _status_of(answer) -> str:
    route = (getattr(answer, "route", "") or "").lower()
    if "refused by validator" in route:
        return "refused_by_validator"
    if "hardcoded" in route:
        return "answered_fixed_text"
    if "handoff" in route:
        return "handoff"
    if "error" in route:
        return "error"
    return "answered"


def log_turn(conn, case_id: str, answer) -> None:
    """
    Log one pipeline turn from a query.Answer.

    Takes the Answer rather than loose arguments so that a field added to the
    provenance later cannot be silently dropped here.
    """
    note = {
        "route": getattr(answer, "route", ""),
        # Scores are stripped: "chunk_id (0.776)" -> "chunk_id". The score
        # belongs in the run log; what a reviewer needs is which law was used.
        "chunk_ids": [str(c).split(" (")[0]
                      for c in (getattr(answer, "chunks", []) or [])],
        "citation_labels": list(getattr(answer, "labels", []) or []),
        "rules": [r for r in (getattr(answer, "rules", []) or [])
                  if r.startswith(("RULE", "CHECK", "PREEMPT", "REVIEW"))],
    }
    log_event(conn, case_id, _intent_of(answer), _status_of(answer), note)


# --------------------------------------------------------------------------
# Reading
# --------------------------------------------------------------------------


def find_case_id(text: str) -> str | None:
    """Pull a case id out of a message, normalised to LDH-NNNN."""
    m = CASE_ID_RE.search(text or "")
    return f"LDH-{m.group(1)}" if m else None


def case_summary(conn, case_id: str) -> str | None:
    case = conn.execute(
        "SELECT * FROM cases WHERE case_id = ?", (case_id,)
    ).fetchone()
    if not case:
        return None
    events = conn.execute(
        "SELECT stage, status, updated_at FROM case_events "
        "WHERE case_id = ? ORDER BY updated_at",
        (case_id,),
    ).fetchall()
    lines = [f"Case {case['case_id']} - opened {case['created_at'][:10]}",
             f"{len(events)} message(s) logged."]
    if events:
        last = events[-1]
        lines.append(
            f"Last: {last['stage']} / {last['status']} on {last['updated_at'][:10]}"
        )
    return "\n".join(lines)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    conn = connect()

    if len(sys.argv) > 1:
        case_id = sys.argv[1].upper()
        summary = case_summary(conn, case_id)
        if not summary:
            print(f"no such case: {case_id}")
            return 1
        print(summary)
        for e in conn.execute(
            "SELECT * FROM case_events WHERE case_id = ? ORDER BY updated_at",
            (case_id,),
        ):
            print(f"\n  {e['updated_at']}  {e['stage']} / {e['status']}")
            if e["note"]:
                for k, v in json.loads(e["note"]).items():
                    print(f"      {k}: {v}")
        return 0

    cases = conn.execute("SELECT * FROM cases ORDER BY created_at").fetchall()
    print(f"{len(cases)} case(s)\n")
    for c in cases:
        n = conn.execute(
            "SELECT COUNT(*) AS c FROM case_events WHERE case_id = ?",
            (c["case_id"],),
        ).fetchone()["c"]
        print(f"  {c['case_id']}  {c['whatsapp_number']}  "
              f"{c['created_at'][:16]}  {n} event(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
