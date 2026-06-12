# Gate B Verification Suite (TRACE_validation_plan.md, Gate B)

Depends on `../GateA` (validated parser, reference oracle, fixtures, real artifact).
Chunked execution (sandbox time limits): `python3 b2_corpus.py 0..5` then `agg`;
`python3 b1_profile.py 0..10` then `agg`; everything else via `python3 run_all.py`.

| File | What it proves | PASS condition |
|---|---|---|
| `grader.py` | production grader: oracle+minimality for prevent (implemented directly from Def. valid via closest-removal search), credit original/modified (witness & union), pin | n/a (library) |
| `b1_regression.py` | grader == validated reference on the 5 worked puzzles + real TempoBench instance; **Prop. pivotal checked against the raw definition** (accepted Def.-valid singletons == pivot set, no-pivot verdict iff empty); witnesses accepted / supersets rejected | R1 ∧ R2 ∧ R3 on all instances |
| `b1_profile.py` | published tractable (|I|,k) envelope per mode; exponential Credit cost exhibited as predicted | every grid point measured; superpolynomial Credit growth |
| `generator.py` + `b2_corpus.py` | pipeline P1-P6 prototype (random Mealy, F2/F3 by construction), trivial filter, corpus statistics incl. no-pivot split, Credit-vs-Pin equality, variant divergence | >=100 retained, all pass audit, totals consistent |
| `b3_identifiability.py` | black-box admission check (exhaustive within a declared device family, one-sided budget guarantee), controls + admission rate | both controls correct |
| `render.py` | shared junction-graph render core (Shannon decomposition, Mealy edge-rendering) + `verify_equivalence` (board == HOA on every window setting) | n/a (library; builders abort on divergence) |
| `build_modes.py` | builds the canonical mode pages `TRACE_stop/pin/credit.html` (no embedded keys) with per-level oracle cross-checks incl. credit expressibility (all minimal causes singletons) | cross-checks pass per level |
| `mode_assign.py` + `build_from_inputs.py` | deterministic mode assignment (v1.0) + quality gate (v1.0: mode-appropriateness, window <= 8 cells, fan-out <= 4, credit 1-3 deciders) building `TRACE_auto_*.html` from raw rows | render==HOA per level; rejections logged with reasons |
| `gold_inputs.py` | the gold-12 coverage set (P1-P5, TB, seed-23 G1-G6 — the retired build's twelve instances) regenerated deterministically as raw rows | byte-identical regeneration (D0) |
| `verify_modes.py` | live JS verdict semantics == oracle for EVERY possible player action, on curated AND gold-12 auto pages; every gold-12 input emitted+verified or rejected-with-reason | all checks + full coverage |
| `verify_mode_assignment.py` | gold placement (P3,P5->credit; P4->pin; P1,P2,TB->stop), assigner purity/totality, declaration-wins, byte-determinism over gold-12 (same inputs / reversed order) | A1-A3, D0-D2 |
| `runtime_smoke.js` | every level of every emitted page (curated + auto) renders non-empty recording and bench SVG in a DOM stub | no empty render, no runtime error |

## Honest limitations
1. Corpus realism not claimed: random Mealy transducers, not SYNTCOMP/ltlsynt syntheses;
   all corpus statistics are machinery-validation numbers, to be recomputed on real artifacts.
2. Profiling uses the exhaustive reference algorithms; production constants can improve,
   but the Credit exponential in |I|*k is structural (mainTB cost analysis), and the
   envelope is what the verifiable-reward claim is restricted to today.
3. b3's identifiability is exhaustive only within the declared family (<=2 states here);
   verdicts are family-relative, with the one-sided budget guarantee recorded in output.
4. Discovered during B2 and now a standing rule: search caps censor keys and corrupt
   corpus statistics (49 phantom divergences at cap 3 vs 0 at full depth) — caps must be
   lifted or certified per instance.
