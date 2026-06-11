"""A3 — HP-variant divergence evidence + decision-record consistency check.
[TRACE_validation_plan Gate A3]

Computes, for every worked puzzle, the witness sets accepted under (a) the
original/updated variant (minimal actual causes, non-actual contingencies) and
(b) the modified-variant reading (minimal extinguishing flip sets), and verifies:
  T1: the two variants AGREE on non-overdetermined instances (P1, P2, P4);
  T2: they DIVERGE exactly on the overdetermined instances (P3, P5), with the
      modified variant returning the joint pair (mainTB 'which Halpern-Pearl':
      "under the modified definition Puzzle 3's cause would be the joint pair");
  T3: dual-acceptance (implementation spec sec. 4.2) accepts the union of both
      variants' witnesses and rejects all strict supersets (minimality shared).
Emits the machine half of A3_decision_record.md."""
import json, sys
from itertools import combinations
from hoa import HOA
from engine import Instance, minimal_actual_causes, minimal_flip_sets, satisfies_ac2, flip_kills
from fixtures import PUZZLES

def main():
    out, ok = [], True
    overdetermined = {"P3 overdetermination", "P5 delayed overdetermination"}
    for p in PUZZLES:
        inst = Instance(HOA(p["hoa"]), p["inputs"], p["obs"], p["out"], p["k"])
        orig = set(minimal_actual_causes(inst)); mod = set(minimal_flip_sets(inst))
        agree = orig == mod
        is_over = p["name"] in overdetermined
        t1t2 = (agree != is_over)  # agree iff not overdetermined
        # T3: enumerate every nonempty submission over window cells
        accepted = []
        cells = inst.cells()
        def is_min(S, pred, pool):
            if not pred(inst, S): return False
            for r in range(1, len(S)):
                for sub in combinations(S, r):
                    if pred(inst, sub): return False
            return True
        for size in range(1, len(cells) + 1):
            for S in combinations(cells, size):
                a = is_min(S, satisfies_ac2, orig)
                b = is_min(S, lambda i, s: flip_kills(i, s), mod)
                if a or b: accepted.append((tuple(sorted(S)), "orig" if a and not b else "mod" if b and not a else "both"))
        acc_sets = set(s for s, _ in accepted)
        want = orig | mod
        t3 = acc_sets == set(want)
        ok &= t1t2 and t3
        out.append({"puzzle": p["name"], "overdetermined": is_over,
                    "original_updated_witnesses": sorted(orig), "modified_witnesses": sorted(mod),
                    "variants_agree": agree, "T1T2_pattern_ok": t1t2,
                    "dual_acceptance_set": sorted(accepted), "T3_dual_equals_union_no_supersets": t3})
    print(json.dumps({"status": "PASS" if ok else "FAIL", "results": out}, indent=1, default=str))
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
