#!/usr/bin/env python3
"""
Tests for the routing layer. Run: python test_classify.py

Spec: knowledge_base/08_intent_classification.md, "Verification before this
ships": the thirteen boundary cases plus the eight Day-1 cases, reported as a
confusion matrix. Two rows must be perfect:

    no settlement_pressure input classified as anything else   (zero tolerance)
    no out_of_scope input classified as a real label           (the case-7 bug)

Without GROQ_API_KEY the classifier layer cannot run, so the LLM-decided cases
are reported as SKIP rather than silently passing. The keyword layer is
deterministic and always runs: which is the point of having it.
"""

import contextlib
import io
import os

import classify
from classify import (
    BODY, CASE_STATUS, DEATH, FIR, OUT_OF_SCOPE, SETTLEMENT,
    classify as route_of,
    settlement_keyword_hit,
)

HAVE_KEY = bool(os.environ.get("GROQ_API_KEY"))

# (question, expected label, note). The thirteen from the spec table, then the
# eight Day-1 cases, then the misroutes worth guarding against by name.
CASES = [
    ("the owner is offering 2 lakh, is that enough?", SETTLEMENT,
     "sounds like compensation; they are mid-decision"),
    ("we already signed the paper", SETTLEMENT, "past tense path"),
    ("they gave us money for the funeral, should we take it?", SETTLEMENT,
     "real entitlement, but the standard waiver wrapper"),
    ("they are saying take the body and go home", BODY,
     "reads as logistics, is hours-critical"),
    ("when will we get the post-mortem report?", BODY, "follow-up, same label"),
    ("police wrote the FIR but under a light section", FIR, "not a refusal"),
    ("the police are refusing to write the FIR", FIR, "day-1 case 3"),
    ("how much are we owed?", DEATH, "no pressure signal"),
    ("he worked through a thekedar", DEATH, "employment status feeds s.85"),
    ("what does the Factories Act say?", DEATH, "RULE 1 handles the repeal"),
    ("my husband died in a factory accident", DEATH, "the flagship"),
    ("what is the weather in Ludhiana", OUT_OF_SCOPE, "the day-1 failure"),
    ("how do I get a ration card", OUT_OF_SCOPE, "real need, wrong service"),
    ("my husband is missing since the fire", OUT_OF_SCOPE,
     "no death confirmed, do not improvise"),

    ("my husband died in a factory accident, what are we owed?", DEATH,
     "day-1 case 1"),
    ("how much money will we get exactly?", DEATH, "day-1 case 2"),
    ("they took his body away, what should we do?", BODY, "day-1 case 4"),
    ("the owner is offering us 2 lakh to sign a paper", SETTLEMENT,
     "day-1 case 5"),
    ("he worked through a thekedar, not directly", DEATH, "day-1 case 6"),
    ("what does the Factories Act say the factory must do", DEATH,
     "day-1 case 8"),

    ("what is happening with my case", CASE_STATUS, "stub -> handoff"),
    ("kitna muavza milega", DEATH,
     "bare 'muavza' must NOT fire the settlement keyword"),
]


def routing_checks() -> list[str]:
    """
    The point of the whole routing layer: an out-of-scope question must not
    reach retrieval or the answer model. Before it existed, the weather question
    was drafted and paid for.

    Stubs the classifier so these run without a key, and stubs retrieval so a
    call to it is a loud failure rather than a missing dependency.
    """
    import query

    bad: list[str] = []
    real_call, real_retrieve = classify._call_classifier, query.retrieve

    def exploded(*_a, **_kw):
        raise AssertionError("retrieval was called")

    for label, should_retrieve in (
        (OUT_OF_SCOPE, False),
        (CASE_STATUS, False),
        (SETTLEMENT, False),
        (DEATH, True),
    ):
        classify._call_classifier = lambda _q, _l=label: _l
        query.retrieve = exploded
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                query.answer_question("probe")
            reached = False
        except AssertionError:
            reached = True
        except Exception as e:
            bad.append(f"{label}: unexpected {type(e).__name__}: {e}")
            continue
        finally:
            classify._call_classifier, query.retrieve = real_call, real_retrieve

        if reached != should_retrieve:
            verb = "reached retrieval" if reached else "did not reach retrieval"
            bad.append(f"{label}: {verb}, expected the opposite")
    return bad


def main() -> int:
    print(f"\nclassifier: {'live' if HAVE_KEY else 'NO KEY, LLM cases skipped'}")

    matrix: dict[tuple[str, str], int] = {}
    fails, skips = [], []

    print("\n" + "-" * 74)
    for question, expected, note in CASES:
        hit = settlement_keyword_hit(question)

        if not hit and not HAVE_KEY:
            # The keyword layer declined and the classifier cannot be reached.
            # If the case expected settlement_pressure, that is a real failure
            # of the offline layer and must not be hidden behind the skip.
            if expected == SETTLEMENT:
                fails.append((question, expected, "no keyword hit", note))
                mark = "FAIL"
            else:
                skips.append(question)
                mark = "skip"
            print(f"  {mark:5} {expected:19} {question[:44]}")
            continue

        got, route, how = route_of(question)
        matrix[(expected, got)] = matrix.get((expected, got), 0) + 1
        ok = got == expected
        if not ok:
            fails.append((question, expected, got, note))
        print(f"  {'PASS' if ok else 'FAIL':5} {expected:19} {question[:44]}")
        if not ok:
            print(f"        got {got} via {how}: {note}")

    print("-" * 74)

    print("\nzero-tolerance rows")
    leaked = [f for f in fails if f[1] == SETTLEMENT]
    stretched = [f for f in fails if f[1] == OUT_OF_SCOPE]
    print(f"  settlement_pressure misrouted : {len(leaked)}  (must be 0)")
    print(f"  out_of_scope stretched        : {len(stretched)}  (must be 0)")

    if matrix:
        print("\nconfusion matrix (expected -> got)")
        for (exp, got), n in sorted(matrix.items()):
            flag = "" if exp == got else "   <-- MISROUTE"
            print(f"  {exp:19} -> {got:19} {n}{flag}")

    print("\nrouting: out_of_scope must never reach retrieval (day-1 case 7)")
    route_fails = routing_checks()
    for f in route_fails:
        print(f"  FAIL  {f}")
    if not route_fails:
        print("  PASS  all four routes behave")
    fails += [(f, "", "", "routing") for f in route_fails]

    if skips:
        print(f"\n{len(skips)} case(s) skipped, so set GROQ_API_KEY to run them")

    print(f"\n{'ALL PASS' if not fails else str(len(fails)) + ' FAILURE(S)'}\n")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
