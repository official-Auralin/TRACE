"""Verifies the EMITTED TRACE_credit_joint.html end-to-end (sibling of
verify_modes.py for the multi-cell joint page). Reads the shipped file's level
data and replicates the live JS win predicate over the emitted junction graph —
a group S wins iff flipping all of S together (everyone else recorded) darkens
the bulb AND no proper subgroup does — then asserts the accepted (subset-minimal)
groups equal the oracle's modified actual causes (engine.minimal_flip_sets) for
EVERY group. Also asserts the page actually exercises the feature: at least one
emitted level has a multi-cell minimal cause.

Defends the shipped artifact against drift from the builder; CI-suitable."""
import json, re, sys, os
from itertools import combinations
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "GateA"))
from engine import minimal_flip_sets
from render import walk_graph
import build_joint as BJ

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")

def inst_for(name):
    if name in BJ.EXTRA: return BJ.EXTRA[name][0]
    return BJ.inst_of_puzzle(name)

def emitted_levels():
    path = os.path.join(ROOT, "TRACE_credit_joint.html")
    s = open(path).read()
    return json.loads(re.search(r'const LEVELS=(\[.*?\]);\n', s, re.S).group(1))

def check_joint(l, inst):
    """Replicate the page's verdict over the emitted graph for every group."""
    cells = sorted(set(tuple(n["cell"]) for n in l["nodes"] if n["kind"] == "test"))
    def js_kills(S):
        g = {c: 1 - inst.obs[c[0]][c[1]] for c in S}
        return not walk_graph(l["nodes"], l["start"], inst.with_cells(g), l["k"])
    found = []
    for size in range(1, len(cells) + 1):
        for S in combinations(cells, size):
            if any(set(m) <= set(S) for m in found): continue
            if js_kills(set(S)): found.append(S)
    js_min = sorted(tuple(sorted(m)) for m in found
                    if not any(set(m2) < set(m) for m2 in found))
    orc = sorted(tuple(sorted(map(tuple, m))) for m in minimal_flip_sets(inst, max_size=len(inst.cells())))
    return js_min == orc, js_min, orc

def main():
    ok, multicell = True, 0
    for l in emitted_levels():
        inst = inst_for(l["name"])
        good, js_min, orc = check_joint(l, inst)
        ok &= good
        mc = max((len(c) for c in orc), default=0)
        if mc >= 2: multicell += 1
        print(f"JOINT {l['name']:6s} {'OK ' if good else 'FAIL'} max_group={mc}  "
              f"accepted-groups == modified causes {orc}")
    ok &= multicell >= 1
    print(f"\nlevels with a genuine multi-cell cause: {multicell}")
    print("EMITTED JOINT PAGE SEMANTICS == ORACLE:", ok)
    return ok

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
