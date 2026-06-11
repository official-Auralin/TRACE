"""A1 — Artifact audit (F1)-(F3)  [TRACE_validation_plan Gate A1; mainTB roadmap V1]

Checks, per HOA artifact:
  F2 (input-determinism): for every reachable (state, input valuation), at most ONE
      (output valuation, successor) pair is consistent with the transition labels.
  F3 (input-totality):    ... at least ONE such pair.
  F1 (implementation, operational necessary conditions):
      h1: an input/output partition is declared (controllable-AP) or supplied;
      h2: output-functionality (== F2's uniqueness of the output completion);
      h3: acceptance is trivial OR ignoring it does not change behavior under the
          run-defined reading (we report acceptance presence; the run-defined reading
          is the construction's own choice, mainTB Def. hoa).
      F1-operational = h1 AND h2 AND F3. NOTE: this is NECESSARY, not sufficient —
      a full F1 verdict additionally requires re-synthesis cross-checks against the
      TLSF source (manual step, recorded as out-of-sandbox).

Self-validation: the audit runs over labelled positive AND negative controls
(fixtures.AUDIT_FIXTURES) and FAILS ITSELF if any fixture is misclassified.
External corpus: every *.hoa under external/ (with a manifest declaring inputs)
is audited and rates reported; absence of artifacts is recorded as BLOCKED-EXTERNAL.
"""
import json, os, sys
from itertools import product
from hoa import HOA, expand
from fixtures import AUDIT_FIXTURES

def audit_one(text, inputs):
    h = HOA(text)
    table, iidx, oidx = expand(h, inputs)
    f2_viol, f3_viol = [], []
    for (s, iv), opts in table.items():
        if len(opts) > 1: f2_viol.append((s, iv, len(opts)))
        if len(opts) == 0: f3_viol.append((s, iv))
    f2, f3 = len(f2_viol) == 0, len(f3_viol) == 0
    h1 = h.controllable is not None
    h3_acceptance_present = h.acceptance_sets > 0
    f1 = h1 and f2 and f3
    return {
        "states": h.n_states, "aps": h.aps, "inputs": inputs,
        "F2_input_deterministic": f2, "F2_violations": f2_viol[:5],
        "F3_input_total": f3, "F3_violations": f3_viol[:5],
        "F1_h1_io_partition_declared": h1,
        "F1_h3_nontrivial_acceptance_present": h3_acceptance_present,
        "F1_operational": f1,
        "note": "F1_operational is a NECESSARY condition; sufficiency requires re-synthesis cross-check (manual)."
    }

def main():
    res = {"self_validation": [], "external": [], "status": None}
    ok = True
    for fx in AUDIT_FIXTURES:
        r = audit_one(fx["hoa"], fx["inputs"])
        got = (r["F1_operational"], r["F2_input_deterministic"], r["F3_input_total"])
        want = (fx["expect_f1"], fx["expect_f2"], fx["expect_f3"])
        match = got == want
        ok &= match
        res["self_validation"].append({"fixture": fx["name"], "expected_F1F2F3": want,
                                       "observed_F1F2F3": got, "classified_correctly": match,
                                       "detail": r})
    res["self_validation_pass"] = ok

    ext_dir = os.path.join(os.path.dirname(__file__), "external")
    manifest = os.path.join(ext_dir, "manifest.json")
    hoas = [f for f in os.listdir(ext_dir) if f.endswith(".hoa")] if os.path.isdir(ext_dir) else []
    if hoas and os.path.exists(manifest):
        man = json.load(open(manifest))
        rates = {"F1": 0, "F2": 0, "F3": 0}
        for f in hoas:
            r = audit_one(open(os.path.join(ext_dir, f)).read(), man[f]["inputs"])
            res["external"].append({"file": f, **r})
            for key, field in [("F1", "F1_operational"), ("F2", "F2_input_deterministic"), ("F3", "F3_input_total")]:
                rates[key] += int(r[field])
        res["external_rates"] = {k: v / len(hoas) for k, v in rates.items()}
        res["status"] = "PASS" if ok else "FAIL"
    else:
        res["status"] = ("PASS-SELFVALIDATED, BLOCKED-EXTERNAL" if ok else "FAIL")
        res["external_note"] = ("No TempoBench artifacts present. Acquire from "
            "https://huggingface.co/datasets/nikolausholzer/tempobench or "
            "https://github.com/nik-hz/tempobench (src/tempobench/data/*.jsonl); place .hoa "
            "files + manifest.json ({file:{inputs:[...]}}) in external/ and re-run. "
            "Network fetch from this sandbox timed out (recorded attempt, 2026-06-10).")
    print(json.dumps(res, indent=1, default=str))
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
