# TRACE — Implementation Specification for Scalable Builds

*Consolidates every mechanic, interaction law, grading policy, and verification requirement settled during the 12-iteration demo process (see `TRACE_game_design.md` §20). This spec is authoritative for the production builds: human game (white-box and black-box), agent harness, and shared grader. Source of truth for semantics: `tex_files/mainTB.tex` (cited by section throughout).*

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

### 2.3 Mealy outputs (open reconciliation — see validation plan G2)
The demo's junction graph is Moore-style: the bulb depends on the state reached at column `k`, i.e. inputs `0..k−1`. The spec's candidate window is `0..k` and Puzzle 4 has a same-column cause. Production options (decide at V-gate): (a) render Mealy output on the *edge* entering column k (bulb hangs off the final junction chain, making moment-k cells testable); or (b) restrict the corpus to instances whose causes lie in `0..k−1` and lean on the trivial-instance filter (which already discards same-column single-literal causes). Option (a) is preferred; either way the choice must be declared and the grader's `cellsIn` must match the rendering's testable cells.

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
  "hp_variant_policy": "either",       // human play: "either"; benchmark corpus: "original" | "modified"
  "budgets": {"probes": null, "attempts": 2},           // probes: null=∞ (white-box human), int otherwise
  "difficulty": {"k":4, "states":9, "transitions":31, "causal_cells":2,
                 "trace_diversity":3, "n":6, "max_fanout":4},
  "layout": {"nodes":[...], "tracks":[...]},            // junction graph, generator-emitted
  "oracle_ref": "key.bin"             // validity oracle + canonical key (never shipped to solver)
}
```

- The **answer key is the oracle, not a string** (mainTB §groundtruth: "certify with the oracle"). Canonical Γ shipped only for TS/AP granularities.
- `layout` is presentation: the grader never reads it; the equivalence check (§2.2) binds it to `machine`.

---

## 4. Grading module (shared by all four consumers)

### 4.1 Objects (from mainTB §two-questions, §scoring)
- **Credit** (core): HP actual cause — AC1 actuality; AC2(a) necessity under contingency (W may be non-actual); AC2(b) robust survival (all subset-resets of W); AC3 subset-minimality. Implemented set-valued (demo `satisfiesAC2`/`isMinimalCause` generalizes singletons → sets).
- **Modified-variant reading** (exogenous collapse): subset-minimal joint flip, others at actual (`isMinimalFlip`).
- **Prevent** (diagnostic): singleton pivotality or the no-pivotal-cell verdict (Prop. pivotal). Not in human play loop; retained as benchmark configuration TRACE-Prevent.
- **Pin** (diagnostic/dual): subset-minimal determining set (non-emptiness check per candidate). Benchmark configuration TRACE-Pin; candidate future human mode (padlock gesture, unprototyped).

### 4.2 Task variants and policies (settled in iterations 11–12)
| Consumer | Task | Acceptance |
|---|---|---|
| Human game (all levels) | **witness** | correct ∧ subset-minimal under **either** HP reading (decider OR minimal extinguishing set). Documented deviation: a single variant cannot be communicated nonverbally; both are spec-documented HP family members (mainTB "which Halpern–Pearl"). |
| Agent benchmark, primary | witness OR per-cell union (declared per corpus) | single declared `hp_variant` (paper default: original/updated, pending V2) |
| Agent leaderboards | TS / AP granularities | canonical key (lexicographically least), per mainTB §scoring |

- Minimality test: ≤ `2^|Γ|` oracle calls; minimal causes are small (mainTB).
- **Failure feedback tiers (human):** (i) superset of an acceptable witness → "a smaller claim is hiding in yours"; (ii) otherwise → neutral "not quite". Never reveal cells. Attempts (♥) per the spec's attempt rule; solved iff any attempt earns full native credit.
- Complexity envelope: necessity/sufficiency polynomial in expanded `|A|,k`; Credit exponential in `|I|·k` (contingency search) — generation-side cost, bounded by knobs; profile per V3.

### 4.3 Submission format (parity)
Human board state and agent JSON are the same object:
- Human: thrown junctions ⇒ `{ "cause": { "t": {"input": observed_value} } }` (cells at actual values; grader supplies flips — mainTB §agent).
- Prevent config: `pivot` / `no_pivot:true`. Pin config: `lock`.

---

## 5. Human game build (TRACE)

### 5.1 Board ontology (final, iteration 9–12; no other object kinds permitted)
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

Text budget: one objective sentence shown once ("Throw what truly decided the light, and leave it thrown — the smallest true cause wins"), single-word feedback cards, numerals. Nothing else.

### 5.2 Tracks
- **White-box:** full junction graph visible; board simulates live (route + bulb). No probe budget (β=∞): the device is shipped, eye-simulation is the intended skill (β=0 regime is the mastery framing). Scored resource: attempts.
- **Black-box:** layout hidden (sealed panel); the recorded run, target, window shown; **probe budget returns here** as the battery/TEST affordance (tap to run a configured input grid; returns lamps + Δ). Instances admitted only if identifiability holds within β (V5). Black-box scores measure identification+reasoning jointly — report separately.

### 5.3 Instance legibility requirements (generator-enforced)
- Decoys are **honest structure only**: junctions rerouting between same-outcome regions (states knob), never fabricated guards (law L4).
- `max_fanout` (junctions per state-column chain) reported; legibility cap per platform (mobile ≤ 4 suggested).
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
5. **One question.** The play loop asks only the TCE question (Credit witness). Prevent/Pin are benchmark configurations, not levels.
6. **Any correct witness wins; supersets never do.** Set-valued grading is the point of the formal backbone; exhaustive-union demands don't scale for humans.
7. **The variant must be handled explicitly.** HP original/updated vs modified diverge exactly on overdetermination; human play accepts either; corpora declare one.
8. **Experiment ≠ claim** is resolved *by the witness task* (one claim, one board state); if a future mode needs multi-experiment claims (union), it requires a marking surface again — do not rediscover this.
9. **Teach by structure:** gate teaches "decided ≠ breaks it alone"; overdetermination teaches "decided ≠ darkens alone"; decoy forks teach irrelevance. No tutorials beyond one sentence.
10. **Minimal feedback, maximal honesty:** "a smaller claim is hiding in yours" is the only coached failure; nothing reveals cells.

## 8. Verification harness (port of demo test suite; CI-mandatory per instance)
1. Totality & determinism over all settings (exhaustive ≤ ~2²⁰ cells; randomized + symbolic beyond).
2. Junction-graph ↔ HOA simulation equivalence (§2.2).
3. Key certification: oracle outputs for all four objects; every key cell testable on the board; decoy inventory.
4. **Full submission enumeration** (small instances) / sampled audit (large): the accepted set under the active policy matches the certified key exactly — this is the test class that caught iterations 10–12's bugs.
5. Render-layer lint: object-kind whitelist (§5.1), fan-out cap, text budget.
6. Parity audit: human board state → JSON serialization → grader equals direct human grading, per instance.
