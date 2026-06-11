"""B1 regression — production grader vs validated reference results.

PASS iff, on all five mainTB worked puzzles (HOA fixtures) AND the real
TempoBench sample instance:
  R1: grader keys() == Gate A oracle outputs (which equal the published answers);
  R2: prevent grading implemented from Def. valid (closest-removal semantics)
      agrees with Prop. pivotal's characterization: accepted singletons == pivot
      set, and the no-pivot verdict is accepted iff the pivot set is empty —
      i.e., the theorem is CHECKED against the definition, not assumed;
  R3: every published witness is accepted and every strict superset rejected,
      in its own mode."""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "GateA"))
from itertools import combinations
from hoa import HOA
from engine import Instance, full_report
from fixtures import PUZZLES
from a2_corp_compare import run_row
from grader import grade_prevent, grade_credit, grade_pin, keys, valid_cause, subset_minimal

def main():
    out, ok = [], True
    for p in PUZZLES:
        inst = Instance(HOA(p["hoa"]), p["inputs"], p["obs"], p["out"], p["k"])
        ref = full_report(inst); k = keys(inst)
        r1 = (k["pivots"] == ref["pivots"] and
              k["credit_original"] == ref["credit_original_minimal_causes"] and
              k["credit_modified"] == ref["credit_modified_minimal_causes"] and
              k["pin"] == ref["pin_determining_sets"])
        # R2: Def.-valid grading vs Prop. pivotal
        accepted_singletons = [c for c in inst.cells()
                               if grade_prevent(inst, [c])["correct"]]
        r2 = (sorted(accepted_singletons) == ref["pivots"] and
              grade_prevent(inst, [], no_pivot=True)["correct"] == ref["no_pivotal_cell"])
        # R3: witnesses accepted, supersets rejected (credit-original + pin)
        r3 = True
        for m in ref["credit_original_minimal_causes"]:
            r3 &= grade_credit(inst, list(m))["correct"]
            for extra in inst.cells():
                if extra not in m:
                    r3 &= not grade_credit(inst, list(m) + [extra])["correct"]
        for m in ref["pin_determining_sets"]:
            r3 &= grade_pin(inst, list(m))["correct"]
        ok &= r1 and r2 and r3
        out.append({"puzzle": p["name"], "R1_keys_equal_reference": r1,
                    "R2_defvalid_matches_prop_pivotal": r2,
                    "R3_witnesses_accepted_supersets_rejected": r3})
    # real TempoBench instance
    row = json.loads(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "..", "GateA", "external", "tb_embedded_sample.jsonl")).read())
    rr = run_row(row)
    tb_ok = rr["agreement_original"]["f1"] == 1.0
    ok &= tb_ok
    out.append({"puzzle": "TempoBench sample (real artifact)",
                "per_cell_agreement_f1": rr["agreement_original"]["f1"], "ok": tb_ok})
    print(json.dumps({"status": "PASS" if ok else "FAIL", "results": out}, indent=1))
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
