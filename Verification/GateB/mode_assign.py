"""Deterministic mode assignment for arbitrary instances.  VERSIONED: changing
this function changes which puzzle builds from the same inputs, so it carries a
version tag that corpora must declare (like the closeness order).

An instance's mode may be DECLARED in its input tuple (the paper's `mode`
field) — declaration always wins. When absent, assign_mode() derives it from
the certified key structure, total and deterministic on every instance that
survives the trivial-instance filter:

  RULE 1  no pivotal cell exists, but actual causes do (the effect is
          overdetermined — the class actual causation exists to handle)
          -> CREDIT
  RULE 2  otherwise, if every minimal determining set is a joint set
          (size >= 2: a guard, where sufficiency needs cooperation)
          -> PIN
  RULE 3  otherwise (a lone pivotal switch exists and single locks suffice)
          -> STOP

Rules are ordered; no ties are possible. Instances with no causes at all are
the trivial filter's discards and raise ValueError here by design."""
MODE_ASSIGN_VERSION = "1.0"

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "GateA"))
from engine import pivots, minimal_actual_causes, determining_sets

def assign_mode(inst, declared=None):
    if declared is not None:
        assert declared in ("stop", "pin", "credit"), declared
        return declared, "declared"
    ncells = len(inst.cells())
    piv = pivots(inst)
    causes = minimal_actual_causes(inst, max_size=ncells)
    if not causes:
        raise ValueError("trivial instance (no causes): excluded by the corpus filter")
    if not piv:
        return "credit", f"rule1: overdetermined (0 pivots, {len(causes)} actual causes)"
    dets = determining_sets(inst, max_size=ncells)
    if dets and min(len(d) for d in dets) >= 2:
        return "pin", f"rule2: joint guard (smallest determining set has {min(len(d) for d in dets)} cells)"
    return "stop", f"rule3: lone pivot exists ({len(piv)} pivot(s))"
