"""Minimal HOA v1 parser + transducer semantics for TRACE Gate A.

Scope: explicit-state HOA with symbolic transition labels (Boolean formulas over
AP indices), as emitted by ltlsynt/Spot and used by TempoBench (mainTB Def. hoa).
Acceptance is parsed but IGNORED for behavior (run-defined / F=Q reading,
mainTB Def. hoa: "admissible iff its run is merely defined").
"""
import re
from itertools import product

class Formula:
    def __init__(self, kind, a=None, b=None, idx=None):
        self.kind, self.a, self.b, self.idx = kind, a, b, idx
    def eval(self, val):  # val: dict ap_index -> bool
        k = self.kind
        if k == 't': return True
        if k == 'f': return False
        if k == 'ap': return bool(val[self.idx])
        if k == '!': return not self.a.eval(val)
        if k == '&': return self.a.eval(val) and self.b.eval(val)
        if k == '|': return self.a.eval(val) or self.b.eval(val)
        raise ValueError(k)

def parse_formula(s, aps=None):
    """Labels may reference APs by index ([!0 & 1]) or by name ([!g & r]) —
    TempoBench artifacts use names; Spot's canonical form uses indices."""
    toks = re.findall(r'[A-Za-z_][A-Za-z0-9_]*|\d+|[!&|()]', s)
    pos = [0]
    def ap_index(t):
        if t.isdigit(): return int(t)
        if aps is None or t not in aps:
            if t == 't': return 't'
            if t == 'f': return 'f'
            raise ValueError(f"unknown AP '{t}' in label '{s}'")
        return aps.index(t)
    def peek(): return toks[pos[0]] if pos[0] < len(toks) else None
    def eat(): t = toks[pos[0]]; pos[0] += 1; return t
    def atom():
        t = eat()
        if t == '(':
            e = disj(); assert eat() == ')'; return e
        if t == '!': return Formula('!', a=atom())
        r = ap_index(t)
        if r == 't': return Formula('t')
        if r == 'f': return Formula('f')
        return Formula('ap', idx=r)
    def conj():
        e = atom()
        while peek() == '&': eat(); e = Formula('&', a=e, b=atom())
        return e
    def disj():
        e = conj()
        while peek() == '|': eat(); e = Formula('|', a=e, b=conj())
        return e
    e = disj()
    assert pos[0] == len(toks), f"trailing tokens in label: {s}"
    return e

class HOA:
    def __init__(self, text):
        self.text = text
        self.aps, self.start, self.n_states = [], 0, 0
        self.controllable = None          # set of AP indices declared controllable (outputs)
        self.acceptance_sets = 0
        self.edges = {}                   # state -> list[(Formula, dest)]
        self._parse(text)
    def _parse(self, text):
        body = False; cur = None
        for raw in text.splitlines():
            line = raw.strip()
            if not line: continue
            if line == '--BODY--': body = True; continue
            if line == '--END--': break
            if not body:
                if line.startswith('States:'): self.n_states = int(line.split()[1])
                elif line.startswith('Start:'): self.start = int(line.split()[1])
                elif line.startswith('AP:'):
                    self.aps = re.findall(r'"([^"]*)"', line)
                    assert int(line.split()[1]) == len(self.aps)
                elif line.startswith('controllable-AP:'):
                    self.controllable = set(int(x) for x in line.split()[1:])
                elif line.startswith('Acceptance:'):
                    self.acceptance_sets = int(line.split()[1])
            else:
                if line.startswith('State:'):
                    cur = int(re.match(r'State:\s*(\d+)', line).group(1))
                    self.edges.setdefault(cur, [])
                else:
                    m = re.match(r'\[(.*)\]\s*(\d+)', line)
                    if m: self.edges[cur].append((parse_formula(m.group(1), self.aps), int(m.group(2))))
    def io_split(self, inputs):
        """inputs: list of AP names. Returns (input_idx, output_idx) lists."""
        iidx = [self.aps.index(a) for a in inputs]
        oidx = [j for j in range(len(self.aps)) if j not in iidx]
        return iidx, oidx

def expand(h, inputs):
    """Explicit transducer table: (state, input-valuation) -> list[(out-val, dest)].
    Cost O(|Q|*2^|AP|) — the one-time expansion of mainTB sec. groundtruth."""
    iidx, oidx = h.io_split(inputs)
    table = {}
    for s in range(h.n_states):
        for ivals in product((0, 1), repeat=len(iidx)):
            opts = []
            for ovals in product((0, 1), repeat=len(oidx)):
                val = {}
                for j, i in enumerate(iidx): val[i] = ivals[j]
                for j, o in enumerate(oidx): val[o] = ovals[j]
                for fm, dst in h.edges.get(s, []):
                    if fm.eval(val):
                        opts.append((ovals, dst))
            table[(s, ivals)] = opts
    return table, iidx, oidx

def simulate(h, inputs, input_rows):
    """input_rows: list per input of list of 0/1 per step. Returns (defined, outputs[t][o])."""
    table, iidx, oidx = expand(h, inputs)
    n = len(input_rows[0]); s = h.start; outs = []
    for t in range(n):
        ivals = tuple(input_rows[r][t] for r in range(len(inputs)))
        opts = table[(s, ivals)]
        if len(opts) != 1: return (False, None)   # partial or nondeterministic
        ovals, s = opts[0]
        outs.append(ovals)
    return (True, outs)
