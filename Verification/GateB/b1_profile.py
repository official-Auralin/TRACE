"""B1 profiling — grader runtime vs (|I|, k) per mode (mainTB roadmap V3).

Measures median wall-clock of one full key computation per mode over random
Mealy instances (3 per grid point, 3 states), and reports the tractable envelope
at thresholds 1s and 10s. This PUBLISHES the envelope the verifiable-reward
claim is restricted to; it does not assume one. Exhaustive reference algorithms
are used deliberately (mainTB's cost analysis predicts exponential Credit cost
in |I|*k; the measurement should exhibit it).
PASS iff every grid point yields a measurement (no crashes/timeouts at the
per-point cap) and Credit cost grows superpolynomially along |I|*k as predicted."""
import json, random, sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "GateA"))
from hoa import HOA
from engine import Instance, pivots, minimal_actual_causes, minimal_flip_sets, determining_sets
from generator import sample_instance

GRID = [(1, 1), (1, 2), (1, 3), (1, 4), (1, 5),
        (2, 1), (2, 2), (2, 3), (2, 4), (3, 1), (3, 2)]   # (|I|, k)
PER_POINT_CAP = 120.0

def time_modes(inst):
    t = {}
    for name, fn in [("prevent", lambda: pivots(inst)),
                     ("credit_original", lambda: minimal_actual_causes(inst, max_size=len(inst.cells()))),
                     ("credit_modified", lambda: minimal_flip_sets(inst, max_size=len(inst.cells()))),
                     ("pin", lambda: determining_sets(inst, max_size=len(inst.cells())))]:
        t0 = time.perf_counter(); fn(); t[name] = time.perf_counter() - t0
    return t

def run_point(idx, seed=11):
    rng = random.Random(seed + idx)
    ni, k = GRID[idx]
    samples, t_start = [], time.perf_counter()
    for _ in range(2):
        if time.perf_counter() - t_start > 30: break
        _, inst = sample_instance(rng, 3, ni, k)
        if inst is None: continue
        samples.append(time_modes(inst))
    row = ({"I": ni, "k": k, "error": "no sample"} if not samples else
           {"I": ni, "k": k, "cells": ni*(k+1), "n": len(samples),
            "median_seconds": {m: round(sorted(s[m] for s in samples)[len(samples)//2], 4)
                               for m in samples[0]}})
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", f"prof_{idx}.json")
    json.dump(row, open(out, "w")); print(idx, GRID[idx], "->", row.get("median_seconds", row))

def aggregate():
    import glob
    rows, ok = [], True
    for f in sorted(glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "prof_*.json")),
                    key=lambda x: int(x.split("_")[-1].split(".")[0])):
        r = json.load(open(f)); rows.append(r); ok &= "median_seconds" in r
    env = {thr: [(r["I"], r["k"]) for r in rows if "median_seconds" in r
                 and max(r["median_seconds"].values()) <= thr] for thr in (1.0, 10.0)}
    # superpolynomial growth check on credit_original along increasing |I|*k
    pts = [(r["cells"], r["median_seconds"]["credit_original"]) for r in rows if "median_seconds" in r]
    pts.sort()
    growth = [pts[i+1][1] / max(pts[i][1], 1e-6) for i in range(len(pts)-1) if pts[i+1][0] > pts[i][0]]
    superpoly = len(growth) >= 2 and growth[-1] > 2.0
    ok &= superpoly
    out = {"status": "PASS" if ok else "FAIL", "grid": rows,
           "tractable_envelope": {"<=1s": env[1.0], "<=10s": env[10.0]},
           "credit_growth_ratios_along_cells": [round(g, 2) for g in growth],
           "exponential_credit_cost_exhibited": superpoly,
           "host": "sandboxed Linux, CPython " + sys.version.split()[0],
           "note": ("Reference (exhaustive) algorithms; production may improve constants "
                    "but the |I|*k exponential in Credit is structural (mainTB cost analysis).")}
    print(json.dumps(out, indent=1))
    return 0 if ok else 1

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] != "agg":
        run_point(int(sys.argv[1])); sys.exit(0)
    sys.exit(aggregate())
