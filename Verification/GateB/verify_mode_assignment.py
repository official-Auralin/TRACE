"""Proves the mode-assignment + arbitrary-input build pipeline is deterministic
and lands the gold instances correctly.

  A1 gold placement: the five worked puzzles + the TempoBench artifact classify
     to their pedagogically-defining modes (P3,P5->credit; P4->pin; P1,P2,TB->stop).
  A2 totality+purity: on freshly generated random instances, assign_mode is
     total on retained instances and returns the identical verdict when called
     twice on independently re-parsed copies of the same inputs.
  A3 declaration wins: an explicit "mode" field overrides the rule.
  D1/D2 build determinism over the FULL gold-12 input set (the same twelve
     instances the retired single-board build shipped): building twice, and
     building with the input order reversed, yields byte-identical pages;
     gold12.jsonl itself regenerates byte-identically (D0)."""
import json, sys, os, random, hashlib
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "GateA"))
from hoa import HOA
from engine import Instance
from fixtures import PUZZLES
from generator import sample_instance, random_mealy
from mode_assign import assign_mode
from build_from_inputs import main as build_main, row_to_instance, instance_id
from gold_inputs import gold_rows

ok = True
# A1 gold placement
expect = {"P1": "stop", "P2": "stop", "P3": "credit", "P4": "pin", "P5": "credit"}
for p in PUZZLES:
    name = p["name"].split(" ")[0]
    inst = Instance(HOA(p["hoa"]), p["inputs"], p["obs"], p["out"], p["k"])
    mode, why = assign_mode(inst)
    good = mode == expect[name]; ok &= good
    print(f"A1 {name}: {mode:6s} ({why})  {'OK' if good else 'WRONG, expected '+expect[name]}")
row = json.loads(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "..", "GateA", "external", "tb_embedded_sample.jsonl")).read())
mode, why = assign_mode(row_to_instance(row))
ok &= mode == "stop"
print(f"A1 TB: {mode} ({why})  {'OK' if mode=='stop' else 'WRONG'}")

# A2 totality + purity on random instances
rng = random.Random(99)
dist = {"stop": 0, "pin": 0, "credit": 0, "trivial": 0}
for _ in range(40):
    text, inst = sample_instance(rng, 3, 2, 2)
    if inst is None: continue
    try:
        m1, _ = assign_mode(inst)
        # purity: rebuild instance from scratch and re-assign
        inst2 = Instance(HOA(text), inst.inputs, inst.obs, inst.out, inst.k)
        m2, _ = assign_mode(inst2)
        assert m1 == m2, "impure classification"
        dist[m1] += 1
    except ValueError:
        dist["trivial"] += 1
print("A2 distribution over 40 random instances:", dist, "| purity OK")

# A3 declaration wins
m, why = assign_mode(row_to_instance(row), declared="credit")
ok &= (m == "credit" and why == "declared")
print("A3 declared mode overrides:", m == "credit")

# D0 gold12 regenerates byte-identically; D1/D2 build determinism over gold-12
g1 = "\n".join(json.dumps(r, sort_keys=True) for r in gold_rows())
g2 = "\n".join(json.dumps(r, sort_keys=True) for r in gold_rows())
ok &= g1 == g2
print("D0 gold12 input set regenerates byte-identically:", g1 == g2,
      f"({len(gold_rows())} rows)")
rows = gold_rows()
d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
f1, f2 = os.path.join(d, "auto_in1.jsonl"), os.path.join(d, "auto_in2.jsonl")
open(f1, "w").write("\n".join(json.dumps(r) for r in rows))
open(f2, "w").write("\n".join(json.dumps(r) for r in reversed(rows)))
import io, contextlib
buf = io.StringIO()
with contextlib.redirect_stdout(buf): s1, log1 = build_main([f1])
with contextlib.redirect_stdout(buf): s1b, _ = build_main([f1])
with contextlib.redirect_stdout(buf): s2, log2 = build_main([f2])
ok &= s1 == s1b == s2
print("D1 same inputs twice -> byte-identical pages:", s1 == s1b)
print("D2 reversed input order -> byte-identical pages:", s1 == s2)
print("   pages:", s1)
print("\nMODE ASSIGNMENT + AUTO-BUILD DETERMINISTIC:", ok)
sys.exit(0 if ok else 1)
