"""Proves the premise behind TRACE_credit_joint.html (build_joint.py): in the
models TRACE/TempoBench use — flat, input-COMPLETE (F3) transducers, where the
effect is a TOTAL Boolean function of the window cells — the HP *original/updated*
actual-cause variant has NO multi-cell minimal causes, whereas the *modified*
variant routinely does. The CREDIT IT page (original/updated) therefore loses no
expressible answer by restricting to singletons; the multi-cell difficulty lives
in the modified reading, which is what TRACE_credit_joint.html grades (and what
CORP, the TempoBench key source, implements — see GateA/A2_definitional_note.md).

This is the machine-checked backing for mainTB Proposition prop:atomize (the
original/updated analog of prop:pivotal's count-only-necessity collapse).

Three layers of evidence, strongest first:
  * SMT (z3): for every window width n=2..8 (the FULL benchmark range, since the
    quality gate caps windows at MAX_WINDOW_CELLS=8) and every cause-size s>=2,
    "exists f with a size-s minimal actual cause" is UNSAT -> a PROOF that every
    minimal original/updated cause on a benchmark instance is a singleton;
  * brute enumeration: all 2^(2^n) functions for n<=4 (exhaustive) yield 0 multi-cell;
  * random: 320k functions at n=5,6 yield 0 (corroboration only).
The fast raw-truth-table HP-original AC2 used by the enumeration is selftested
equal to the Gate-A reference engine (engine.minimal_actual_causes).

All-ones observation == every observation, by coordinate-negation symmetry
(negating input coordinate i is an automorphism of the cube carrying (f,obs) to
(f',all-ones) preserving causes), so an all-ones sweep over all functions is an
exhaustive sweep over all (function, observation) pairs.

Deterministic (fixed RNG seeds; SMT is decision-only); CI-suitable (exit code).
Gracefully degrades to the enumeration layers if z3 is unavailable."""
import sys, os, itertools, random, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "GateA"))
from engine import Instance, minimal_actual_causes, minimal_flip_sets
from hoa import HOA

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------- fast raw HP-original AC2 over a truth table (obs = all ones) ----------
def ac2_raw(f, n, S):
    Sset = set(S)
    others = [j for j in range(n) if j not in Sset]
    for w in range(1 << len(others)):
        on = 0
        for j in Sset: on |= (1 << j)
        diff = []
        for b, j in enumerate(others):
            if (w >> b) & 1: on |= (1 << j)
            else: diff.append(j)
        off = on & ~sum(1 << j for j in Sset)
        if f[on] != 1 or f[off] != 0: continue
        robust = True
        for r in range(1, len(diff) + 1):
            for back in itertools.combinations(diff, r):
                h = on
                for j in back: h |= (1 << j)
                if f[h] != 1: robust = False; break
            if not robust: break
        if robust: return True
    return False

def min_causes_raw(f, n):
    found = []
    for size in range(1, n + 1):
        for S in itertools.combinations(range(n), size):
            if any(set(m) <= set(S) for m in found): continue
            if ac2_raw(f, n, S): found.append(S)
    return [m for m in found if not any(set(m2) < set(m) for m2 in found)]

def comb_instance(n, bits):
    """Single-state Mealy machine realizing the truth table `bits` (idx = sum x_j<<j)."""
    aps = " ".join(f'"x{i}"' for i in range(n)) + ' "o"'
    lines = ["State: 0"]
    for iv in itertools.product((0, 1), repeat=n):
        idx = sum(iv[j] << j for j in range(n))
        olit = f"{n}" if bits[idx] else f"!{n}"
        ilits = " & ".join((f"{j}" if iv[j] else f"!{j}") for j in range(n))
        lines.append(f"[{olit} & {ilits}] 0")
    text = (f"HOA: v1\nStates: 1\nStart: 0\nAP: {n+1} {aps}\n"
            f"controllable-AP: {n}\nAcceptance: 0 t\n--BODY--\n" + "\n".join(lines) + "\n--END--\n")
    return Instance(HOA(text), [f"x{i}" for i in range(n)], [[1]] * n, "o", 0)

def selftest(trials=300, seed=1):
    rng = random.Random(seed)
    for _ in range(trials):
        n = rng.choice([2, 3, 4])
        bits = [rng.getrandbits(1) for _ in range(1 << n)]
        bits[(1 << n) - 1] = 1
        raw = sorted(tuple(c) for c in min_causes_raw(bits, n))
        eng = sorted(tuple(c[0] for c in m) for m in minimal_actual_causes(comb_instance(n, bits), max_size=n))
        assert raw == eng, f"raw != engine on n={n} bits={bits}: {raw} vs {eng}"
    return trials

def exhaustive(n):
    hits = 0
    for mask in range(1 << (1 << n)):
        bits = [(mask >> i) & 1 for i in range(1 << n)]
        if not bits[(1 << n) - 1]: continue
        if any(len(c) >= 2 for c in min_causes_raw(bits, n)): hits += 1
    return hits

def random_sweep(n, samples, seed=7):
    rng = random.Random(seed)
    hits = 0
    for _ in range(samples):
        bits = [rng.getrandbits(1) for _ in range(1 << n)]
        bits[(1 << n) - 1] = 1
        if any(len(c) >= 2 for c in min_causes_raw(bits, n)): hits += 1
    return hits

# ---------- AUTHORITATIVE: SMT proof (z3) that no minimal multi-cell cause exists ----------
# For each (n, s>=2) z3 decides: does there exist a total f with f(all-ones)=1 such
# that S={0..s-1} satisfies AC2 (some contingency) while EVERY nonempty proper subset
# of S fails AC2 (all contingencies)? UNSAT for every s in 2..n  ==>  every minimal
# actual cause at width n is a singleton (a PROOF, not a sample). Fixing S to the first
# s cells is WLOG by coordinate-permutation symmetry. This is the original/updated
# analog of mainTB Proposition prop:pivotal (count-only necessity collapse).
def smt_atomization(maxn):
    try:
        from z3 import Bool, Solver, And, Or, Not, sat, unsat
    except Exception as e:
        return {"available": False, "reason": str(e)}
    def proof(n, s):
        F = [Bool(f"f{i}") for i in range(1 << n)]
        full = (1 << n) - 1
        cons = [F[full]]
        def ac2(S):
            Sset = set(S); others = [j for j in range(n) if j not in Sset]; cl = []
            for w in range(1 << len(others)):
                on = full; diff = []
                for b, j in enumerate(others):
                    if not ((w >> b) & 1): on &= ~(1 << j); diff.append(j)
                off = on & ~sum(1 << j for j in Sset)
                leg = [Not(F[off])]
                for r in range(0, len(diff) + 1):
                    for back in itertools.combinations(diff, r):
                        h = on
                        for j in back: h |= (1 << j)
                        leg.append(F[h])
                cl.append(And(*leg))
            return Or(*cl)
        S = list(range(s)); cons.append(ac2(S))
        for r in range(1, s):
            for T in itertools.combinations(S, r):
                cons.append(Not(ac2(list(T))))
        sol = Solver(); sol.add(*cons); return sol.check() == unsat
    res = {"available": True, "max_n": maxn, "all_unsat": True, "per_n": {}}
    for n in range(2, maxn + 1):
        row = {s: proof(n, s) for s in range(2, n + 1)}
        res["per_n"][n] = row
        if not all(row.values()): res["all_unsat"] = False
    return res

def main():
    rep = {}
    rep["selftest_trials"] = selftest()
    # AUTHORITATIVE proof: SMT over the full benchmark window range (cap is
    # MAX_WINDOW_CELLS=8 in build_from_inputs). UNSAT everywhere == proven.
    rep["smt_atomization"] = smt_atomization(8)
    # Corroboration: brute-enumeration (n<=4 exhaustive) + random (n=5,6).
    rep["original_multicell_enum"] = {
        "n3_exhaustive": exhaustive(3),
        "n4_exhaustive": exhaustive(4),
        "n5_random_200k": random_sweep(5, 200_000),
        "n6_random_120k": random_sweep(6, 120_000, seed=11),
    }
    # modified variant DOES produce multi-cell causes — the build_joint fixtures:
    or3 = comb_instance(3, [0,1,1,1,1,1,1,1])              # a OR b OR c
    het = comb_instance(3, [0,0,0,1,0,1,0,1])              # a AND (b OR c)  (idx=sum x_j<<j)
    rep["modified_multicell_examples"] = {
        "OR3_triple": [list(map(list, c)) for c in minimal_flip_sets(or3, max_size=3)],
        "HET_singleton_plus_pair": [list(map(list, c)) for c in minimal_flip_sets(het, max_size=3)],
    }
    enum_total = sum(rep["original_multicell_enum"].values())
    smt = rep["smt_atomization"]
    smt_ok = smt.get("available") and smt.get("all_unsat")
    rep["VERDICT"] = {
        "original_variant_atomizes_smt_proven_to_n": smt.get("max_n") if smt_ok else None,
        "original_variant_atomizes_enum_corroborated": enum_total == 0,
        "modified_variant_has_multicell":
            any(len(c) >= 2 for c in minimal_flip_sets(or3, max_size=3)) and
            any(len(c) >= 2 for c in minimal_flip_sets(het, max_size=3)),
    }
    ok = (smt_ok or smt.get("available") is False) and enum_total == 0 \
         and rep["VERDICT"]["modified_variant_has_multicell"]
    print(json.dumps(rep, indent=1))
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    open(os.path.join(HERE, "results", "atomization.json"), "w").write(json.dumps(rep, indent=1, sort_keys=True))
    if smt_ok:
        print(f"\nATOMIZATION PROVEN by SMT for all window widths n<=8 (the full benchmark range); "
              f"enum-corroborated; modified variant carries the multi-cell causes.")
    else:
        print(f"\nz3 unavailable; atomization enum-corroborated (n<=4 exhaustive, n=5,6 random). ok={ok}")
    return ok

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
