# Proposal: Constructing TRACE Puzzles Without Hidden Objectives

*A reviewer-grade rethink of the puzzle construction, written after reverting the
insight-layer patch. Status: **ADOPTED AND IMPLEMENTED** — construction C (Visible
Verification) with B's demonstration gesture as the Credit mode is the canonical
human game: `TRACE_stop.html` / `TRACE_pin.html` / `TRACE_credit.html`, built by
`Verification/GateB/build_modes.py`, semantics proven equal to the oracle for every
possible player action by `verify_modes.py`; arbitrary-input builds via
`build_from_inputs.py` (deterministic mode assignment §5 + versioned quality gate).
The dual-acceptance single-board build (`TRACE_play.html`) is retained only as a
labeled sandbox/archive and pilot-comparison arm; its hidden-objective defect is
stated on the page itself. The implementation spec §5.0 records the construction.*

---

## 1. The diagnosis: where hidden objectives enter the pipeline

Walk the pipeline as a reviewer and ask, at each stage, "can the player see what
is being asked and whether they've done it?"

**1.1 The root mismatch: epistemic objects on an operational board.**
Every causal object the benchmark grades — actual cause, extinguishing set,
determining set, pivotal cell — is an *epistemic claim about the recorded run*,
defined by quantification over counterfactuals (∃ contingency, ∀ closest
removals, ∀ completions). A game win, by contrast, is *operational*: a state the
player reaches and can see. Our construction has tried, in every iteration, to
encode an epistemic claim as a board state (diff-as-answer). The encoding must
leak, because a claim quantified over runs the player has not made cannot be a
property of the one run on the board. The grader's quantifier **is** the hidden
objective. The lit-bulb decider is just its most visible symptom.

**1.2 The two-worlds conflation.** One board serves as both the *recording*
(the world the question is about) and the *scratchpad* (the world the player
manipulates). The claim refers to the recording; the demonstration happens on
the scratchpad; the submission is read off the scratchpad as if it were a
statement about the recording. The player is never shown which world they are
being graded in. This is a construction defect independent of variant choice.

**1.3 The implicit question.** The paper defines three modes with plain verbs
(*Prevent / Credit / Pin*) and prices their quantifiers explicitly ("the
grader's quantifiers — finite checks over the same frozen device"). Iteration 7
collapsed play to a single implicit Credit question; iterations 11–12 then
widened *acceptance* (any witness, either variant) without widening the visible
*question*. Result: the question on screen ("throw what decided the light") and
the predicate in the grader (witness under either HP reading) are different
objects. Multiple-solution types with invisible results follow necessarily.

**1.4 Minimality is also hidden.** Even in the all-dark construction, "no
proper subset would do" is an ∃-claim the player cannot see. Every prior fix
ignored this second hidden quantifier.

**Conclusion of the diagnosis:** patching acceptance policies cannot fix this.
The construction itself must make every quantifier in the win condition either
(a) the player's own exhibited object, or (b) a finite, *watchable* check whose
outcome is shown as runs on the board. Nothing else may be graded.

---

## 2. Requirements for a no-hidden-objective construction

R1. **One declared question per puzzle**, stated in the mode's plain verb, with
    the win condition decidable by looking at the board(s) after the verdict.
R2. **Two worlds, visibly distinct:** the recording is immutable and always on
    screen; experiments happen in a scratch world. Claims are *about* the
    recording; the UI must show which world every element belongs to.
R3. **Every quantifier is discharged on-screen:** acceptance ends with a
    visibly completed enumeration; rejection ends with a *counterexample run
    left on the board*. No verdict without its witness.
R4. **Minimality is taught by counterexample too:** a non-minimal submission is
    answered with the smaller sufficient sub-claim, shown as a run.
R5. **Agent parity untouched:** the benchmark protocol, oracle, and metrics do
    not change; this is a construction of the *human surface* over the same
    instances and grader.

---

## 3. Candidate constructions

### A. Single-reading, extinguish-only (the reverted patch, as baseline)
Win = subset-minimal set of throws that darkens the bulb. Visible result, yes —
but the *minimality* quantifier stays hidden (R4 unmet), the original-variant
core object vanishes from play entirely, and the fix is an acceptance policy,
not a construction. **Rejected as insufficient** (and by playtest direction).

### B. Demonstration-as-goal ("make this switch the decider")
Each puzzle designates a candidate cell and asks the player to *build the
contingency*: arrange the other switches so that the designated switch visibly
toggles the bulb (a wiggle interaction: hold the junction, bulb blinks with
it). The win is the player's own exhibited AC2(a) pair-of-runs — the spec's own
demonstration form — so the central quantifier (∃ contingency) is discharged by
the player, on-screen, as the goal itself.
- Faithful: the win object is literally the paper's "pair of runs under that
  setting"; the checker verifies AC2(b) robustness silently and *shows the
  failing subset-reset run* if it rejects (R3).
- Honest limits: designating the candidate changes the task from "find the
  cause" to "prove this is a cause" — a different (constructive-proof) skill,
  closer to the benchmark's witness *verification* than its search. Strong as a
  mode; wrong as the only mode.

### C. Visible Verification (recommended)
Keep the paper's three modes as three explicit puzzle types, restore the
two-world board, and surface every grader quantifier as a watchable finite
check with counterexample verdicts:

- **Board:** top strip = the recording (frozen, lit path and flash shown);
  main area = the scratch world. The claim chips always name recording cells.
- **STOP IT (Prevent):** "stop the light with ONE throw." Win is visible
  (dark on your throw). The ⊘ verdict becomes *enumerable*: the board keeps a
  visible tally of single throws tried (each junction dims its ✂ tag once its
  lone flip has been seen to fail); ⊘ unlocks only when the tally is complete.
  The ∀ behind ⊘ is finite and small — the player literally finishes it.
- **PIN IT (Pin):** "lock switches so the light cannot go out." On submit, the
  verifier *visibly* sweeps the unlocked switches (fast replay of completions);
  rejection halts at the counterexample completion, left on the board;
  acceptance ends with the sweep exhausted — a progress ring over the finite
  completion space. The ∀ is watched, not trusted.
- **CREDIT IT (Credit):** "show me a switch that truly decided it." Two-step
  gesture matching Def. actual: (1) build a contingency in the scratch world;
  (2) wiggle your candidate — bulb must blink with it. Submission = (candidate,
  exhibited contingency). The checker's only silent work, AC2(b) robustness, is
  verdict-visible: rejection replays the subset-reset run that kills the
  effect (R3). Minimality (AC3): rejection replays the sub-candidate's own
  demonstration (R4).
- **Verdict grammar (all modes):** ACCEPT = "checks complete" with the
  enumeration/progress shown; REJECT = a single concrete run, on the board,
  that defeats the claim. No bare "not quite" anywhere.

Faithfulness notes. (i) The sweeps and replays are the grader's finite checks
of mainTB §groundtruth, animated — the spec already insists the quantifiers are
"finite checks over the same frozen device," and explicitly distinguishes this
from the excluded live adversary; nothing strategic is added. (ii) The three
modes are the paper's own benchmark configurations, restored to the surface
instead of collapsed. (iii) The HP-variant question dissolves at the surface:
Credit puzzles ask for a *demonstrated* decider (the original-variant object,
now with a visible win); extinguishing sets are not a Credit answer and never
collide with it — they are simply how multi-throw STOP-style play would be
posed if a corpus wants it (a fourth, optional type: "darken with the fewest
throws," graded modified, fully visible). (iv) Agent protocol unchanged (R5);
the agent's Credit submission may carry its contingency, which the schema
already supports as probe pairs.

Costs and risks. Verification sweeps must stay watchable: fine within the
profiled envelope (≤8 window cells ⇒ ≤256 completions; sample-then-counterexample
display beyond). Two-world layout costs vertical space on mobile. The Credit
two-step gesture needs onboarding (the wiggle is new). Generation must declare
mode per instance and filter for mode-appropriateness (e.g., STOP puzzles need a
pivot or a completable ⊘ tally — both already computed by the oracle).

### D. Constructive play (build a run meeting causal constraints)
Operational and visible, but it changes the task from explaining a given trace
to synthesizing one — outside TCE. **Rejected for the core; usable as tutorial.**

---

## 4. Recommendation and decision ask

Adopt **C (Visible Verification)** as the construction, with **B's
demonstration gesture as C's Credit mode** (they compose: B is C's third
panel). Decision points for sign-off before any implementation:

1. Approve the two-world board (recording strip + scratch world).
2. Approve the three visible mode types (+ optional fewest-throws type) as the
   level grammar, replacing the single implicit question.
3. Approve verdict grammar: counterexample-run rejections, enumeration-complete
   acceptances, everywhere (this retires "Not quite," PROVE IT, and any
   post-hoc explanation layer — the verification IS the explanation).
4. Sequencing: prototype on the existing 12 verified instances (each already
   carries oracle keys for all three modes); parity suite re-run; then the
   pilot protocol picks up the mode-explicit design.

If approved, the implementation plan is: extend the instance schema with
`mode`, build the verdict-replay engine on top of the existing oracle
(counterexamples are already computed — they are currently discarded), and
re-skin the player as the two-world board. Estimated as one focused iteration;
no changes to engine, oracle, generator mathematics, or agent protocol.

---

## 5. Addendum (implemented): deterministic mode assignment for arbitrary inputs

With three explicit puzzle types, "which puzzle builds?" must be reproducible.
Two layers, both implemented and machine-verified (`Verification/GateB/mode_assign.py`,
`build_from_inputs.py`, `verify_mode_assignment.py`):

1. **Mode is normally declared input** — part of the instance tuple, like the
   effect selection; declaration always wins.
2. **When undeclared, a versioned pure function of the certified keys assigns it**
   (assigner v1.0, ordered and tie-free): overdetermined → CREDIT; joint guard →
   PIN; lone pivot → STOP. Total on trivial-filter survivors.

Verified: the five worked puzzles and the TempoBench artifact classify to their
pedagogically defining modes; classification is pure (identical on re-parsed
copies); auto-built pages are byte-identical across repeated runs and across
input-order permutations (levels are ordered by instance content hash, never by
arrival order). Measured note: random 3-state transducers skew heavily toward
PIN under v1.0 (33/40 in the sample) because joint guards are common in random
machines — corpus stratification should balance modes by selection, not by
bending the rule; any rule change is a version bump that corpora must declare.
