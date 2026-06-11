"""Builds TRACE_play.html — a playable review build of HOA-derived puzzles.

Levels: the five mainTB worked puzzles (HOA fixtures), the real TempoBench sample
artifact, and freshly generated instances from the B2 generator. For each level:
  1. the HOA is unrolled over the causal window into a junction graph
     (one-input tests; Shannon chains for multi-input columns; equal-target
     tests collapsed; effect column routes into ONE bulb / ground per the
     Mealy edge-rendering rule of the implementation spec);
  2. EQUIVALENCE IS MACHINE-CHECKED: for every input assignment over the window,
     walking the emitted graph reaches the bulb iff the HOA simulation fires
     (the spec's 'picture = mechanics' obligation) — the build aborts otherwise;
  3. the accepted witness sets are computed by the verified oracle (minimal
     actual causes, original/updated variant, UNION minimal flip sets, modified)
     and embedded as the grading key — the page never re-derives causality.
"""
import json, random, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "GateA"))
from itertools import product
from hoa import HOA, expand
from engine import Instance, minimal_actual_causes, minimal_flip_sets
from itertools import product as iproduct, combinations as icombos
from fixtures import PUZZLES
from generator import sample_instance

def find_contingency(inst, S):
    """The W=w certifying S as a decider (same search as satisfies_ac2, returning
    the held cells that differ from the recording). Used only for the in-game
    pair-of-runs demonstration; grading still uses the oracle."""
    Sset = set(map(tuple, S))
    others = [c for c in inst.cells() if tuple(c) not in Sset]
    for wvals in iproduct((0, 1), repeat=len(others)):
        cont = {tuple(c): v for c, v in zip(others, wvals)}
        diff = [c for c in others if cont[tuple(c)] != inst.obs[c[0]][c[1]]]
        on = dict(cont); off = dict(cont)
        off.update({tuple(c): 1 - inst.obs[c[0]][c[1]] for c in S})
        if inst.fires(inst.with_cells(on)) is not True: continue
        if inst.fires(inst.with_cells(off)) is not False: continue
        robust = True
        for rsz in range(1, len(diff) + 1):
            for back in icombos(diff, rsz):
                h = dict(on)
                for c in back: h[tuple(c)] = inst.obs[c[0]][c[1]]
                if inst.fires(inst.with_cells(h)) is not True: robust = False; break
            if not robust: break
        if robust:
            return [[c[0], c[1], cont[tuple(c)]] for c in diff]   # held-off backups
    return None

# ---------- junction-graph construction ----------
def build_graph(inst):
    h, inputs, k = inst.h, inst.inputs, inst.k
    table, iidx, oidx = expand(h, inputs)
    opos = inst.opos
    nodes = []
    cons = {}                  # structural hash-consing: identical tests share a node,
                               # so the "does this input matter?" collapse sees through
                               # isomorphic subtrees (no phantom junctions)
    def add(n):
        key = (n["kind"], tuple(n.get("cell", [])), n.get("out1"), n.get("out0"), n.get("next"))
        if key in cons: return cons[key]
        nodes.append(n); cons[key] = len(nodes) - 1
        return cons[key]
    BULB = add({"kind": "bulb"}); GND = add({"kind": "gnd"})
    # reachable states per column (arbitrary inputs)
    cols = [{h.start}]
    for t in range(k):
        nxt = set()
        for s in cols[-1]:
            for iv in range(2 ** len(inputs)):
                nxt.add(table[(s, tuple((iv >> j) & 1 for j in range(len(inputs))))][0][1])
        cols.append(nxt)
    # build per (t, state): a chain testing inputs in order; returns entry node id
    memo = {}
    def target(t, s, ivals):
        opts = table[(s, ivals)]
        ovals, dst = opts[0]
        if t == k: return BULB if ovals[opos] == 1 else GND
        return entry(t + 1, dst)
    def chain(t, s, fixed):
        r = len(fixed)
        if r == len(inputs):
            return target(t, s, tuple(fixed))
        # does input r matter given fixed prefix? (compare full subtrees)
        def subtree(v): return chain(t, s, fixed + [v])
        a, b = subtree(1), subtree(0)
        if a == b: return a
        return add({"kind": "test", "cell": [r, t], "out1": a, "out0": b, "col": t, "state": s})
    def col_of(i):
        n = nodes[i]
        return n["col"] if n["kind"] == "test" else k + 1
    def entry(t, s):
        """Guarantees a VISIBLE node at column t: the machine's march through a
        moment it ignores is drawn as pass-through track (no empty columns)."""
        if (t, s) in memo: return memo[(t, s)]
        e = chain(t, s, [])
        if col_of(e) > t:                       # chain collapsed past this column
            e2 = e
            for tt in range(min(col_of(e), k + 1) - 1, t - 1, -1):
                e2 = add({"kind": "pass", "col": tt, "next": e2})
            e = e2
        memo[(t, s)] = e
        return e
    start = entry(0, h.start)
    # layout: x by column (test sub-level offsets), y by discovery order per column
    ycount = {}
    for n in nodes:
        if n["kind"] == "test":
            x = n["col"] + 0.45 * n["cell"][0]
            n["x"] = x
            ycount.setdefault(round(x, 2), 0)
            n["y"] = ycount[round(x, 2)] * 1.15 + 0.4 * n["cell"][0]
            ycount[round(x, 2)] += 1
    maxy = max([n.get("y", 0) for n in nodes] + [1])
    nodes[BULB].update({"x": k + 1, "y": 0})
    nodes[GND].update({"x": k + 1, "y": maxy + 0.8})
    # pass nodes ride the y of what they lead to (straight march); chains resolve
    # by fixpoint since creation order is innermost-first
    pending = [n for n in nodes if n["kind"] == "pass"]
    for n in pending: n["x"] = n["col"]
    for _ in range(len(pending) + 1):
        for n in pending:
            if "y" not in n and "y" in nodes[n["next"]]:
                n["y"] = nodes[n["next"]]["y"]
    assert all("y" in n for n in pending), "unresolved pass-node layout"
    return nodes, start

def walk_graph(nodes, start, rows, k):
    cur = start
    for _ in range(200):
        n = nodes[cur]
        if n["kind"] == "bulb": return True
        if n["kind"] == "gnd": return False
        if n["kind"] == "pass": cur = n["next"]; continue
        r, t = n["cell"]
        cur = n["out1"] if rows[r][t] else n["out0"]
    raise RuntimeError("walk did not terminate")

def verify_equivalence(inst, nodes, start):
    cells = inst.cells()
    for vals in product((0, 1), repeat=len(cells)):
        rows = [list(r) for r in inst.obs]
        for (r, t), v in zip(cells, vals): rows[r][t] = v
        if walk_graph(nodes, start, rows, inst.k) != (inst.fires(rows) is True):
            return False
    return True

def level(name, provenance, inst):
    nodes, start = build_graph(inst)
    assert verify_equivalence(inst, nodes, start), f"RENDER != HOA on {name}"
    orig = set(tuple(sorted(m)) for m in minimal_actual_causes(inst, max_size=len(inst.cells())))
    mod = set(tuple(sorted(m)) for m in minimal_flip_sets(inst, max_size=len(inst.cells())))
    accepted = sorted(orig | mod)
    why = ["decider" if m in orig and m not in mod else
           "extinguish" if m in mod and m not in orig else "both" for m in accepted]
    demos = [find_contingency(inst, list(m)) if w == "decider" else []
             for m, w in zip(accepted, why)]
    assert all(d is not None for d in demos), "decider without certifiable contingency"
    return {"name": name, "prov": provenance, "k": inst.k,
            "inputs": inst.inputs, "obs": inst.obs,
            "nodes": nodes, "start": start,
            "accepted": [[list(c) for c in m] for m in accepted],
            "why": why, "demos": demos,
            "verified": True}

def main(seed=23, n_generated=6):
    levels = []
    for p in PUZZLES:
        inst = Instance(HOA(p["hoa"]), p["inputs"], p["obs"], p["out"], p["k"])
        levels.append(level(p["name"].split(" ")[0], "mainTB worked puzzle (HOA fixture)", inst))
    row = json.loads(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "..", "GateA", "external", "tb_embedded_sample.jsonl")).read())
    h = HOA(row["hoa"]); inputs = [a for i, a in enumerate(h.aps) if i not in h.controllable]
    from a2_corp_compare import parse_trace
    k = row["effects"][0].count("X"); out = row["effects"][0].split()[-1]
    tv = parse_trace(row["trace"], h.aps, k + 1)
    obs = [[tv[t][a] for t in range(k + 1)] for a in inputs]
    levels.append(level("TB", "real TempoBench artifact (6-state arbiter)",
                        Instance(h, inputs, obs, out, k)))
    rng = random.Random(seed)
    strata = [(2, 1, 2), (2, 2, 2), (3, 2, 2), (3, 1, 3), (3, 2, 3), (4, 2, 3)]
    got = 0
    while got < n_generated and strata:
        st, ni, k2 = strata[got % len(strata)]
        _, inst = sample_instance(rng, st, ni, k2)
        if inst is None: continue
        if not minimal_actual_causes(inst, max_size=len(inst.cells())): continue  # trivial filter
        levels.append(level(f"G{got+1}", f"generated: {st} states, |I|={ni}, k={k2} (seed {seed})", inst))
        got += 1
    tpl = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "player_template.html")).read()
    html = tpl.replace("/*__LEVELS__*/", json.dumps(levels))
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "TRACE_play.html")
    open(out_path, "w").write(html)
    print(f"built {out_path}: {len(levels)} levels, all render==HOA verified")

if __name__ == "__main__":
    main()
