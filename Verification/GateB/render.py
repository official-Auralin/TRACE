"""Junction-graph renderer: the single render core shared by every build and
verification consumer (build_modes, build_from_inputs, verify_modes, GateC
parity). Implements the implementation spec sec. 2.2:

  1. the HOA is unrolled over the causal window into a junction graph
     (one-input tests; Shannon chains for multi-input columns; equal-target
     tests collapsed; effect column routed into ONE bulb / ground per the
     Mealy edge-rendering rule);
  2. EQUIVALENCE IS MACHINE-CHECKED by verify_equivalence(): for every input
     assignment over the window, walking the emitted graph reaches the bulb
     iff the HOA simulation fires (the spec's 'picture = mechanics'
     obligation) -- callers abort the build otherwise.

Pure functions of the instance: byte-determinism of every page built on top
of this module is tested by verify_mode_assignment.py.
"""
from itertools import product
from hoa import expand


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
