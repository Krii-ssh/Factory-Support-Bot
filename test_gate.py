#!/usr/bin/env python3
"""
Tests for the retrieval gate. Run: python3 test_gate.py

These test the failure modes found in the source audit, not happy paths.
"""

from ingest import Chunk, apply_filters, answer_constraints

FAILS = 0


def check(name, cond):
    global FAILS
    print(("  PASS  " if cond else "  FAIL  ") + name)
    if not cond:
        FAILS += 1


def mk(cid, **kw):
    base = dict(
        chunk_id=cid, doc_id="d", name=cid, text="",
        citation_label="X", status="in_force", source_type="primary",
    )
    base.update(kw)
    return Chunk(**base)


print("\nRULE 1: repealed law must not become operative advice")
# The exact failure from the audit: Factories Act scores high on employer duty.
factories = mk("factories::s88", status="repealed")
kept, trig = apply_filters([factories])
check("repealed chunk dropped", kept == [])
check("drop is logged", any("RULE1" in t for t in trig))
check("sole repealed match -> handoff", answer_constraints(kept)["handoff"])

print("\n  ...but a pre-commencement incident may still use it")
kept, _ = apply_filters([factories], historical=True)
check("historical query keeps it", len(kept) == 1)

print("\nRULE 3: secondary sources must not support a section citation")
# The exact failure from the audit: the FIR blog post citing s.154(3) CrPC.
blog = mk("fir_blog::sp", source_type="secondary")
c = answer_constraints(apply_filters([blog])[0])
check("citation suppressed", c["may_cite_sections"] is False)
primary = mk("bnss::173_4")
c = answer_constraints(apply_filters([primary])[0])
check("primary source may cite", c["may_cite_sections"] is True)

print("\nRULE 4: blocker chunks must not produce a rupee figure")
blocked = mk("ss_code::sixth_schedule", verification="UNVERIFIED_BLOCKER")
c = answer_constraints(apply_filters([blocked])[0])
check("figures suppressed", c["may_state_figures"] is False)
check("structure still answerable", c["handoff"] is False)

print("\n  mixed retrieval: one blocker poisons the figure gate")
c = answer_constraints(apply_filters([primary, blocked])[0])
check("one blocker suppresses figures", c["may_state_figures"] is False)

print("\nRULE 5: Central Rules must not be quoted at a Ludhiana factory")
central = mk("oshwc_rules::r7", sphere="central")
kept, trig = apply_filters([central])
check("central-sphere dropped by default", kept == [])
check("drop is logged", any("RULE5" in t for t in trig))
kept, _ = apply_filters([central], confirmed_central_sphere=True)
check("kept when sphere confirmed", len(kept) == 1)

print("\nreview_required propagates")
rr = mk("x::y", review_required=True)
check("flagged", answer_constraints(apply_filters([rr])[0])["requires_review"])

print(f"\n{'ALL PASS' if not FAILS else str(FAILS) + ' FAILURE(S)'}\n")
raise SystemExit(1 if FAILS else 0)
