# Gate B — Results Report

Run: 2026-06-12T20:57:01.140146 · Python 3.10.12 (sandboxed Linux)

| Test | Status |
|---|---|
| B1 regression | PASS |
| B1 profiling | PASS |
| B2 corpus | PASS |
| B3 identifiability | PASS |

## Headline measurements
- Tractable grader envelope (median per full key computation): <=1s at (|I|,k) in [[1, 1], [1, 2], [1, 3], [1, 4], [1, 5], [2, 1], [2, 2], [2, 3], [3, 1]]; <=10s adds [[2, 4], [3, 2]]. Credit-original cost is the exponential one, as mainTB's cost analysis predicts (growth ratios [7.0, 1.86, 1.0, 2.93, 1.31, 21.92, 3.16]).
- Prototype corpus: 139 generated, 107 retained (discard rate 23%: 4 input-unconditional, 28 same-column single-literal).
- No-pivotal-cell verdicts: 11 overdetermined (retained class) vs 4 input-unconditional (discarded).
- Credit-vs-Pin per-cell unions agree on 107/107 retained instances (zero divergences at full search depth) — empirical support for the per-cell equality mainTB leaves open. NOTE: with a size-3 search cap this statistic falsely showed 49 divergences; cap-censoring corrupts keys, validating the 'lift caps or certify per instance' requirement.
- Original-vs-modified HP variant keys diverge on 63/107 retained instances (~59%) — the class where the CORP correspondence is predicted to fail is common on random machines.
- Black-box identifiability: controls pass (known-identifiable accepted, observed-run-only refused); random 2-state/1-input instances with 3 probes: 0/10 admitted — the admission check is severely restrictive, as mainTB anticipated.

Caveat: corpus realism is NOT claimed (random Mealy machines, not SYNTCOMP syntheses); statistics demonstrate the machinery and bound expectations only.
