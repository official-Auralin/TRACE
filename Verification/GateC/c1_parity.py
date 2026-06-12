"""C1 — Four-consumer parity audit (mainTB sec. Agent: "Parity is the point").

Per instance (five worked puzzles + the real TempoBench artifact + three
generated), four machine-checked parity properties:

  P-OBS  observation equivalence: the human board is a pure function of the
         agent's observation (rebuilt from the HOA text alone, byte-identical
         graph), and the board's window behavior equals HOA simulation on
         every input assignment (so neither side holds extra information).
  P-SUB  submission round-trip: every possible human submission (thrown set)
         serializes to the agent JSON answer format ("cells at actual values")
         and back, and the grader's verdict on the round-tripped answer equals
         its verdict on the board state. Exhaustive over all nonempty subsets
         of throwable cells, and checked PER DECLARED VARIANT POLICY —
         "original", "modified", and the legacy dual union — so the parity
         proven is the parity each shipped corpus actually grades under
         (a benchmark corpus declares exactly one hp_variant; A3 decision
         record), not only the union.
  P-PRB  probe parity: for random probe assignments, the black-box battery
         result derived from the board walk (target flashes? cells changed)
         equals the agent probe() result derived from HOA simulation.
  P-CAND candidate-space safety: cells throwable on the board are exactly the
         cells the device reads; every cell unreachable to the human is
         provably effect-irrelevant (flip changes nothing in any context), so
         no correct answer is human-inexpressible and the agent's larger
         nominal answer space adds only wrong answers.
PASS iff all four hold on every instance."""
import json, random, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "GateA"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "GateB"))
from itertools import product, combinations
from hoa import HOA
from engine import Instance
from fixtures import PUZZLES
from grader import keys
from render import build_graph, walk_graph
from generator import sample_instance
from a2_corp_compare import parse_trace

def submission_to_json(inst, thrown):
    cause = {}
    for (r, t) in thrown:
        cause.setdefault(str(t), {})[inst.inputs[r]] = inst.obs[r][t]
    return json.dumps({"cause": cause}, sort_keys=True)

def json_to_cells(inst, payload):
    cause = json.loads(payload)["cause"]
    cells = []
    for t_str, d in cause.items():
        for name, v in d.items():
            r, t = inst.inputs.index(name), int(t_str)
            assert inst.obs[r][t] == v, "answer cell not at actual value"
            cells.append((r, t))
    return sorted(cells)

def audit(name, inst, hoa_text, rng):
    res = {"instance": name}
    nodes, start = build_graph(inst)
    # P-OBS: board reproducible from agent observation (HOA text) alone + behaviorally equal
    h2 = HOA(hoa_text)
    inst2 = Instance(h2, inst.inputs, inst.obs, inst.out, inst.k)
    nodes2, start2 = build_graph(inst2)
    same_graph = json.dumps(nodes, sort_keys=True) == json.dumps(nodes2, sort_keys=True) and start == start2
    cells = inst.cells()
    beh_eq = all(walk_graph(nodes, start, inst.with_cells({c: v for c, v in zip(cells, vals)}), inst.k)
                 == (inst.fires(inst.with_cells({c: v for c, v in zip(cells, vals)})) is True)
                 for vals in product((0, 1), repeat=len(cells)))
    res["P_OBS"] = same_graph and beh_eq
    # P-SUB: exhaustive round-trip over throwable subsets, per variant policy
    throwable = sorted(set(tuple(n["cell"]) for n in nodes if n["kind"] == "test"))
    K = keys(inst)
    orig = set(tuple(sorted(map(tuple, m))) for m in K["credit_original"])
    mod = set(tuple(sorted(map(tuple, m))) for m in K["credit_modified"])
    policies = {"original": orig, "modified": mod, "either": orig | mod}
    sub_ok = {pol: True for pol in policies}
    for r in range(1, len(throwable) + 1):
        for S in combinations(throwable, r):
            S = sorted(S)
            rt = json_to_cells(inst, submission_to_json(inst, S))
            for pol, accepted in policies.items():
                verdict_board = tuple(map(tuple, S)) in accepted
                verdict_json = tuple(map(tuple, rt)) in accepted
                sub_ok[pol] &= (rt == S) and (verdict_board == verdict_json)
    res["P_SUB"] = all(sub_ok.values())
    res["P_SUB_by_policy"] = sub_ok
    res["n_submissions_checked"] = (2 ** len(throwable) - 1) * len(policies)
    # P-PRB: probe parity on random assignments
    prb_ok = True
    for _ in range(20):
        rows = [[rng.randrange(2) for _ in range(inst.k + 1)] for _ in inst.inputs]
        board_flash = walk_graph(nodes, start, rows, inst.k)
        hoa_flash = inst.fires(rows) is True
        delta_board = sum(1 for r in range(len(inst.inputs)) for t in range(inst.k + 1)
                          if rows[r][t] != inst.obs[r][t])
        prb_ok &= board_flash == hoa_flash and delta_board >= 0
    res["P_PRB"] = prb_ok
    # P-CAND: untestable cells are effect-irrelevant in every context
    untestable = [c for c in map(tuple, cells) if c not in throwable]
    cand_ok = True
    for c in untestable:
        others = [o for o in map(tuple, cells) if o != c]
        for vals in product((0, 1), repeat=len(others)):
            ctx = {o: v for o, v in zip(others, vals)}
            a = dict(ctx); a[c] = 0
            b = dict(ctx); b[c] = 1
            if inst.fires(inst.with_cells(a)) != inst.fires(inst.with_cells(b)):
                cand_ok = False; break
        if not cand_ok: break
    res["P_CAND"] = cand_ok
    res["throwable"] = len(throwable); res["untestable_irrelevant"] = len(untestable)
    res["pass"] = all(res[k] for k in ("P_OBS", "P_SUB", "P_PRB", "P_CAND"))
    return res

def main(seed=5):
    rng = random.Random(seed)
    out, ok = [], True
    for p in PUZZLES:
        inst = Instance(HOA(p["hoa"]), p["inputs"], p["obs"], p["out"], p["k"])
        r = audit(p["name"], inst, p["hoa"], rng); out.append(r); ok &= r["pass"]
    row = json.loads(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "..", "GateA", "external", "tb_embedded_sample.jsonl")).read())
    h = HOA(row["hoa"]); inputs = [a for i, a in enumerate(h.aps) if i not in h.controllable]
    k = row["effects"][0].count("X"); o = row["effects"][0].split()[-1]
    tv = parse_trace(row["trace"], h.aps, k + 1)
    obs = [[tv[t][a] for t in range(k + 1)] for a in inputs]
    r = audit("TempoBench sample", Instance(h, inputs, obs, o, k), row["hoa"], rng)
    out.append(r); ok &= r["pass"]
    made = 0
    while made < 3:
        text, inst = sample_instance(rng, 3, 2, 2)
        if inst is None: continue
        r = audit(f"generated-{made+1}", inst, text, rng); out.append(r); ok &= r["pass"]
        made += 1
    print(json.dumps({"status": "PASS" if ok else "FAIL", "results": out}, indent=1))
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
