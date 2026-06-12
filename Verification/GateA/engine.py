"""Causal-object oracle over HOA transducers (TRACE Gate A reference engine).

Implements, for a point effect X^k o on an observed trace (mainTB sec. framework):
  - PREVENT  : count-only necessity -> singleton pivots or no-pivotal-cell (Prop. pivotal)
  - CREDIT-O : HP actual causes, original/updated variant (Def. actual): AC2(a) necessity
               under a contingency W over OTHER INPUT CELLS at possibly NON-ACTUAL values,
               AC2(b) robustness (every subset of W reset to actual keeps effect), AC3 minimality.
  - CREDIT-M : modified-variant reading on exogenous cells = subset-minimal joint flip
               (others at actual) destroying the effect.
  - PIN      : determining sets (Def. determining): fixing cells forces effect over all
               admissible completions; subset-minimal.
All quantifications are exhaustive over window cells {0..k} x I — ground truth by
enumeration, deliberately unoptimized (this is the reference oracle the production
grader must match)."""
from itertools import product, combinations
from hoa import simulate

class Instance:
    def __init__(self, h, inputs, obs_rows, out_name, k):
        self.h, self.inputs, self.obs, self.k = h, inputs, [list(r) for r in obs_rows], k
        self.out = out_name
        d, outs = simulate(h, inputs, self.obs)
        assert d, "observed inputs not admissible (F2/F3 violation on artifact)"
        _, oidx = h.io_split(inputs)
        self.opos = [h.aps[j] for j in oidx].index(out_name)
        self.obs_outs = outs
        assert outs[k][self.opos] == 1, "effect does not hold on observed trace"
    def cells(self):
        return [(r, t) for r in range(len(self.inputs)) for t in range(self.k + 1)]
    def fires(self, rows):
        d, outs = simulate(self.h, self.inputs, rows)
        if not d: return None                      # inadmissible (signals F2/F3 break)
        return outs[self.k][self.opos] == 1
    def with_cells(self, assign):
        rows = [list(r) for r in self.obs]
        for (r, t), v in assign.items(): rows[r][t] = v
        return rows

def pivots(inst):
    out = []
    for c in inst.cells():
        f = inst.fires(inst.with_cells({c: 1 - inst.obs[c[0]][c[1]]}))
        assert f is not None, "single flip inadmissible: F3 violated"
        if f is False: out.append(c)
    return out

def flip_kills(inst, S):
    return inst.fires(inst.with_cells({c: 1 - inst.obs[c[0]][c[1]] for c in S})) is False

def _search_bound(inst, max_size):
    """Search-depth policy: None (the default) means EXHAUSTIVE over the whole
    window. A finite cap is permitted only as an explicit, caller-certified
    bound: GateB measured that an uncertified size-3 cap silently censors keys
    (49 phantom Credit-vs-Pin divergences vs 0 at full depth — see
    GateB/results/REPORT.md). Callers passing a cap own its certificate."""
    return len(inst.cells()) if max_size is None else max_size

def minimal_flip_sets(inst, max_size=None):
    found = []
    for size in range(1, _search_bound(inst, max_size) + 1):
        for S in combinations(inst.cells(), size):
            if any(set(m) <= set(S) for m in found): continue
            if flip_kills(inst, S): found.append(S)
    return [tuple(sorted(m)) for m in found
            if not any(set(m2) < set(m) for m2 in found)]

def satisfies_ac2(inst, S):
    """Original/updated HP: exists contingency W=w over other window cells s.t.
    (a) flipping all of S (W at w) destroys the effect, and
    (b) with S at actual, effect holds under W=w AND under every subset of W reset
        to actual (robustness)."""
    Sset = set(S)
    others = [c for c in inst.cells() if c not in Sset]
    for wvals in product((0, 1), repeat=len(others)):
        contingency = {c: v for c, v in zip(others, wvals)}
        diff = [c for c in others if contingency[c] != inst.obs[c[0]][c[1]]]
        on = dict(contingency)                                  # S at actual
        off = dict(contingency); off.update({c: 1 - inst.obs[c[0]][c[1]] for c in S})
        if inst.fires(inst.with_cells(on)) is not True: continue
        if inst.fires(inst.with_cells(off)) is not False: continue
        robust = True
        for rsz in range(1, len(diff) + 1):
            for back in combinations(diff, rsz):
                h = dict(on)
                for c in back: h[c] = inst.obs[c[0]][c[1]]
                if inst.fires(inst.with_cells(h)) is not True: robust = False; break
            if not robust: break
        if robust: return True
    return False

def minimal_actual_causes(inst, max_size=None):
    found = []
    for size in range(1, _search_bound(inst, max_size) + 1):
        for S in combinations(inst.cells(), size):
            if any(set(m) <= set(S) for m in found): continue
            if satisfies_ac2(inst, S): found.append(S)
    return [tuple(sorted(m)) for m in found
            if not any(set(m2) < set(m) for m2 in found)]

def sufficient(inst, S):
    """Def. determining: fixing S at actual forces effect over ALL window completions."""
    Sset = set(S)
    others = [c for c in inst.cells() if c not in Sset]
    for vals in product((0, 1), repeat=len(others)):
        f = inst.fires(inst.with_cells({c: v for c, v in zip(others, vals)}))
        if f is not True: return False
    return True

def determining_sets(inst, max_size=None):
    found = []
    for size in range(1, _search_bound(inst, max_size) + 1):
        for S in combinations(inst.cells(), size):
            if any(set(m) <= set(S) for m in found): continue
            if sufficient(inst, S): found.append(S)
    return [tuple(sorted(m)) for m in found
            if not any(set(m2) < set(m) for m2 in found)]

def full_report(inst):
    """All four certified keys at EXHAUSTIVE search depth (the only depth at
    which the report is a certificate; see _search_bound)."""
    pv = pivots(inst)
    co = minimal_actual_causes(inst)
    cm = minimal_flip_sets(inst)
    pn = determining_sets(inst)
    union = sorted(set(c for m in co for c in m))
    return {"pivots": sorted(pv), "no_pivotal_cell": len(pv) == 0,
            "credit_original_minimal_causes": sorted(co),
            "credit_union": union,
            "credit_modified_minimal_causes": sorted(cm),
            "pin_determining_sets": sorted(pn)}

def cellname(inst, c):
    return f"({inst.inputs[c[0]]},{c[1]})"
