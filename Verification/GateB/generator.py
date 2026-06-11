"""B2 — Instance generator (mainTB production path P1-P6, synthesis-free variant).

P1/P2 are replaced for prototyping by direct sampling of random Mealy transducers
(F2/F3 hold BY CONSTRUCTION: delta and lambda are total functions), serialized to
HOA with named labels; P3 random trace; P4 effect selection; P5 keys certified by
the production grader; P6 packaging with difficulty stats and the trivial-instance
filter of mainTB sec. 'Difficulty knobs':
  discard if (a) no causal cells at all (input-unconditional target), or
  (b) the only minimal cause is a single literal in the effect column.
NOTE: corpus realism (SYNTCOMP/ltlsynt structure) is NOT claimed; this prototype
exercises the pipeline mechanics and statistics machinery only."""
import random, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "GateA"))
from hoa import HOA
from engine import Instance
from grader import keys

def random_mealy(n_states, inputs, outputs, rng):
    nI, nO = len(inputs), len(outputs)
    aps = outputs + inputs                      # outputs first (TempoBench style)
    delta, lam = {}, {}
    for s in range(n_states):
        for iv in range(2 ** nI):
            delta[(s, iv)] = rng.randrange(n_states)
            lam[(s, iv)] = rng.randrange(2 ** nO)
    lines = ["HOA: v1", f"States: {n_states}", "Start: 0",
             f'AP: {len(aps)} ' + " ".join(f'"{a}"' for a in aps),
             "controllable-AP: " + " ".join(str(i) for i in range(nO)),
             "Acceptance: 0 t", "--BODY--"]
    for s in range(n_states):
        lines.append(f"State: {s}")
        for iv in range(2 ** nI):
            lits = []
            for j, o in enumerate(outputs):
                lits.append(o if (lam[(s, iv)] >> j) & 1 else "!" + o)
            for j, i in enumerate(inputs):
                lits.append(i if (iv >> j) & 1 else "!" + i)
            lines.append("[" + " & ".join(lits) + f"] {delta[(s, iv)]}")
    lines += ["--END--", ""]
    return "\n".join(lines)

def sample_instance(rng, n_states, n_inputs, k):
    inputs = [f"i{j}" for j in range(n_inputs)]
    out = "o"
    text = random_mealy(n_states, inputs, [out], rng)
    h = HOA(text)
    for _ in range(40):                        # find a trace with the effect at k
        obs = [[rng.randrange(2) for _ in range(k + 1)] for _ in inputs]
        try: inst = Instance(h, inputs, obs, out, k)
        except AssertionError: continue
        return text, inst
    return None, None

def transition_count(h):
    return sum(len(v) for v in h.edges.values())

def classify(inst, K):
    """trivial-filter + stats per mainTB difficulty features."""
    causes = K["credit_original"]
    cause_cells = set(c for m in causes for c in m)
    if not causes: return "discard:input-unconditional", cause_cells
    same_col = [m for m in causes if len(m) == 1 and m[0][1] == inst.k]
    if len(causes) == len(same_col): return "discard:same-column-single-literal", cause_cells
    return "retain", cause_cells
