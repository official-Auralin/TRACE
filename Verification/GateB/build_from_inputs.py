"""Arbitrary-input puzzle builder: (HOA, trace, effect[, mode]) rows in, the
three mode pages out — deterministically.

Input: JSONL rows in the TempoBench raw schema (hoa / trace / effects, with
optional explicit "mode"), or this repo's fixture names. Each instance is
classified by mode_assign (declaration wins; otherwise the versioned rule),
then emitted into TRACE_auto_stop/pin/credit.html using the same verified
templates as the curated pages.

Determinism guarantees, tested by verify_mode_assignment.py:
  D1 same inputs -> byte-identical pages (no timestamps, sorted keys,
     levels ordered by content hash of the instance, not input order);
  D2 input-order permutation -> identical pages;
  D3 classification is a pure function of the instance (stable across runs).

Quality gate (QUALITY_GATE_VERSION below; versioned like the mode assigner):
formal validity is not puzzle quality, so beyond render-equivalence every
instance must pass a deterministic mode-appropriateness + legibility check
before it is emitted as a human level. Rejections are logged with reasons;
the gate is a pure function of the instance, so build determinism holds."""
import json, hashlib, sys, os, glob
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "GateA"))
from hoa import HOA
from engine import Instance, pivots, minimal_actual_causes, determining_sets, sufficient
from build_player import build_graph, verify_equivalence
from a2_corp_compare import parse_trace
from mode_assign import assign_mode, MODE_ASSIGN_VERSION
import build_modes as BM

QUALITY_GATE_VERSION = "1.0"
# Legibility caps (proposal sec. C "Costs and risks" + implementation spec 5.3):
MAX_WINDOW_CELLS = 8     # any on-screen enumeration stays watchable (<=256 runs)
MAX_TESTS_PER_COLUMN = 4 # render fan-out cap (spec 5.3 suggested legibility cap)
MAX_CREDIT_DECIDERS = 3  # more accepted deciders than this = stumble-into-win

def quality_gate(inst, mode, nodes):
    """(ok, metrics, reasons). Deterministic; oracle-backed; versioned.
    Mode-appropriateness guarantees the level's win condition is reachable and
    every grader-correct answer is expressible by the mode's gesture."""
    reasons, m = [], {}
    tests = [n for n in nodes if n["kind"] == "test"]
    m["window_cells"] = len(inst.cells())
    m["testable_cells"] = len(set(tuple(n["cell"]) for n in tests))
    percol = {}
    for n in tests: percol[n["col"]] = percol.get(n["col"], 0) + 1
    m["max_tests_per_column"] = max(percol.values()) if percol else 0
    if m["window_cells"] > MAX_WINDOW_CELLS:
        reasons.append(f"window has {m['window_cells']} cells > {MAX_WINDOW_CELLS} (sweep unwatchable)")
    if m["max_tests_per_column"] > MAX_TESTS_PER_COLUMN:
        reasons.append(f"fan-out {m['max_tests_per_column']} > {MAX_TESTS_PER_COLUMN} (illegible column)")
    if m["testable_cells"] == 0:
        reasons.append("no testable cells")
    if mode == "stop":
        m["pivots"] = len(pivots(inst))        # 0 is fine: the o-slash tally is the win
    elif mode == "pin":
        dets = determining_sets(inst)
        m["determining_sets"] = len(dets)
        if not dets: reasons.append("pin level with no determining set")
        if sufficient(inst, []): reasons.append("empty lock sufficient (unconditional target)")
    elif mode == "credit":
        causes = minimal_actual_causes(inst)
        m["deciders"] = sum(1 for c in causes if len(c) == 1)
        if not causes: reasons.append("no actual causes")
        elif any(len(c) > 1 for c in causes):
            reasons.append("multi-cell minimal cause: human-inexpressible as a singleton claim")
        elif m["deciders"] > MAX_CREDIT_DECIDERS:
            reasons.append(f"{m['deciders']} deciders > {MAX_CREDIT_DECIDERS} (trial-and-error wins)")
    return (not reasons), m, reasons

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")

def row_to_instance(row):
    h = HOA(row["hoa"])
    assert h.controllable is not None, "row lacks controllable-AP"
    inputs = [a for i, a in enumerate(h.aps) if i not in h.controllable]
    eff = row["effects"][0]; k = eff.count("X"); out = eff.split()[-1]
    tv = parse_trace(row["trace"], h.aps, k + 1)
    obs = [[tv[t][a] for t in range(k + 1)] for a in inputs]
    return Instance(h, inputs, obs, out, k)

def instance_id(row):
    basis = json.dumps({"hoa": row["hoa"], "trace": row["trace"],
                        "effects": row["effects"]}, sort_keys=True)
    return hashlib.sha256(basis.encode()).hexdigest()[:10]

def main(paths):
    rows = []
    for p in paths:
        for ln in open(p):
            if ln.strip():
                r = json.loads(ln)
                if r.get("error") is None: rows.append(r)
    buckets = {"stop": [], "pin": [], "credit": []}
    log = []
    for row in rows:
        inst = row_to_instance(row)
        iid = instance_id(row)
        try:
            mode, why = assign_mode(inst, declared=row.get("mode"))
        except ValueError as e:
            log.append({"id": iid, "mode": None, "why": str(e)}); continue
        nodes, start = build_graph(inst)
        assert verify_equivalence(inst, nodes, start), f"render != HOA on {iid}"
        ok, metrics, reasons = quality_gate(inst, mode, nodes)
        if not ok:
            log.append({"id": iid, "mode": mode, "why": why, "quality": metrics,
                        "rejected": reasons}); continue
        buckets[mode].append((iid, {"name": iid[:6], "prov": f"auto · {why} · assigner v{MODE_ASSIGN_VERSION}",
                                    "k": inst.k, "inputs": inst.inputs, "obs": inst.obs,
                                    "nodes": nodes, "start": start}))
        log.append({"id": iid, "mode": mode, "why": why, "quality": metrics})
    goal = {"stop": BM.STOP_JS, "pin": BM.PIN_JS, "credit": BM.CREDIT_JS}
    texts = {"stop": ("STOP IT", "One throw. <b>Put the light out by flipping a single switch</b> — or finish the tally and say nothing alone can."),
             "pin": ("PIN IT", "<b>Lock switches so the light CANNOT go out</b> — the sweep verifies every completion before your eyes."),
             "credit": ("CREDIT IT", "<b>Make the light OBEY one switch:</b> claim it, build the bench, make it blink.")}
    shas = {}
    for mode, items in buckets.items():
        items.sort(key=lambda x: x[0])                      # content-hash order: input order irrelevant
        levels = [lv for _, lv in items]
        if not levels: continue
        html = BM.page(mode, texts[mode][0], texts[mode][1], goal[mode], levels,
                       f"Auto-built from raw instance inputs; mode assigner v{MODE_ASSIGN_VERSION}; "
                       f"quality gate v{QUALITY_GATE_VERSION} (mode-appropriateness + legibility).")
        path = os.path.join(ROOT, f"TRACE_auto_{mode}.html")
        open(path, "w").write(html)
        shas[mode] = hashlib.sha256(html.encode()).hexdigest()[:16]
    print(json.dumps({"assigner_version": MODE_ASSIGN_VERSION,
                      "quality_gate_version": QUALITY_GATE_VERSION,
                      "classified": log, "page_sha16": shas}, indent=1))
    return shas, log

if __name__ == "__main__":
    main(sys.argv[1:] or [os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "..", "GateA", "external", "tb_embedded_sample.jsonl")])
