"""Gold-12 input set: the canonical raw-input rows the build pipeline is
tested against — the SAME twelve instances the retired single-board build
shipped, now exercised end-to-end through the mode-explicit pipeline:

  P1..P5  the five mainTB worked puzzles (HOA fixtures);
  TB      the real TempoBench sample artifact (row passed through verbatim);
  G1..G6  generated instances, reproduced EXACTLY (seed 23, the same strata
          and the same sampling/skip loop as the retired builder), so the
          coverage obligation "every input used by the old build is used to
          test the new build" is discharged deterministically.

Each instance is serialized in the TempoBench raw schema consumed by
build_from_inputs.py: {"hoa": <text>, "trace": "lit&lit;...", "effects":
["X..X o"], "error": null}. Writing the file twice is byte-identical
(verified by verify_mode_assignment.py D-tests over these rows)."""
import json, random, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "GateA"))
from hoa import HOA, simulate
from engine import Instance, minimal_actual_causes
from fixtures import PUZZLES
from generator import sample_instance

HERE = os.path.dirname(os.path.abspath(__file__))
GOLD_PATH = os.path.join(HERE, "results", "gold12.jsonl")


def row_of(hoa_text, inst, name):
    """Serialize an Instance as a raw input row (spot-style trace: all APs per
    step, outputs from simulation, inputs from the observed grid)."""
    h = inst.h
    _, outs = simulate(h, inst.inputs, inst.obs)
    _, oidx = h.io_split(inst.inputs)
    onames = [h.aps[j] for j in oidx]
    steps = []
    for t in range(inst.k + 1):
        lits = []
        for j, nm in enumerate(onames): lits.append(nm if outs[t][j] else "!" + nm)
        for r, nm in enumerate(inst.inputs): lits.append(nm if inst.obs[r][t] else "!" + nm)
        steps.append("&".join(lits))
    return {"hoa": hoa_text, "trace": ";".join(steps),
            "effects": ["X" * inst.k + " " + inst.out if inst.k else inst.out],
            "name": name, "error": None}


def gold_rows(seed=23, n_generated=6):
    rows = []
    for p in PUZZLES:
        inst = Instance(HOA(p["hoa"]), p["inputs"], p["obs"], p["out"], p["k"])
        rows.append(row_of(p["hoa"], inst, p["name"].split(" ")[0]))
    # the real TempoBench artifact, passed through verbatim (plus a name tag)
    tb = json.loads(open(os.path.join(HERE, "..", "GateA", "external",
                                      "tb_embedded_sample.jsonl")).read())
    rows.append({"hoa": tb["hoa"], "trace": tb["trace"], "effects": tb["effects"],
                 "name": "TB", "error": None})
    # G1..G6: the retired builder's exact sampling loop (rng consumption and
    # skip conditions preserved verbatim so the instances reproduce).
    rng = random.Random(seed)
    strata = [(2, 1, 2), (2, 2, 2), (3, 2, 2), (3, 1, 3), (3, 2, 3), (4, 2, 3)]
    got = 0
    while got < n_generated and strata:
        st, ni, k2 = strata[got % len(strata)]
        text, inst = sample_instance(rng, st, ni, k2)
        if inst is None: continue
        if not minimal_actual_causes(inst): continue   # trivial filter (exhaustive)
        rows.append(row_of(text, inst, f"G{got+1}"))
        got += 1
    return rows


def write(path=GOLD_PATH):
    rows = gold_rows()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        for r in rows:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    return path, rows


if __name__ == "__main__":
    path, rows = write()
    print(f"wrote {path}: {len(rows)} rows ({', '.join(r['name'] for r in rows)})")
