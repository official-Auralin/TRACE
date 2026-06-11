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
