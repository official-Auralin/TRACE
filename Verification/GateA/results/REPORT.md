# Gate A — Results Report

Run: 2026-06-12T21:36:57.062930  ·  Python 3.10.12

| Gate | Test | Status | Exit |
|---|---|---|---|
| A1 | `a1_audit.py` | PASS | 0 |
| A2i | `a2_oracle_check.py` | PASS | 0 |
| A2ii | `a2_corp_compare.py` | MEASURED(n=1) | 0 |
| A3 | `a3_variants.py` | PASS | 0 |
| A4 | `a4_window.py` | PASS | 0 |

## Pass/fail conditions (see README.md)
- A1: PASS iff every labelled fixture (1 positive, 4 negative controls) is classified
  correctly on all of F1-operational/F2/F3. External corpus rates reported when present.
- A2i: PASS iff oracle output == mainTB's published answers, 5 puzzles x 4 causal objects.
- A2ii: PASS only on real TempoBench keys; otherwise BLOCKED-EXTERNAL (recorded).
- A3: PASS iff variants agree exactly on non-overdetermined puzzles, diverge to the
  joint pair on overdetermined ones, and dual-acceptance = union with no supersets.
- A4: PASS iff same-step relevance detector flags exactly P4; Mealy rendering covers
  all cause cells; Moore coverage holds iff Moore-safe.

Evidence documents: A2_definitional_note.md, A3_decision_record.md.
