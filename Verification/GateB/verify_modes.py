"""Verifies the mode pages end-to-end: the live JS verdict semantics
(replicated here over the EMITTED files' level data) coincide with the verified
oracle for EVERY possible player action. Covers BOTH page families:

  curated  TRACE_stop/pin/credit.html         (built by build_modes.py)
  gold-12  TRACE_auto_stop/pin/credit.html    (built by build_from_inputs.py
           from results/gold12.jsonl — the same twelve instances the retired
           single-board build shipped, so pipeline coverage of those inputs
           is part of this suite's PASS condition)

Run after build_modes.py and build_from_inputs.py; CI-suitable."""
import json, re, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "GateA"))
from itertools import product, combinations
from hoa import HOA
from engine import Instance, pivots, satisfies_ac2, determining_sets, minimal_actual_causes
from fixtures import PUZZLES
from render import walk_graph
from a2_corp_compare import parse_trace

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")

def inst_for(name):
    P = {p["name"].split(" ")[0]: p for p in PUZZLES}
    if name in P:
        p = P[name]; return Instance(HOA(p["hoa"]), p["inputs"], p["obs"], p["out"], p["k"])
    row = json.loads(open(os.path.join(HERE, "..", "GateA", "external",
                                       "tb_embedded_sample.jsonl")).read())
    return inst_of_row(row)

def inst_of_row(row):
    h = HOA(row["hoa"]); inputs = [a for i, a in enumerate(h.aps) if i not in h.controllable]
    k = row["effects"][0].count("X"); o = row["effects"][0].split()[-1]
    tv = parse_trace(row["trace"], h.aps, k + 1)
    return Instance(h, inputs, [[tv[t][a] for t in range(k+1)] for a in inputs], o, k)

def levels(page):
    path = os.path.join(ROOT, f"{page}.html")
    if not os.path.exists(path): return None
    s = open(path).read()
    return json.loads(re.search(r'const LEVELS=(\[.*?\]);\n', s, re.S).group(1))

def lit(l, g):  # JS litOf over emitted graph
    return walk_graph(l["nodes"], l["start"], g, l["k"])

# ---------- per-mode checks: every possible player action vs the oracle ----------
def check_stop(l, inst):
    """Every tap (single flip) wins iff oracle pivot; o-slash legal iff no pivot."""
    cells = sorted(set(tuple(n["cell"]) for n in l["nodes"] if n["kind"] == "test"))
    js_wins = [c for c in cells
               if not lit(l, inst.with_cells({c: 1 - inst.obs[c[0]][c[1]]}))]
    orc = sorted(map(tuple, pivots(inst)))
    return sorted(js_wins) == orc, f"taps-that-win == pivots; o-slash == {not orc}"

def check_pin(l, inst):
    """Every lock subset: sweep + minimality verdict == oracle determining sets."""
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
            if sweep_ok(S) and not (len(S) > 1 and any(sweep_ok(set(sub))
                                    for n in range(1, len(S))
                                    for sub in combinations(S, n))):
                js_accept.append(tuple(sorted(S)))
    orc = sorted(tuple(sorted(map(tuple, m))) for m in determining_sets(inst))
    return sorted(js_accept) == orc, f"accepted lock-sets == determining sets {orc}"

def check_credit(l, inst):
    """A claim (cell) is winnable with SOME bench iff oracle singleton actual
    cause; the JS robustness check equals AC2(b) for every bench (same
    enumeration by construction)."""
    cells = sorted(set(tuple(n["cell"]) for n in l["nodes"] if n["kind"] == "test"))
    win_all = [tuple(c) for c in inst.cells()]
    js_winnable = []
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
    orc = sorted(m[0] for m in minimal_actual_causes(inst) if len(m) == 1)
    return sorted(js_winnable) == sorted(map(tuple, orc)), f"winnable claims == singleton causes {sorted(js_winnable)}"

CHECK = {"stop": check_stop, "pin": check_pin, "credit": check_credit}

ok = True

# ---------- curated pages ----------
for mode in ("stop", "pin", "credit"):
    for l in levels(f"TRACE_{mode}"):
        good, detail = CHECK[mode](l, inst_for(l["name"]))
        ok &= good
        print(f"{mode.upper():6s} {l['name']:8s} {'OK ' if good else 'FAIL'} {detail}")

# ---------- gold-12 auto pages: coverage of the retired build's twelve inputs ----------
gold_path = os.path.join(HERE, "results", "gold12.jsonl")
if not os.path.exists(gold_path):
    import gold_inputs; gold_inputs.write()
rows = {r["name"]: r for r in (json.loads(ln) for ln in open(gold_path)) }
covered = set()
for mode in ("stop", "pin", "credit"):
    lv = levels(f"TRACE_auto_{mode}")
    if lv is None: continue
    for l in lv:
        row = rows.get(l["name"])
        assert row is not None, f"auto level {l['name']} not in gold12 inputs"
        good, detail = CHECK[mode](l, inst_of_row(row))
        ok &= good; covered.add(l["name"])
        print(f"AUTO-{mode.upper():6s} {l['name']:8s} {'OK ' if good else 'FAIL'} {detail}")
# every gold input is accounted for: emitted (verified above) or rejected with a reason
blog = json.load(open(os.path.join(HERE, "results", "gold12_build.json")))
logged = {e["name"]: e for e in blog["classified"]}
missing = []
for name in rows:
    if name in covered: continue
    e = logged.get(name)
    if e is None or not (e.get("rejected") or e.get("mode") is None):
        missing.append(name); continue
    why = e.get("rejected") or [e["why"]]
    print(f"GOLD   {name:8s} REJECTED (deterministic, logged): {'; '.join(why)}")
ok &= not missing
if missing: print("UNACCOUNTED GOLD INPUTS:", missing)
print(f"\ngold-12 coverage: {len(rows)} inputs = {len(covered)} emitted+verified + {len(rows)-len(covered)} rejected-with-reason")
print("ALL MODE SEMANTICS == ORACLE:", ok)
sys.exit(0 if ok else 1)
