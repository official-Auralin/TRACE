# Gate C Verification Suite (TRACE_validation_plan.md, Gate C)

`python3 run_all.py` → results/REPORT.md. Depends on ../GateA and ../GateB.

- `c1_parity.py` — the four-consumer parity audit (P-OBS, P-SUB, P-PRB, P-CAND);
  PASS iff all four properties hold on all 9 instances. P-SUB is exhaustive over
  every submission the board can produce; P-CAND proves human-unreachable cells
  are effect-irrelevant in every context (the agent's larger nominal answer
  space adds only wrong answers — the parity-relevant direction).
- `C2_whitebox_budget_decision.md` — the budget policy per consumer, retaining the
  paper's budgeted-white-box construct as a calibration arm rather than amending it.
- `C3_modality_protocol.md` + `c3_materials.py` — the 2×2 spatial/textual design
  controlling mainTB's modality caveat, with agent observations emitted from the
  same instances the human board renders (equivalence covered by c1).

Limitations: P-PRB samples 20 random probes per instance (the full space is
covered by P-OBS's exhaustive behavioral check; the sampling is only about the
probe *interface*); board-image rendering for the A-board arm reuses the
playable build and is not yet automated into image files.
