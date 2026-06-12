# Gate C — Results Report

Run: 2026-06-12T20:57:04.188068 · Python 3.10.12

| Item | Status |
|---|---|
| C1 four-consumer parity audit | PASS |
| C2 white-box budget | DECIDED (C2_whitebox_budget_decision.md) |
| C3 modality protocol + materials | EMITTED — emitted 6 agent observations to materials/ |

C1 checks, per instance (9 instances: 5 worked puzzles, the real TempoBench
artifact, 3 generated): observation equivalence (board is a pure function of the
agent observation AND behaviorally identical on every assignment); submission
round-trip (every possible board submission ↔ agent JSON, identical verdicts —
exhaustive, and checked PER DECLARED VARIANT POLICY: original, modified, and the
legacy dual union, so the parity proven is the parity each shipped corpus grades
under); probe parity (board walk == HOA simulation on random probes);
candidate-space safety (every human-unreachable cell proven effect-irrelevant in
every context, so no correct answer is human-inexpressible). Candidate-space
safety (P_CAND) is release-blocking: future generator changes must keep it green.
