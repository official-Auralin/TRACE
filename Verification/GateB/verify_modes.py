"""Verifies the three mode pages end-to-end: the live JS verdict semantics
(replicated here over the EMITTED files' level data) coincide with the verified
oracle for EVERY possible player action. Run after build_modes.py; CI-suitable."""
import json, re, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "GateA"))
from itertools import product, combinations
from hoa import HOA
from engine import Instance, pivots, satisfies_ac2, determining_sets, minimal_actual_causes
from fixtures import PUZZLES
from build_player import walk_graph
from a2_corp_compare import parse_trace

def inst_for(name):
    P = {p["name"].split(" ")[0]: p for p in PUZZLES}
    if name in P:
        p = P[name]; return Instance(HOA(p["hoa"]), p["inputs"], p["obs"], p["out"], p["k"])
    row = json.loads(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "..", "GateA", "external", "tb_embedded_sample.jsonl")).read())
    h = HOA(row["hoa"]); inputs = [a for i, a in enumerate(h.aps) if i not in h.controllable]
    k = row["effects"][0].count("X"); o = row["effects"][0].split()[-1]
    tv = parse_trace(row["trace"], h.aps, k + 1)
    return Instance(h, inputs, [[tv[t][a] for t in range(k+1)] for a in inputs], o, k)

def levels(mode):
    s = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", f"TRACE_{mode}.html")).read()
    return json.loads(re.search(r'const LEVELS=(\[.*?\]);\n', s, re.S).group(1))

def lit(l, g):  # JS litOf over emitted graph
    return walk_graph(l["nodes"], l["start"], g, l["k"])

ok = True
# ---- STOP: every tap (single flip) wins iff oracle pivot; tally-complete iff oracle no-pivot
for l in levels("stop"):
    inst = inst_for(l["name"])
    cells = [tuple(n["cell"]) for n in l["nodes"] if n["kind"] == "test"]
    cells = sorted(set(cells))
    js_wins = [c for c in cells if not lit(l, inst.with_cells({c: 1 - inst.obs[c[0]][c[1]]}))]
    orc = sorted(map(tuple, pivots(inst)))
    good = sorted(js_wins) == orc
    ok &= good
    print("STOP  ", l["name"], "taps-that-win == oracle pivots:", good,
          "| o-slash earnable:", not js_wins, "== oracle no-pivot:", (not orc) == (not js_wins))

# ---- PIN: enumerate EVERY lock subset; sweep+minimality verdict == oracle determining sets
for l in levels("pin"):
    inst = inst_for(l["name"])
    cells = sorted(set(tuple(n["cell"]) for n in l["nodes"] if n["kind"] == "test"))
    win_all = [tuple(c) for c in inst.cells()]
    def sweep_ok(lock):
        rest = [c for c in win_all if c not in lock]
        return all(lit(l, inst.with_cells({c: v for c, v in zip(rest, vals)}))
                   for vals in product((0, 1), repeat=len(rest)))
    js_accept = []
    for r in range(1, len(cells) + 1):
        for S in combinations(cells, r):
            S = set(S)
            if sweep_ok(S) and not any(sweep_ok(S - {x}) for x in S if len(S) > 1) \
               and not (len(S) > 1 and any(sweep_ok(set(sub)) for n in range(1, len(S))
                                           for sub in combinations(S, n))):
                js_accept.append(tuple(sorted(S)))
    orc = sorted(tuple(sorted(map(tuple, m))) for m in determining_sets(inst, max_size=len(win_all)))
    good = sorted(js_accept) == orc
    ok &= good
    print("PIN   ", l["name"], "accepted lock-sets == oracle determining sets:", good, "|", orc)

# ---- CREDIT: a claim (cell) is winnable with SOME bench iff oracle singleton actual cause;
#      and the JS robustness check equals AC2(b) for every bench (same enumeration by construction)
for l in levels("credit"):
    inst = inst_for(l["name"])
    cells = sorted(set(tuple(n["cell"]) for n in l["nodes"] if n["kind"] == "test"))
    js_winnable = []
    win_all = [tuple(c) for c in inst.cells()]
    for c in cells:
        others = [o for o in win_all if o != c]
        found = False
        for vals in product((0, 1), repeat=len(others)):
            bench = {o: v for o, v in zip(others, vals)}
            gOn = dict(bench); gOff = dict(bench); gOff[c] = 1 - inst.obs[c[0]][c[1]]
            if not lit(l, inst.with_cells(gOn)) or lit(l, inst.with_cells(gOff)): continue
            diff = [o for o in others if bench[o] != inst.obs[o[0]][o[1]]]
            robust = all(lit(l, inst.with_cells({**gOn, **{d: inst.obs[d[0]][d[1]] for d in back}}))
                         for r in range(1, len(diff) + 1) for back in combinations(diff, r))
            if robust: found = True; break
        if found: js_winnable.append(c)
    orc = sorted(m[0] for m in minimal_actual_causes(inst, max_size=len(win_all)) if len(m) == 1)
    good = sorted(js_winnable) == sorted(map(tuple, orc))
    ok &= good
    print("CREDIT", l["name"], "winnable claims == oracle singleton actual causes:", good, "|", sorted(js_winnable))

print("\nALL MODE SEMANTICS == ORACLE:", ok)
sys.exit(0 if ok else 1)
