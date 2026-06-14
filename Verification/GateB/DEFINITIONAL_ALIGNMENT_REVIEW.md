# Definitional peer-review & alignment pass — cause definitions across the repo (2026-06-14)

**Trigger.** While building the multi-cell Credit game we found that *original/updated*
HP actual causes are never multi-cell on TRACE/TempoBench instances, yet the multi-cell
game grades the *modified* variant. Question raised: *did we define "cause" incorrectly
in main / main2 / mainTB, is the TempoBench-constrained frame wrong, or is it a different
issue?* This document records the review and every correction.

## Verdict (short)

**The definitions are not wrong.** `main`/`main2` (necessity/sufficiency, explicitly
disclaiming HP actual causation) and `mainTB` `Def. actual` (original/updated HP) and
`Def. determining`/`Def. valid` are each correctly stated legitimate objects. The
TempoBench-constrained frame correctly instantiates original/updated HP on a *flat*
trellis (all in-window cells exogenous, the only endogenous variable is the effect, no
intermediate `Z`).

The real issues were (a) **one unstated mathematical consequence** of that flattening,
(b) **one incorrect claim**, and (c) **a reconciliation gap** for the new modified-variant
game. All three are now fixed.

## Method

1. **SMT proof (z3)** that the unstated consequence is a theorem on the benchmark range:
   `Verification/GateB/verify_atomization.py` decides, for every window width `n=2..8`
   (the `MAX_WINDOW_CELLS=8` legibility cap → *every* admissible instance) and every
   cause-size `s≥2`, whether a minimal multi-cell original/updated cause can exist →
   **UNSAT everywhere**. Corroborated by exhaustive enumeration (`n≤4`) and random
   (`n=5,6`); the raw checker is self-tested equal to the Gate-A reference engine.
2. **Engine checks** of the per-puzzle variant keys (original / modified / determining)
   and `union(original)==union(determining)` on the five worked puzzles.
3. **Comprehensive audit** (multi-agent, adversarially verified) of all three papers, the
   pipeline `.py`, the game docs, the Gate records, and the HTML games against those facts.
   Clean (0 findings): `main.tex`, `main2.tex`, the pipeline code, the HTML game UI,
   `A2_definitional_note.md`, `A3_decision_record.md`. Findings concentrated in `mainTB.tex`
   and the game design docs.

## The load-bearing facts (machine-verified)

- **F1 — Atomization (THEOREM, SMT-proven for window ≤ 8 = full benchmark range).** Under
  `Def. actual` (original/updated), every subset-minimal actual cause on an (F2)–(F3)
  instance is a **singleton**. `Γ^ac` is a *union of singleton causes*, never an
  irreducible joint cause. This is the actual-causation analog of the paper's existing
  `Prop. pivotal` (count-only-necessity collapse).
- **F2 — Modified variant has multi-cell causes.** `engine.minimal_flip_sets` (subset-minimal
  joint flip, others at recorded) — CORP's discipline — yields P3 `{a@0,b@0}`, P5
  `{a@0,b@1}`, 3-OR a triple, etc. This is the *only* home of joint causes on the frame.
- **F3/F4 — Variant outputs.** P3: original `{a},{b}` · modified `{a,b}` · determining `{a},{b}`.
  P4: original `{req},{¬cancel}` · modified `{req},{¬cancel}` · determining `{req,¬cancel}`.
  So **modified distinguishes P3 from P4**; **original gives the same singleton shape for both**.

## Corrections made (exactly what changed)

### `tex_files/mainTB.tex` (compiles clean; `Prop. atomize` resolves)
1. **Added `Proposition prop:atomize`** (+ verification proof sketch) after the
   "which Halpern–Pearl" discussion: original/updated minimal causes are singletons,
   SMT-verified ≤ 8 cells; stated as the analog of `prop:pivotal`. *(was: unstated — C1/C2)*
2. **Fixed the backwards P3/P4 claim** (old lines 674–676). The old text said the *modified*
   variant "cannot distinguish two independently sufficient switches from two switches that
   act only jointly (Puzzle 4)." This is doubly backwards: modified *does* distinguish them,
   and it is *original/updated* that returns the same singleton shape for P3 and P4. Replaced
   with the correct per-cell-credit argument (original credits each overdetermining switch;
   modified collapses P3 to the joint pair) + the agreement on P4. *(was: error — C3)*
3. **`def:actual` parenthetical**: `Γ^ac` now noted to be exactly the set of single-cell
   causes under (F2)–(F3) (xref `prop:atomize`). *(C1)*
4. **Scoring (`sec:scoring`)**: the per-cell-union note "nor decompose into singleton causes"
   is now mode-qualified — true for Pin / modified Credit, false for original/updated Credit
   (always decomposes, `prop:atomize`); the witness bullet notes original Credit witnesses
   are always singletons. *(was: imprecise — C4)*
5. **Variant policy**: the playable-Credit paragraph now documents the *separate*
   `Credit·Joint` modified surface for TempoBench-alignment corpora, and notes (via
   `prop:atomize`) it is the only surface where a multi-cell cause can win. *(was: alignment gap — C5)*

### Game design docs
- `TRACE_game_design.md`: fixed the "multi-cell necessity… by theorem" table cell (impossible,
  not merely disallowed); fixed §20.10 "Credit is genuinely multi-cell" → multi-cell *union of
  singletons* by atomization; added forward pointer in §20.17 and a new **§20.18 (Iteration 14)**
  recording the atomization theorem and the `Credit·Joint` modified surface.
- `TRACE_implementation_spec.md` §4.2: CREDIT IT row reworded (singleton check is an invariant,
  not a filter); **added a CREDIT·JOINT row**; design-law L7 updated (modified = separate surface,
  not dual acceptance).
- `TRACE_puzzle_construction_proposal.md` §3.C: added the atomization remark; note (iii) now
  points to the built `Credit·Joint` surface (its anticipated "fourth, optional type").

### Decision record
- `Verification/GateA/A3_decision_record.md`: split the play-surface row into CREDIT IT
  (original/updated, reinforced by atomization) and **CREDIT·JOINT (modified, added 2026-06-14)**;
  marked the "requires a paper edit" item DONE.

### Code (already consistent — audit found 0; comments only)
- `build_modes.py` / `build_from_inputs.py`: the singleton assertion/gate documented as the
  now-proven `atomize` invariant (no behavior change).
- New: `verify_atomization.py` (SMT + enum proof), `build_joint.py`, `verify_joint.py`,
  `TRACE_credit_joint.html`.

## What was deliberately NOT changed

- **The canonical variant choice.** mainTB keeps original/updated as the credit-assignment
  core and modified for TempoBench-alignment (the dual-variant stance from `A3`/the variant
  policy). Atomization *strengthens* that stance (original gives clean per-cell singletons);
  switching the canonical variant is an authorial research decision, not a correctness fix.
- **`main.tex` / `main2.tex`.** Necessity/sufficiency framework, HP actual causation explicitly
  disclaimed; audited clean.
- **Conjecture corp** stays open (real per-cell keys not yet released) — A2(ii).
