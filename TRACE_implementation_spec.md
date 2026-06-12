# TRACE — Implementation Specification for Scalable Builds

*Consolidates every mechanic, interaction law, grading policy, and verification requirement settled during the 12-iteration demo process (see `TRACE_game_design.md` §20) and the mode-explicit reconstruction that followed it (`TRACE_puzzle_construction_proposal.md`, adopted). This spec is authoritative for the production builds: human game (white-box and black-box), agent harness, and shared grader. Source of truth for semantics: `tex_files/mainTB.tex` (cited by section throughout).*

**Canonical artifacts (one authority per consumer; nothing hand-built ships).** The canonical human game is the **mode-explicit, live-verdict pages** `TRACE_stop.html` / `TRACE_pin.html` / `TRACE_credit.html` (built and cross-checked by `Verification/GateB/build_modes.py`; semantics proven equal to the oracle by `verify_modes.py`). They expose the paper's three modes (mainTB §modes) under the paper's verbs — STOP IT = *Prevent*, PIN IT = *Pin*, CREDIT IT = *Credit* — and embed **no answer key**: every verdict is computed on screen by running the build-verified board, every quantifier discharged visibly (tally / sweep / counterexample replay). The **auto pages** `TRACE_auto_stop/pin/credit.html` are built deterministically from raw instance rows by `build_from_inputs.py` (mode assigner + quality gate); the canonical input set is **gold-12** (`Verification/GateB/results/gold12.jsonl` — the five worked puzzles, the TempoBench artifact, and the six seed-23 generated instances), and `verify_modes.py` PASSES only if every gold-12 input is either emitted-and-oracle-verified or rejected with a logged reason. Earlier hand-built or single-question builds (mockup, dual-acceptance `TRACE_play.html`, its template) are **removed**; git history preserves them. `index.html` lands on the mode pages.

---

## 1. System overview

Three consumers, one engine, one grader:

```
 SYNTCOMP/TLSF ─ltlsynt→ A_HOA ─HOAX→ trace τ ─select→ effect X^k o      (pipeline P1–P4)
                                │
                       ┌────────┴────────┐
                       │  INSTANCE (JSON) │←─ ground-truth oracle V + key Γ (P5–P6)
                       └────────┬────────┘
        ┌───────────────┬───────┴──────────┬──────────────────┐
   Human white-box   Human black-box   Agent white-box   Agent black-box
   (live board)      (budgeted probes) (HOA + JSON)      (probes + JSON)
                       └───────── one GRADER (native predicate) ─────────┘
```

**Parity invariant (non-negotiable):** within a track, human and agent receive the same information, the same probe affordance, and are graded by the same checker on the same answer format (mainTB §Agent: "Parity is the point"). Every build feature below states its parity image.

---

## 2. Device engine

### 2.1 Canonical model
- Input: `A_HOA` (HOA format, symbolic transition labels), AP partition `I`/`O`.
- One-time **explicit expansion** per instance: `O(|Q|·2^|I|)` edges (mainTB §groundtruth cost analysis). All complexity statements are against the expanded graph; `|I|` is capped by the difficulty knobs.
- Semantics: behavior-set/transducer reading; admissible = run-defined (F=Q ignored). Under (F2) each input sequence has exactly one completion; `out(g)` is computed by simulation.
- **Assumptions consumed:** (F1) implementation-not-monitor, (F2) input-determinism, (F3) input-totality. The engine MUST refuse (or quarantine) artifacts failing the V1 audit (see validation plan); it must not silently patch them.

### 2.2 Renderable form: the junction graph (white-box board)
The board is generated from the expanded automaton by **Shannon decomposition** of each state's transition function into a chain/tree of one-input tests:

- Node kinds: `test {cell:(i,t), out1, out0}` · `pass {next}` · `bulb` (effect terminal) · `ground` (non-effect terminal) · `merge` (cosmetic).
- **One lamp:** all flash-states' tracks converge into a single bulb terminal for the selected output `o` at column `k`. Multi-output instances render one bulb per relevant output, only the target ringed (▼).
- Variable ordering per state chosen by the generator to minimize junction count (BDD-style reduction); equal-target branches collapse (irrelevant inputs disappear unless retained deliberately as decoy forks — §5.3).
- **Structural invariants, machine-checked at generation** (demo harness, to be ported): every route terminates at a terminal under *all* `2^(|I|·(n+1))` settings (totality); simultaneously-satisfiable branches share a target (determinism); every cell of the certified key is testable at some junction; declared decoys present.
- **Equivalence obligation:** `route_junctionGraph(g) ⊨ out(g) = simulate_HOA(g)` for all settings (exhaustive on small windows; randomized + symbolic check at scale). The picture IS the mechanics — render divergence is a build-breaking bug class (design law L1, §7).

### 2.3 Mealy outputs (RESOLVED — option (a) shipped)
The demo's junction graph was Moore-style (bulb depending on inputs `0..k−1` only) while the formal candidate window is `0..k`. Production adopted option (a), **Mealy edge-rendering**: the shared render core (`Verification/GateB/render.py`) renders the output on the edge entering column `k`, so moment-`k` cells are drawn and testable wherever the device reads them (e.g. the TB arbiter's `(r,3)` junction). Residual safety is machine-checked per instance by Gate C's **P_CAND**: every cell not testable on the board is proven effect-irrelevant in every context, so no correct answer is human-inexpressible and the agent's larger nominal space adds only wrong answers. This invariant is release-blocking: any future generator change must keep P_CAND green (CI gate, §8).

---

## 3. Instance schema

Extends mainTB Appendix "Interface Schema" with the render layout. One JSON per instance:

```jsonc
{
  "id": "syntcomp-arbiter3-t017-k4-credit",
  "apc": {"inputs": ["..."], "outputs": ["..."]},
  "machine": "<HOA text>",            // omitted in black-box observations
  "run": [{"t":0, "...inputs/outputs...": 0}],
  "target": {"output": "o", "step": 4},
  "window": [0, 4],
  "task": {"object": "credit", "variant": "witness"},   // see §4
  "hp_variant_policy": "original",     // ONE declared variant per corpus: "original" | "modified" (A3 decision record)
  "budgets": {"probes": null, "attempts": 2},           // probes: null=∞ (white-box human), int otherwise
  "difficulty": {"k":4, "states":9, "transitions":31, "causal_cells":2,
                 "trace_diversity":3, "n":6, "max_fanout":4},
  "layout": {"nodes":[...], "tracks":[...]},            // junction graph, generator-emitted
  "oracle_ref": "key.bin"             // validity oracle + canonical key (never shipped to solver)
}
```

- The **answer key is the oracle, not a string** (mainTB §groundtruth: "certify with the oracle"). Canonical Γ shipped only for TS/AP granularities.
- **Mode determinism.** `task.object` is part of the input tuple (like the effect selection); declaration always wins. When absent, the mode is derived by the **versioned assigner** (`mode_assign.py`, v1.0), a pure function of the certified keys with ordered, tie-free rules: (1) overdetermined (no pivot, actual causes exist) → credit; (2) joint guard (smallest determining set ≥ 2 cells) → pin; (3) otherwise → stop. Total on trivial-filter survivors. Verified: gold instances land in their defining modes (P3,P5→credit; P4→pin; P1,P2,TB→stop); classification is pure; auto-built pages are byte-identical across runs and input orderings (`verify_mode_assignment.py`). Changing the assigner version changes which puzzle builds — corpora must declare it, exactly like the closeness order.
- `layout` is presentation: the grader never reads it; the equivalence check (§2.2) binds it to `machine`.

---

## 4. Grading module (shared by all four consumers)

### 4.1 Objects (from mainTB §two-questions, §scoring)
- **Credit** (core): HP actual cause — AC1 actuality; AC2(a) necessity under contingency (W may be non-actual); AC2(b) robust survival (all subset-resets of W); AC3 subset-minimality. Implemented set-valued (demo `satisfiesAC2`/`isMinimalCause` generalizes singletons → sets).
- **Modified-variant reading** (exogenous collapse): subset-minimal joint flip, others at actual (`isMinimalFlip`).
- **Prevent** (diagnostic): singleton pivotality or the no-pivotal-cell verdict (Prop. pivotal). Not in human play loop; retained as benchmark configuration TRACE-Prevent.
- **Pin** (diagnostic/dual): subset-minimal determining set (non-emptiness check per candidate). Benchmark configuration TRACE-Pin; candidate future human mode (padlock gesture, unprototyped).

### 4.2 Task variants and policies (revised on adopting the mode-explicit construction)
| Consumer | Task | Acceptance |
|---|---|---|
| Human game — STOP IT | Prevent | single throw that darkens (Def. valid via Prop. pivotal), or the ⊘ verdict earned by the player's own complete tally. No variant question arises. |
| Human game — PIN IT | Pin (witness) | locked set survives the on-screen sweep of **every** completion ∧ no single lock removable (minimality, also swept visibly). No variant question arises. |
| Human game — CREDIT IT | Credit (witness, demonstrated) | the player's own exhibited contingency pair-of-runs: bulb on with the claimed switch as recorded, off when flipped, robust under every subset-reset of the bench to the recording (AC2(b), counterexample replayed on failure). **This is the original/updated HP object only** — the variant ambiguity is dissolved at the surface, not split: extinguishing sets are not a CREDIT answer. Levels admit only instances whose minimal causes are all singletons (expressibility check, `build_modes.py`). |
| Agent benchmark, primary | witness OR per-cell union (declared per corpus) | **single declared `hp_variant` per corpus**: `modified` for TempoBench-alignment corpora (CORP's own discipline, A3 decision record), `original` for the credit-assignment stance (mainTB's core object). Human results in a calibrated comparison are graded under the same declared variant. |
| Agent leaderboards | TS / AP granularities | canonical key (lexicographically least), per mainTB §scoring |

- Parity scope: the "same game" claim is made **within a declared (track, variant)**; the Gate C parity audit checks the submission round-trip under `original`, `modified`, and the legacy union separately (`c1_parity.py` P-SUB).

- Minimality test: ≤ `2^|Γ|` oracle calls; minimal causes are small (mainTB).
- **Failure feedback tiers (human):** (i) superset of an acceptable witness → "a smaller claim is hiding in yours"; (ii) otherwise → neutral "not quite". Never reveal cells. Attempts (♥) per the spec's attempt rule; solved iff any attempt earns full native credit.
- Complexity envelope: necessity/sufficiency polynomial in expanded `|A|,k`; Credit exponential in `|I|·k` (contingency search) — generation-side cost, bounded by knobs; profile per V3.

### 4.3 Submission format (parity)
Human board state and agent JSON are the same object:
- Human: thrown junctions ⇒ `{ "cause": { "t": {"input": observed_value} } }` (cells at actual values; grader supplies flips — mainTB §agent).
- Prevent config: `pivot` / `no_pivot:true`. Pin config: `lock`.

---

## 5. Human game build (TRACE)

### 5.0 Mode-explicit construction (adopted from the puzzle-construction proposal)
The human game is **three explicit puzzle pages**, one per mainTB mode, on a **two-world board**: a frozen RECORDING strip (the run the question is about) above a live BENCH (the scratch world the player manipulates). Every grader quantifier is discharged on screen — no page embeds an answer key:

| Page | Mode (paper verb) | Gesture | Visible quantifier discharge |
|---|---|---|---|
| `TRACE_stop.html` | Prevent | tap = one lone throw against the recording | win = dark on your throw; the ⊘ (no-pivotal-cell) verdict unlocks only when the player's own tally has tried **every** single throw |
| `TRACE_pin.html` | Pin | lock switches; RUN THE SWEEP | acceptance = the sweep visibly exhausts every completion; rejection = the leaking completion left on the bench; minimality = removable-lock counterexample shown |
| `TRACE_credit.html` | Credit (core) | claim a switch (★), set the bench, MAKE IT BLINK | the player's own exhibited AC2 pair-of-runs; AC2(b) robustness checked with the failing subset-reset left on the bench; AC3 trivial for singleton claims |

Verdict grammar (all modes): ACCEPT = enumeration/sweep visibly complete; REJECT = one concrete counterexample run left on the board. No bare "not quite".

### 5.1 Board ontology (iteration 9–12 core, extended by the mode surfaces; no other object kinds permitted)
| Object | Visual | Interaction | Meaning |
|---|---|---|---|
| Junction | small circle; the lever IS the node | tap = throw (toggle its cell); tap a branch = align onto that branch | input cell test |
| Track | curve; **aligned** = connected full-strength; **unaligned** = gap at junction + dimmed | (branch tap only) | transition under one value |
| Live route | single gold flow animation from entry | — | the current run |
| Bulb (one) | lit (glow+rays) / dark, **live** in white-box | — | effect `o@k`; ▼ marks column k |
| Ground stub | dim ⏚ | — | non-effect terminal |
| Blue ring | around thrown junctions | — | diff from recorded = the claim |
| Linked tint | shared color across junctions testing the same cell; thrown together | — | one cell, several states (only when present) |
| ♥ / ↺ / SUBMIT / chips / Δ | HUD | — | attempts, reset (free), submit, claim list |
| Recording strip | dashed-border miniature of the observed run (frozen) | — | the world the claim is about (two-worlds rule, R2 of the proposal) |
| ★ claim tag | gold star over a junction (CREDIT IT) | tap = claim that cell as the decider | the candidate of Def. actual |
| Lock ring | blue ring (PIN IT) | tap = lock/unlock at recorded value | membership in the submitted determining set |
| ✂ tally tag | dims once that lone throw has been seen to fail (STOP IT) | tap = run that single-throw experiment | progress of the player's ∀-tally toward ⊘ |
| Sweep bar | gold progress bar (PIN IT) | — | the grader's ∀-completions check, watched |

Text budget: one objective sentence per mode page, feedback cards that name a concrete counterexample run, numerals. Nothing else.

### 5.2 Tracks
- **White-box:** full junction graph visible; board simulates live (route + bulb). No probe budget (β=∞): the device is shipped, eye-simulation is the intended skill (β=0 regime is the mastery framing). Scored resource: attempts. **Reported as its own condition**: live-board human play is a declared regime (the human analog of the code-equipped agent regime); a budgeted/static white-box arm is retained for the pilot so the paper's budgeted construct is measured, not amended away (C2 decision record).
- **Black-box:** layout hidden (sealed panel); the recorded run, target, window shown; **probe budget returns here** as the battery/TEST affordance (tap to run a configured input grid; returns lamps + Δ). Instances admitted only if identifiability holds within β (V5). Black-box scores measure identification+reasoning jointly — report separately.

### 5.3 Instance legibility requirements (generator-enforced)
- Decoys are **honest structure only**: junctions rerouting between same-outcome regions (states knob), never fabricated guards (law L4).
- `max_fanout` (junctions per state-column chain) reported; legibility cap per platform (mobile ≤ 4 suggested).
- **Quality gate (versioned, `build_from_inputs.py` v1.0):** beyond render-equivalence, every auto-built level passes a deterministic mode-appropriateness + legibility check — window ≤ 8 cells (sweeps stay watchable), per-column fan-out ≤ 4, PIN needs a non-trivial determining set, CREDIT needs ≥1 and ≤3 deciders with **all** minimal causes singletons (expressibility). Rejections logged with reasons. Formal validity alone does not admit a human level.
- **Mode balance is by selection, not by bending the assigner**: random transducers skew toward PIN (33/40 measured); corpora stratify modes at selection time and declare the assigner + gate versions.
- Same-outcome decoy forks render as two visible arcs; cosmetic merges allowed.
- Trace padding beyond the window (n > k knob) is **cropped** from the human board, not curtained.
- Trivial-instance filter (mainTB §difficulty): unconditional targets and same-column single-literal causes discarded.

### 5.4 Difficulty progression
Knobs only (mainTB table): k, #states, transition count, |Γ*| (causal-cell count), trace diversity, n, β (black-box), task object, closeness order (expert variants), track. Demo level set (5 instances: single cause → delay+decoys → gate → overdetermination → cross-time) is the canonical teaching ramp; production corpora stratify per knob ranges and ARC-style human calibration (V6).

---

## 6. Agent harness

- Observation = instance JSON minus `oracle_ref` (+`machine` in white-box only); never `φ` or the key (mainTB §agent).
- `probe(partial-assignment) → {lights, target_flashes, switches_changed}`, budget-metered identically to the human battery.
- Tool regimes declared per run: tool-less (reasoning), code-equipped (solver ceiling) — white-box agent evals MUST report which.
- Modality-confound control (paper's caveat): support rendering the board image to agents and the JSON to humans for the controlled comparison condition in V6/V7.
- Verifiable reward: native predicate, binary per attempt; AP/TS available as a training signal.

## 7. Design laws (the demo's distilled lessons — binding on future UI work)
1. **The picture is the mechanics.** The renderer consumes the same graph the simulator walks; equivalence is tested, not assumed.
2. **Routing, not cutting.** Inputs are binary and total: a flip selects the sibling transition. Nothing is ever "off"; no severed-wire fiction.
3. **Local info free, global info priced.** White-box may show alignment (local) and, having shipped the machine, may simulate live; black-box prices global recomputation via β.
4. **No fabricated structure.** Every visible element traces to the automaton; decoys are real reroutes between equivalent-outcome regions.
5. **One question per puzzle, declared.** (Revises the iteration-7 "one question" law, which produced the hidden-objective defect.) Each level states exactly one mode's question in the mode's plain verb; the three modes are explicit level types (paper §modes), assigned deterministically when undeclared (`mode_assign.py` v1.0). The win condition is decidable by looking at the board after the verdict.
6. **Any correct witness wins; supersets never do.** Set-valued grading is the point of the formal backbone; exhaustive-union demands don't scale for humans.
7. **The variant must be handled explicitly.** HP original/updated vs modified diverge exactly on overdetermination. The CREDIT IT surface poses only the original/updated object (the demonstrated decider); extinguishing sets are never a Credit answer. Benchmark corpora declare exactly one `hp_variant`; TempoBench-alignment corpora declare `modified` (A3). The dual-acceptance policy is retired (history preserves the iteration-12 build).
8. **Experiment ≠ claim, shown as two worlds.** The recording (the world the claim is about) is frozen on screen; experiments happen on the bench; the claim names recording cells. (Revises the iteration-12 resolution, which collapsed the two worlds into diff-as-answer and leaked the objective.)
9. **Teach by structure:** gate teaches "decided ≠ breaks it alone"; overdetermination teaches "decided ≠ darkens alone"; decoy forks teach irrelevance. No tutorials beyond one sentence.
10. **Every verdict carries its witness.** ACCEPT shows the completed enumeration/sweep; REJECT leaves a concrete counterexample run on the board. Nothing reveals cells the player has not implicated.

## 8. Verification harness (CI-mandatory per instance/build)
1. Totality & determinism over all settings (exhaustive ≤ ~2²⁰ cells; randomized + symbolic beyond).
2. Junction-graph ↔ HOA simulation equivalence (§2.2) — every builder calls `render.verify_equivalence` and aborts on divergence.
3. Key certification: oracle outputs for all four objects at **exhaustive search depth** (capped searches censor keys — GateB measured 49 phantom divergences under a size-3 cap; `engine.py` defaults are exhaustive, finite caps must carry a caller's certificate); every key cell testable on the board; decoy inventory.
4. **Mode-semantics equivalence** (`verify_modes.py`): the live JS verdict of each mode page, replicated over the emitted level data, equals the oracle for **every possible player action** (every single throw, every lock subset, every claimable cell).
5. **Full submission enumeration** (small instances) / sampled audit (large): the accepted set under the active policy matches the certified key exactly — this is the test class that caught iterations 10–12's bugs.
6. Render-layer lint: object-kind whitelist (§5.1), fan-out cap, text budget; quality gate (§5.3) on auto-built levels.
7. Parity audit (Gate C): observation, submission round-trip **per variant policy**, probe semantics, candidate-space safety (P_CAND, release-blocking).
8. Build determinism (`verify_mode_assignment.py`): byte-identical pages across runs and input orderings.
