"""B2 — Prototype corpus + statistics (mainTB roadmap V4 prototype).

Generates random-Mealy instances across difficulty strata, certifies every key
with the production grader, applies the trivial-instance filter, and reports the
quantities mainTB asks for:
  - instances per stratum and discard rate;
  - frequency of the no-pivotal-cell verdict, SPLIT into overdetermined
    (actual causes exist) vs input-unconditional (none; discarded);
  - per-cell agreement of Credit and Pin (a divergence instance, if found, is
    the example mainTB says would justify Credit specifically);
  - original-vs-modified variant divergence rate (the class where Conjecture
    corp is predicted to fail);
  - audit re-check: every retained instance passes the F2/F3/F1-operational
    audit (defense in depth: F2/F3 hold by construction, the audit must agree).
PASS iff: >=100 retained instances, all retained pass the audit, and all
reported counts are internally consistent (cross-checked totals)."""
import json, random, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "GateA"))
from hoa import HOA
from engine import Instance
from a1_audit import audit_one
from grader import keys
from generator import sample_instance, classify, transition_count

STRATA = [(2, 1, 2), (2, 2, 2), (3, 2, 2), (3, 1, 4), (3, 2, 3), (4, 2, 3)]  # (states,|I|,k); window cells <= 8
CAP = None  # None = exhaustive over the full window (cells <= 8 in all strata), no censoring

def run_stratum(idx, seed=7, per_stratum=24):
    """One stratum per process call (sandbox 45s budget); checkpoint to results/."""
    rng = random.Random(seed + idx)
    st, ni, k = STRATA[idx]
    data = []
    for _ in range(per_stratum):
        text, inst = sample_instance(rng, st, ni, k)
        if inst is None: continue
        K = keys(inst, cap=CAP)
        verdict, cause_cells = classify(inst, K)
        aud = audit_one(text, inst.inputs)
        pin_cells = set(c for m in K["pin"] for c in m)
        data.append({"stratum": [st, ni, k], "verdict": verdict,
            "pivots": len(K["pivots"]),
            "no_piv": len(K["pivots"]) == 0,
            "has_causes": bool(K["credit_original"]),
            "n_min_causes": len(K["credit_original"]),
            "causal_cells": sorted(cause_cells), "pin_cells": sorted(pin_cells),
            "credit_pin_div": pin_cells != cause_cells,
            "variant_div": set(map(tuple, K["credit_original"])) != set(map(tuple, K["credit_modified"])),
            "audit_ok": aud["F1_operational"] and aud["F2_input_deterministic"] and aud["F3_input_total"],
            "transitions": transition_count(inst.h)})
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", f"b2_part{idx}.json")
    json.dump(data, open(out, "w"))
    print(f"stratum {idx} {STRATA[idx]}: {len(data)} instances -> {out}")

def aggregate():
    import glob
    rows = []
    for f in sorted(glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "b2_part*.json"))):
        rows += json.load(open(f))
    counts = {"generated": len(rows),
              "retain": sum(1 for r in rows if r["verdict"] == "retain"),
              "discard:input-unconditional": sum(1 for r in rows if r["verdict"] == "discard:input-unconditional"),
              "discard:same-column-single-literal": sum(1 for r in rows if r["verdict"] == "discard:same-column-single-literal")}
    nopiv_over = sum(1 for r in rows if r["no_piv"] and r["has_causes"])
    nopiv_uncond = sum(1 for r in rows if r["no_piv"] and not r["has_causes"])
    retained = [r for r in rows if r["verdict"] == "retain"]
    credit_pin_div = [{"stratum": r["stratum"], "credit_cells": r["causal_cells"],
                       "pin_cells": r["pin_cells"]} for r in retained if r["credit_pin_div"]]
    variant_div = sum(1 for r in retained if r["variant_div"])
    audit_fail = sum(1 for r in retained if not r["audit_ok"])
    consistent = (counts["generated"] == counts["retain"] +
                  counts["discard:input-unconditional"] + counts["discard:same-column-single-literal"])
    ok = counts["retain"] >= 100 and audit_fail == 0 and consistent
    out = {"status": "PASS" if ok else "FAIL", "seed": "7+stratum", "strata": STRATA,
           "counts": counts, "discard_rate": 1 - counts["retain"] / max(1, counts["generated"]),
           "no_pivotal_cell": {"overdetermined": nopiv_over, "input_unconditional_discarded": nopiv_uncond},
           "credit_vs_pin_per_cell_divergences": {"count": len(credit_pin_div),
                                                  "examples": credit_pin_div[:5]},
           "original_vs_modified_divergence_count": variant_div,
           "retained_audit_failures": audit_fail,
           "minimal_cause_size_cap": CAP,
           "totals_consistent": consistent,
           "retained_sample": retained[:8]}
    print(json.dumps(out, indent=1, default=str))
    return 0 if ok else 1

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] != "agg":
        run_stratum(int(sys.argv[1])); sys.exit(0)
    sys.exit(aggregate())
