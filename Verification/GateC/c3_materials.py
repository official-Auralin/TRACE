"""C3 materials — emit the agent-facing observation for every playable level.

For each level of the playable build: materials/<name>.observation.json holds
exactly what an agent receives (machine HOA, AP split, run over the window,
target, window, task, budgets) and NOTHING the human board does not also encode
(no key, no oracle). The parity audit (c1) is the proof of equivalence; this
script is the packaging."""
import json, sys, os, re
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "GateA"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "GateB"))
from hoa import HOA
from engine import Instance
from fixtures import PUZZLES
from a2_corp_compare import parse_trace

def emit(name, hoa_text, inst, outdir):
    run = []
    d, outs = __import__("hoa").simulate(inst.h, inst.inputs, inst.obs)
    _, oidx = inst.h.io_split(inst.inputs)
    onames = [inst.h.aps[j] for j in oidx]
    for t in range(inst.k + 1):
        row = {"t": t}
        for r, nm in enumerate(inst.inputs): row[nm] = inst.obs[r][t]
        for j, nm in enumerate(onames): row[nm] = outs[t][j]
        run.append(row)
    obs = {"machine": hoa_text, "aps": {"inputs": inst.inputs, "outputs": onames},
           "run": run, "target": {"output": inst.out, "step": inst.k},
           "window": [0, inst.k],
           "task": {"object": "credit", "variant": "witness", "hp_variant_policy": "either"},
           "budgets": {"probes": None, "attempts": 2}}
    open(os.path.join(outdir, f"{name}.observation.json"), "w").write(json.dumps(obs, indent=1))

def main():
    outdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "materials")
    n = 0
    for p in PUZZLES:
        inst = Instance(HOA(p["hoa"]), p["inputs"], p["obs"], p["out"], p["k"])
        emit(p["name"].split(" ")[0], p["hoa"], inst, outdir); n += 1
    row = json.loads(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "..", "GateA", "external", "tb_embedded_sample.jsonl")).read())
    h = HOA(row["hoa"]); inputs = [a for i, a in enumerate(h.aps) if i not in h.controllable]
    k = row["effects"][0].count("X"); o = row["effects"][0].split()[-1]
    tv = parse_trace(row["trace"], h.aps, k + 1)
    obs = [[tv[t][a] for t in range(k + 1)] for a in inputs]
    emit("TB", row["hoa"], Instance(h, inputs, obs, o, k), outdir); n += 1
    print(f"emitted {n} agent observations to materials/")

if __name__ == "__main__":
    main()
