"""A4 — Mealy/Moore window reconciliation.  [TRACE_validation_plan Gate A4]

Question: are the human-game's TESTABLE cells identical to the grader's CANDIDATE
cells {0..k} x I?  The demo's Moore-style board renders only cells that route the
state path (t < k); the spec's window includes t = k, and mainTB Puzzle 4 has
same-column causes.

Tests, per worked puzzle:
  D1: detect same-step (t=k) dependence: does ANY context make a (i,k) flip change
      the effect? (exhaustive over window contexts)
  D2: Moore-safe classification: instance is Moore-safe iff no (i,k) cell is
      EVER effect-relevant; P4 must be flagged NOT Moore-safe, P1/P2/P3/P5 safe.
  D3: key-coverage: every cell of every minimal cause (both variants) lies in the
      testable set of (a) Mealy rendering (all of {0..k} x I) — must ALWAYS hold;
      (b) Moore rendering ({0..k-1} x I) — must hold exactly for Moore-safe instances.
Verdict emitted: the production rule (Mealy edge-rendering, or Moore + filter)."""
import json, sys
from itertools import product
from hoa import HOA
from engine import Instance, minimal_actual_causes, minimal_flip_sets
from fixtures import PUZZLES

def same_step_relevant(inst):
    rel = []
    cells = inst.cells()
    kcells = [c for c in cells if c[1] == inst.k]
    others = [c for c in cells if c[1] != inst.k]
    for c in kcells:
        found = False
        for vals in product((0, 1), repeat=len(others)):
            ctx = {o: v for o, v in zip(others, vals)}
            a = dict(ctx); a[c] = 0
            b = dict(ctx); b[c] = 1
            fa, fb = inst.fires(inst.with_cells(a)), inst.fires(inst.with_cells(b))
            if fa is not None and fb is not None and fa != fb:
                found = True; break
        if found: rel.append(c)
    return rel

def main():
    out, ok = [], True
    expect_unsafe = {"P4 guard (request/cancel)"}
    for p in PUZZLES:
        inst = Instance(HOA(p["hoa"]), p["inputs"], p["obs"], p["out"], p["k"])
        rel = same_step_relevant(inst)
        moore_safe = len(rel) == 0
        d2 = moore_safe == (p["name"] not in expect_unsafe)
        causes = set(minimal_actual_causes(inst)) | set(minimal_flip_sets(inst))
        cause_cells = set(c for m in causes for c in m)
        mealy_testable = set(inst.cells())
        moore_testable = set(c for c in inst.cells() if c[1] < inst.k)
        d3a = cause_cells <= mealy_testable
        d3b = (cause_cells <= moore_testable) == moore_safe
        ok &= d2 and d3a and d3b
        out.append({"puzzle": p["name"], "k": p["k"],
                    "same_step_relevant_cells": sorted(rel), "moore_safe": moore_safe,
                    "D2_classification_ok": d2,
                    "cause_cells": sorted(cause_cells),
                    "D3a_mealy_covers_all_causes": d3a,
                    "D3b_moore_coverage_iff_safe": d3b})
    verdict = ("PRODUCTION RULE: adopt Mealy edge-rendering (option a) — it covers every "
               "cause cell on all five gold instances including the same-column guard; OR "
               "restrict corpora to Moore-safe instances (option b), which excludes the "
               "P4 class entirely (stronger than the trivial-instance filter, which only "
               "drops single-literal same-column causes).")
    print(json.dumps({"status": "PASS" if ok else "FAIL", "results": out,
                      "verdict": verdict}, indent=1, default=str))
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
