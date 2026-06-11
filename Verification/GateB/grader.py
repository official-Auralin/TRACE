"""B1 — Production grader (mainTB Appendix 'Interface Schema and Checker').

Grades a submission against the native predicate of the active mode, using the
validity-oracle + minimality design of mainTB sec. 'Computing and certifying the
answer key' ("certify with the oracle, not the string"). Modes:

  prevent : Def. valid (count-only necessity), submission = singleton pivot at
            actual value, or the no-pivotal-cell verdict. Implemented directly
            from the definition: closest removals = minimum-Hamming admissible
            input changes violating the candidate; valid iff every closest
            removal kills the effect.
  credit  : Def. actual (original/updated HP) — witness | union granularity.
  credit_modified : modified-discipline reading (minimal joint flip) — the
            discipline CORP uses (verified against primary sources; see
            GateA/A2_definitional_note.md).
  pin     : Def. determining (sufficiency), subset-minimal.

Engine semantics are shared with the validated Gate A reference oracle (import),
so B1 regression (b1_regression.py) is an exact-equality check against the
oracle that already reproduces mainTB's five published puzzle answers and the
TempoBench sample key."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "GateA"))
from itertools import product, combinations
from hoa import HOA                                   # GateA, control-validated
from engine import (Instance, pivots, satisfies_ac2, flip_kills, sufficient,
                    minimal_actual_causes, minimal_flip_sets, determining_sets)

# ---------- Def. valid, implemented from the definition (general candidate) ----------
def closest_removals(inst, cand):
    """cand: set of cells (at actual values). Returns (m, removals): all admissible
    input grids violating C_cand at minimum Hamming distance m from the observed."""
    cells = inst.cells()
    best, removals = None, []
    for vals in product((0, 1), repeat=len(cells)):
        assign = {c: v for c, v in zip(cells, vals)}
        if all(assign[c] == inst.obs[c[0]][c[1]] for c in cand):
            continue                                   # does not violate C
        d = sum(1 for c in cells if assign[c] != inst.obs[c[0]][c[1]])
        if best is None or d < best: best, removals = d, [assign]
        elif d == best: removals.append(assign)
    return best, removals

def valid_cause(inst, cand):
    """mainTB Def. valid: actuality + non-vacuity + every closest removal kills."""
    if not cand: return False
    _, rem = closest_removals(inst, cand)
    if not rem: return False
    return all(inst.fires(inst.with_cells(a)) is False for a in rem)

def subset_minimal(pred, cand):
    if not pred(cand): return False
    for r in range(1, len(cand)):
        for sub in combinations(sorted(cand), r):
            if pred(set(sub)): return False
    return True

# ---------- grading entry points ----------
def grade_prevent(inst, submission, no_pivot=False):
    if no_pivot:
        return {"correct": len(pivots(inst)) == 0, "predicate": "no-pivotal-cell verdict"}
    if len(submission) != 1:
        return {"correct": False, "predicate": "prevent submissions are singletons (Prop. pivotal)"}
    ok = subset_minimal(lambda S: valid_cause(inst, S), set(submission))
    return {"correct": ok, "predicate": "valid cause (Def. valid) + minimality"}

def grade_credit(inst, submission, granularity="witness", variant="original"):
    S = set(submission)
    if variant == "original":
        pred = lambda T: satisfies_ac2(inst, sorted(T))
        keysets = minimal_actual_causes(inst, max_size=len(inst.cells()))
    elif variant == "modified":
        pred = lambda T: flip_kills(inst, sorted(T))
        keysets = minimal_flip_sets(inst, max_size=len(inst.cells()))
    else: raise ValueError(variant)
    if granularity == "witness":
        return {"correct": subset_minimal(pred, S), "predicate": f"minimal actual cause ({variant})"}
    if granularity == "union":
        union = set(c for m in keysets for c in m)
        return {"correct": S == union, "predicate": f"per-cell union ({variant})",
                "key_union": sorted(union)}
    raise ValueError(granularity)

def grade_pin(inst, submission):
    ok = subset_minimal(lambda T: sufficient(inst, sorted(T)), set(submission))
    return {"correct": ok, "predicate": "determining set (Def. determining) + minimality"}

def keys(inst, cap=None):
    """cap: optional certified bound on minimal-cause size (recorded by callers);
    None = exhaustive (full window)."""
    m = cap or len(inst.cells())
    return {"pivots": sorted(pivots(inst)),
            "credit_original": sorted(minimal_actual_causes(inst, max_size=m)),
            "credit_modified": sorted(minimal_flip_sets(inst, max_size=m)),
            "pin": sorted(determining_sets(inst, max_size=m))}
