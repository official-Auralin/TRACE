"""A2(i) — Oracle end-to-end check against the paper's published answers.
[TRACE_validation_plan Gate A2 foundational half; prerequisite for the CORP comparison]

For each of the five worked puzzles of mainTB (here encoded as machine-readable HOA
artifacts, not hand simulations), the oracle computes ALL FOUR causal objects and the
result must EXACTLY match the answers published in mainTB sec. 'Five worked puzzles'
(plus the modified-variant verdicts mainTB states in 'which Halpern-Pearl').

PASS iff 5 puzzles x {prevent, credit-original, credit-modified, pin} all match.
This certifies: HOA parser -> expansion -> simulation -> oracle as a faithful
implementation of the paper's definitions on its own gold examples."""
import json, sys
from hoa import HOA
from engine import Instance, full_report
from fixtures import PUZZLES

def main():
    results, ok = [], True
    for p in PUZZLES:
        inst = Instance(HOA(p["hoa"]), p["inputs"], p["obs"], p["out"], p["k"])
        got = full_report(inst)
        diffs = {}
        for key, want in p["expect"].items():
            g = got[key]
            if isinstance(want, list):
                gnorm = sorted([tuple(x) if isinstance(x, (list, tuple)) and x and isinstance(x[0], tuple)
                                else x for x in g])
                wnorm = sorted(want)
                if gnorm != wnorm: diffs[key] = {"want": wnorm, "got": gnorm}
            elif g != want: diffs[key] = {"want": want, "got": g}
        match = not diffs
        ok &= match
        results.append({"puzzle": p["name"], "k": p["k"], "inputs": p["inputs"],
                        "observed_run_inputs": p["obs"], "oracle_output": got,
                        "matches_paper": match, "diffs": diffs})
    out = {"status": "PASS" if ok else "FAIL", "n_puzzles": len(PUZZLES),
           "all_match_published_answers": ok, "results": results}
    print(json.dumps(out, indent=1, default=str))
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
