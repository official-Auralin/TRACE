"""A2(ii) — TempoBench gold-key vs TRACE oracle, per-cell comparison.
[TRACE_validation_plan Gate A2 empirical half; mainTB roadmap V2]

Schema (validated against the cloned tempobench repo, dataset.py + causality_sample.py):
  row = {hoa: <HOA text>, trace: "<l1>;<l2>;...;cycle{i}", effects: ["X..X o"],
         causality: {effect: {"t": ["lit", ...] | ["no constraints"]}}, error: null}
  - inputs = APs NOT listed in controllable-AP (controllable = system outputs);
  - k = number of 'X' in the effect; effect AP = last token;
  - trace steps are total conjunctions over AP; cycle{i} unrolled if the window needs it;
  - gold constraints are input literals at their actual values, per timestep.

For each row we compute the per-cell key under BOTH HP variants:
  ORIGINAL/UPDATED: union of minimal actual causes (mainTB Def. actual);
  MODIFIED:         union of minimal joint-flip (extinguishing) sets
                    (= Halpern-2015 discipline on exogenous cells; per
                    A2_definitional_note.md this is CORP's discipline).
and report per-cell precision/recall/F1 vs gold, plus an actuality-consistency
check (gold literal values must equal the observed trace values, as mainTB's
'cells at actual values' requires).

Status semantics:
  MEASURED(n=K)      — K rows compared; agreement metrics are the result.
  ROW-ERRORS         — some rows failed to parse/audit (listed; fails the gate).
  BLOCKED-EXTERNAL   — no rows found.
PASS condition for the HARNESS: every available row parses, passes the F2/F3
artifact pre-audit, and is actuality-consistent. The agreement RATE itself is a
reported scientific quantity (Conjecture corp is the thing under test, not the
harness)."""
import json, os, sys, glob, re
from hoa import HOA
from engine import Instance, minimal_actual_causes, minimal_flip_sets
from a1_audit import audit_one

def parse_trace(trace, aps, need_steps):
    parts = [p for p in trace.split(";") if p]
    cyc = None
    steps = []
    for p in parts:
        m = re.match(r'cycle\{(\d+)\}', p)
        if m: cyc = int(m.group(1)); break
        steps.append(p)
    while len(steps) < need_steps:
        if cyc is None: raise ValueError("trace shorter than window and no cycle")
        steps += steps[cyc:][:need_steps - len(steps)]
    vals = []
    for s in steps[:need_steps]:
        v = {}
        for lit in s.split("&"):
            lit = lit.strip()
            neg = lit.startswith("!")
            v[lit.lstrip("!")] = 0 if neg else 1
        for a in aps:
            if a not in v: raise ValueError(f"step '{s}' does not fix AP '{a}'")
        vals.append(v)
    return vals

def parse_gold(gold_for_effect, inputs, k):
    cells = set()
    for t_str, lits in gold_for_effect.items():
        t = int(t_str)
        if lits == ["no constraints"]: continue
        for entry in lits:
            for tok in re.split(r'\s+AND\s+|&', entry):
                tok = tok.strip()
                if not tok or tok.lower() == "no constraints": continue
                neg = tok.startswith("!")
                name = tok.lstrip("!")
                cells.add(((inputs.index(name), t), 0 if neg else 1))
    return cells

def scores(gold, ours):
    g, o = set(gold), set(ours)
    tp = len(g & o)
    p = tp / len(o) if o else (1.0 if not g else 0.0)
    r = tp / len(g) if g else 1.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return {"precision": p, "recall": r, "f1": f}

def run_row(row):
    h = HOA(row["hoa"])
    assert h.controllable is not None, "no controllable-AP: cannot derive I/O split"
    inputs = [a for i, a in enumerate(h.aps) if i not in h.controllable]
    effect = row["effects"][0]
    k = effect.count("X"); out = effect.split()[-1]
    pre = audit_one(row["hoa"], inputs)
    if not (pre["F2_input_deterministic"] and pre["F3_input_total"]):
        return {"error": "artifact fails F2/F3 pre-audit", "audit": pre}
    tvals = parse_trace(row["trace"], h.aps, k + 1)
    obs = [[tvals[t][a] for t in range(k + 1)] for a in inputs]
    inst = Instance(h, inputs, obs, out, k)
    orig = minimal_actual_causes(inst); mod = minimal_flip_sets(inst)
    u_orig = set((c, inst.obs[c[0]][c[1]]) for m in orig for c in m)
    u_mod = set((c, inst.obs[c[0]][c[1]]) for m in mod for c in m)
    gold = parse_gold(row["causality"][effect], inputs, k)
    actuality_ok = all(inst.obs[c[0][0]][c[0][1]] == c[1] for c in gold)
    return {"effect": effect, "k": k, "inputs": inputs,
            "observed_window_inputs": obs,
            "artifact_preaudit_F1F2F3": [pre["F1_operational"], True, True],
            "gold_cells": sorted(map(str, gold)),
            "ours_original_cells": sorted(map(str, u_orig)),
            "ours_modified_cells": sorted(map(str, u_mod)),
            "gold_actuality_consistent": actuality_ok,
            "agreement_original": scores(gold, u_orig),
            "agreement_modified": scores(gold, u_mod),
            "variants_diverge_here": u_orig != u_mod,
            "minimal_causes_original": sorted(map(str, orig)),
            "minimal_flip_sets_modified": sorted(map(str, mod))}

def main():
    ext = os.path.join(os.path.dirname(__file__), "external")
    rows = []
    for f in sorted(glob.glob(os.path.join(ext, "*.jsonl"))):
        for l in open(f):
            if l.strip():
                r = json.loads(l)
                if r.get("error") is None: rows.append((os.path.basename(f), r))
    if not rows:
        print(json.dumps({"status": "BLOCKED-EXTERNAL",
            "reason": "no TempoBench rows in external/",
            "acquisition": "https://huggingface.co/datasets/nikolausholzer/tempobench"}, indent=1))
        return 0
    out, errs = [], 0
    agg = {"original": [], "modified": []}
    for src, row in rows:
        try:
            r = run_row(row); r["source"] = src
            if "error" in r: errs += 1
            else:
                agg["original"].append(r["agreement_original"]["f1"])
                agg["modified"].append(r["agreement_modified"]["f1"])
                if not r["gold_actuality_consistent"]: errs += 1
        except Exception as e:
            r = {"source": src, "error": repr(e)}; errs += 1
        out.append(r)
    n = len(agg["original"])
    summary = {v: {"mean_f1": (sum(agg[v]) / n if n else None),
                   "perfect_agreement_rate": (sum(1 for x in agg[v] if x == 1.0) / n if n else None)}
               for v in agg}
    status = ("ROW-ERRORS" if errs else f"MEASURED(n={n})")
    print(json.dumps({"status": status, "rows_compared": n, "row_errors": errs,
        "per_variant_agreement_with_tempobench_gold": summary,
        "caveat": ("n is small; full datasets at huggingface.co/datasets/nikolausholzer/tempobench. "
                   "Conjecture-corp discrimination requires overdetermined rows, where the variants diverge."),
        "rows": out}, indent=1, default=str))
    return 1 if errs else 0

if __name__ == "__main__":
    sys.exit(main())
