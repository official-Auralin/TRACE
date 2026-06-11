# GLOWBOX — A Visual Puzzle Game Design for TRACE

*A minimalist, all-ages rendering of the TRACE benchmark (Temporal Reasoning And Causal Explanation), faithful to `tex_files/mainTB.tex` and its companion framework papers (`main.tex`, `main2.tex`).*

---

## 1. Executive summary

The repository specifies TRACE: a one-player benchmark in which a frozen, synthesized finite-state controller is presented as a sealed reactive device; the player sees an observed run (switch settings over time, lights that flashed), one highlighted target flash (light *o* at step *k*), and must answer one of three precise causal questions — **Prevent** (which single switch flip, alone, stops the flash; count-only necessity), **Credit** (which switches actually decided the flash, allowing contingencies; Halpern–Pearl actual causation — the core object), and **Pin** (the fewest switches to lock so the flash is forced no matter what; determining-set sufficiency). Experimentation happens through a budgeted **run/probe** button that deterministically replays the device.

**GLOWBOX** is the player-facing rendering of exactly this system. The player sees a small machine: a grid of levers (rows = switches, columns = moments in time), a lamp strip beneath, one star-ringed flash as the target, and a curtain dimming everything after the target moment. They flip levers, turn the crank (each turn costs one *spark*), watch the lamps recompute, and finally answer the mode's question by placing **stop-scissors**, **gold stars**, or **locks** directly on lever cells. Nothing technical is visible; every rule, mode, budget, scoring granularity, and difficulty knob is taken verbatim from the source specification. The paper itself prescribes this abstraction family ("a marble-and-switch device in the mechanical spirit of *Turing Tumble*", §"Running synthesis backwards into a board") — GLOWBOX is that prescription made concrete, screen-ready, and child-readable.

Core loop: **look → flip → crank → watch → mark → submit**.

---

## 2. Repository evidence map

All references are to `tex_files/mainTB.tex` (line numbers from the source file). `main.tex` / `main2.tex` supply the general frame-relative causal framework that §2 of `mainTB.tex` restates; `mainTB.tex` is the authoritative spec for the game.

| # | Source | Technical element | Plain-language explanation | Type | Player-facing possibility | Difficulty relevance | Confidence | Design risk |
|---|--------|------------------|---------------------------|------|--------------------------|---------------------|-----------|-------------|
| E1 | mainTB §2.1, ll. 262–295 | Reactive system, inputs *I*, outputs *O*, finite trace τ≤n; acceptor A_HOA, admissibility = run-defined | A machine reads switch values each step and emits output values; the observed history is a finite trace | entity / state | A device with a switch grid (rows×time) and a lamp strip | trace length *n* is a knob | confirmed | too invisible if grid unlabeled — solved by column numerals |
| E2 | mainTB ll. 274–276, 444–457 | Mealy machine; assumptions (F1) behavior model, (F2) input-determinism, (F3) input-totality | Outputs are fully determined by inputs; any switch setting yields a legal run | invariant | Crank always works; same levers ⇒ same lamps, always | enables the whole probe mechanic | confirmed | trivial-looking but must never be violated |
| E3 | mainTB §2.3, ll. 327–350 | Input cell (t,i); count-only closeness d(τ,τ′) = # changed input cells | The unit of change is one lever at one moment; "closer" = fewer flips | constraint / metric | A flip counter on the device ("changed: 2") | closeness order is a knob (count-only vs profile) | confirmed | easy to misrepresent if outputs were counted — they are not |
| E4 | mainTB Def. "Valid cause", ll. 352–371 | Four clauses: actuality, non-vacuity, counterfactual dependence, anti-circularity | A cause must be true on the run, removable, its removal must kill the effect on every closest removal, and may not restate the effect | rule / goal | The Prevent grading predicate | — | confirmed | anti-circularity is automatic in TB frame (l. 435) — hide it |
| E5 | mainTB §2.4, ll. 386–412 | TempoBench frame: effect X^k o; candidates Γ ⊆ {0..k}×Lit(I); B=true; input-only intervention; subset minimality | Target = one light at one step; answers are sets of (moment, lever:value) cells inside the window; smaller sets preferred | goal / constraint | Star-ringed flash; marks placed only on cells in columns 0..k; spam answers score 0 | window size 2^{2|I|(k+1)} grows with k, \|I\| | confirmed | minimality invisible until graded — teach via attempts feedback |
| E6 | mainTB ll. 968–970, fig. anatomy | Causal window 0..k; steps after k dimmed | Later levers cannot cause an earlier flash | constraint | A curtain/dimming over columns after the target | trace length n beyond k = distractor context | confirmed | low |
| E7 | mainTB Prop. "pivotal", ll. 514–536 | Under (F2)–(F3) every minimal count-only necessity cause is a singleton; else "no pivotal cell" | Either one lone flip stops the flash, or nothing alone does | rule / failure verdict | Prevent mode: place ONE scissors, or press the "nothing alone stops it" button | overdetermination instances force the verdict | confirmed | players may try multi-cell Prevent answers — UI allows exactly one scissors |
| E8 | mainTB Def. "determining set", ll. 579–590 | Sufficient set: fixing Γ's cells forces o at k over all admissible completions; subset-minimal | Lock these levers and the flash fires no matter what else happens | rule / goal | Pin mode: padlocks on cells | \|Γ*\| is a knob | confirmed | "for all other settings" is the grader's quantifier — one crank ≠ proof; teach via budget |
| E9 | mainTB Def. "actual cause", ll. 592–633 | AC1 actuality; AC2(a) necessity under contingency W=w; AC2(b) robust local sufficiency; AC3 minimality | A switch is a decider if under some setting of the others, toggling it flips the flash while in place it keeps it | rule / goal (core) | Credit mode: gold stars; a contingency test = a *pair* of cranks | mode is a knob; Credit is hardest | confirmed | most subtle object — teach via paired-run "ghost" comparison |
| E10 | mainTB Remark "non-monotone", ll. 478–488 | Validity is not monotone in Γ; greedy literal-deletion fails | Adding or removing cells from a candidate can flip its validity either way | constraint | No hint system that suggests greedy pruning; puzzles where greedy fails | source of genuine search difficulty | confirmed | must NOT add a "remove-while-valid" helper |
| E11 | mainTB §3 modes, ll. 1021–1086 | Three modes Credit / Prevent / Pin; plain verbs; quantifiers belong to grader | The three questions over the same device | action / goal | Three mode tabs with icon grammar (★ / ✂ / 🔒) | mode is an explicit difficulty knob | confirmed | low — verbs are already player-facing in source |
| E12 | mainTB §"try button", ll. 1088–1122 | Probe: set any in-window cells, run replays deterministically, returns lights + target status + change count; budget β_max; β=0 = pure deduction; large β = trial-and-error | The crank, sparks, and flip counter | action / resource | Crank button; spark meter; counter | probe budget β_max is a knob | confirmed | budget pressure must feel fair — show sparks up front |
| E13 | mainTB §scoring, ll. 1124–1175 | Native predicate grading; Witness / All-causes / Per-cell-union variants; non-minimal superset scores 0; TS and AP granularities; few attempts, solved if any attempt is fully correct | Any correct minimal answer wins; spam fails; limited tries | scoring rule | Hearts (attempts); submission checked by hidden grader; full-win chime only on exact predicate satisfaction | — | confirmed | partial credit (AP) is for leaderboards, not the toy — keep player score binary per attempt |
| E14 | mainTB §difficulty, ll. 1177–1206 | Knob table: effect depth k; # automaton states; transition count; \|Γ*\|; trace diversity; trace length n; probe budget β_max; mode; closeness order. Trivial-instance filter (unconditional target, same-column cause) | The complete, source-defined difficulty model | difficulty factors | See §4 below — progression uses ONLY these | this IS the difficulty model | confirmed | inventing other difficulty axes is forbidden |
| E15 | mainTB worked puzzles 1–5, ll. 1208–1385 | Five canonical instances with checker-verified answers in all three modes | Tutorial through delayed overdetermination | examples | Directly reused as GLOWBOX levels 1–6 | puzzles 3–5 show mode divergence | confirmed | none — they are the gold standard |
| E16 | mainTB §agent, ll. 1387–1460 | White-box track (device shown as trellis/table) vs black-box track (device hidden; identifiability requirement); JSON protocol mirrors board 1:1 | Two information settings; black-box adds system identification | observation / difficulty | Lid open (lane map visible) vs lid sealed | black-box is harder by design | confirmed | black-box must only ship identifiable instances (roadmap V5) — generator concern, not UI |
| E17 | mainTB fig. anatomy, ll. 981–1019 | Trellis: states as lanes, columns as steps, lit path = observed run, goal node q* flashes target, dashed = untaken routes | The white-box depiction | entity / observation | The "lane map" under the lever grid: a marble path through lanes | # states / transition count knobs are *visible* here | confirmed | lanes must not look interactable — only levers are |
| E18 | mainTB ll. 1093–1095, 1106–1110 | One press evaluates ONE scenario; Pin's ∀ and Credit's ∃ are the grader's | The player generalizes from finitely many experiments | rule | Crank result card says "this time"; submission says "always/decided" | — | confirmed | risk: players conflate one good run with proof — wording + iconography fix |
| E19 | main.tex / main2.tex (titles, framework) | Frame-relative counterfactual causes; frame 𝔉 = (B, E, S, O, K, I, ⪯, ◁) | The general theory the TB frame instantiates | hidden machinery | None — entirely hidden | closeness-order knob comes from here (App. flex) | confirmed | must stay invisible |
| E20 | mainTB ll. 543–558 | No-pivotal-cell verdict is ambiguous: overdetermined vs input-unconditional; the latter is filtered out | If nothing alone stops it, deciders may still exist (Credit finds them) | state / verdict | The ⊘ "nothing alone stops it" button is a *correct answer*, not a forfeit | overdetermination = Credit-vs-Prevent divergence | confirmed | must feel like a triumphant answer, not giving up |

---

## 3. Canonical source model

**Entities.** A frozen input-deterministic, input-total finite-state device A_HOA over inputs *I* and outputs *O*; an observed trace τ≤n = α₀…α_n; a target effect X^k o with o ∈ α_k; the causal window {0,…,k}; a probe budget β_max; an attempt count.

**States.** Each input cell (t,i) is ON/OFF; each output cell (t,o) flashed/dark; the device occupies one (hidden or shown) automaton state per step; the current *scenario* is the player's edited input grid; remaining sparks; remaining attempts; placed marks (stars/scissors/locks).

**Player-equivalent actions** (source: §try-button, §agent action). Toggle any in-window input cell; press run (replay from step 0, deterministic, −1 spark); place/remove marks of the active mode; press submit; in Prevent, alternatively press the no-pivotal-cell verdict; reset scenario to the observed run (free — it changes no information).

**System responses.** Run: recompute all lamps from the edited inputs, report target flashes? and # cells changed vs. observed. Submit: grade against the active mode's predicate (valid cause / actual cause / sufficient set, each subset-minimal); full credit or attempt lost.

**Rules.** Allowed: editing input cells in columns 0..k only. Forbidden: editing lamps, editing the device, editing columns past k, multi-cell Prevent answers, answers not true on the observed run (actuality), answers naming the target lamp at the target step (anti-circularity — structurally impossible here since marks go on levers only). Preserved: determinism (same inputs ⇒ same lamps). Consumed: sparks per run, hearts per failed submission.

**Invariants.** Wiring never changes; every lever setting yields a legal run (F3); outputs are a function of inputs (F2); distance counts changed *levers* only, never lamp consequences; the observed run always satisfies a gradable answer's cells at their actual values.

**Goals.** Prevent: one singleton pivotal cell, or the no-pivotal-cell verdict when none exists. Credit: one minimal actual cause (witness) or the per-cell union Γ^ac. Pin: one subset-minimal determining set. Solved iff some attempt earns full native credit.

**Failure / invalid states.** Wrong cell(s); non-minimal superset (scores 0); claiming a pivot where none exists or vice versa; running out of attempts. Invalid *actions* (clicking past the curtain, clicking lamps, second scissors) are softly refused — they are not failures.

**Source-defined difficulty factors.** Exactly the knob table (E14): k, #states, transition count, |Γ*|, trace diversity, n, β_max, mode, closeness order; plus the white-box/black-box track (E16) and the trivial-instance filter.

**Feedback requirements.** After each run: full recomputed lamp strip, target status, change count. After submit: solved / not solved (native, binary per attempt).

**Hidden machinery.** HOA serialization, LTLf semantics, the frame tuple 𝔉, the grader's reachability checks, CORP/Halpern–Pearl definitions, the ∀/∃ quantifiers (felt, never shown), the answer key.

**Faithfulness checklist** — every player-facing element below traces to one of E1–E20; see §16 for the rule-by-rule table.

---

## 4. Difficulty model (source-defined, mainTB §"Difficulty knobs")

| Source knob | Technical meaning | What it changes in play | Exposed visually? | Stage introduced |
|---|---|---|---|---|
| Effect depth *k* | target step index; window {0..k}; candidate space ≤ 2^{2\|I\|(k+1)} | more columns before the star; longer credit assignment; bigger search space | **yes** — board width up to the curtain | early→all |
| # automaton states | richer internal dynamics to simulate | more lanes in the lane map (white-box); harder mental simulation (black-box) | yes (white-box lanes) / felt (black-box) | medium |
| Transition count | denser branching | more arrows between lanes; more routes to consider | yes (white-box) / felt | medium |
| Causal-input count \|Γ*\| | larger true cause | more marks needed; Pin sets grow | felt, then seen at solve | medium |
| Trace diversity (# distinct inputs) | more candidate cells | more lever rows / more rows actually toggled in the run | **yes** — row count & busy grid | early-medium |
| Trace length *n* | distractor context beyond the window | wider board behind the curtain; visual noise that must be ignored | **yes** — curtain extent | medium |
| Probe budget β_max | less brute-force checking; β=0 ⇒ pure deduction | fewer sparks; forces hypothesis-driven cranking | **yes** — spark meter | medium→expert |
| Mode | necessity / actual cause / sufficiency | scissors → locks → stars; stars (Credit) hardest: paired-run contingencies | **yes** — mode tab | staged: Prevent → Pin → Credit |
| Closeness order | count-only vs profile (App. flex) | how the flip counter weighs changes | hidden (count-only only in core corpus) | expert variant only |
| Track (white/black-box) | device shown vs inferred | lid open (lane map) vs sealed lid | **yes** — lid | expert |

**Forbidden difficulty changes** (would distort the source): timers/time pressure (no source basis); randomizing the device between runs (violates F2); making some lever settings illegal (violates F3); counting lamp changes as distance (violates count-only closeness); grading partial answers as wins in the core game (violates native predicate grading); shipping instances with an unconditional target or a same-column single-literal cause (trivial-instance filter); adding a live adversary (explicitly excluded, ll. 1066–1073).

**Felt-but-hidden:** the non-monotonicity of validity (E10) — the player experiences it as "adding a lock broke my answer," never as a stated rule.

---

## 5. Abstraction candidates

### Frame A — "Glowbox" (sealed lamp machine; the paper's own family)
- **Premise:** a wind-up box of levers and lamps replays one recorded evening; explain the starred flash.
- **Verb:** flip & crank. **Visual language:** instrument panel — lever grid, lamp strip, brass crank, curtain.
- **Sees:** lever grid (rows×moments), lamp strip, star ring, spark meter, hearts, mode tab. **Manipulates:** levers, marks.
- **After a move:** crank → lamps recompute, counter shows flips, spark spent.
- **Goal display:** mode icon + the starred flash. **Invalid display:** lever springs back with a soft thunk; curtain ripples; second scissors refuses.
- **Difficulty display:** wider boards (k, n), more rows (diversity), fewer sparks (β), lane map density (#states/transitions), lid sealed (black-box).
- **Hidden:** automaton, LTLf, grader. **Faithful:** literally the spec's prescribed device (E1–E18). **Minimalist:** one grid, one strip, one button. **All-ages:** levers and lamps need no reading. **Risk:** Credit's "for some setting of the others" can read as "I found one run that worked" — mitigated by the paired-run ghost UI (§7).

### Frame B — "Signal Yard" (train through switch-tracks)
- **Premise:** a recorded train ran through a rail yard; the bell rang at station k; explain it.
- **Verb:** throw switches, replay the train. Lanes = automaton states (the trellis literally drawn); bell = output.
- **Faithful:** excellent for the white-box track (trellis is native); state lanes are *the* depiction (E17). **Risks:** the train metaphor implies the player routes the train freely — but only switch cells are inputs and the engine (controller) is frozen; multiple output lamps per step strain the bell metaphor; black-box (hidden tracks) reads as broken, not sealed.

### Frame C — "Night Garden" (watering valves and a bloom)
- **Premise:** valves were opened on certain days; a flower glowed on day k; mark the waterings that decided it.
- **Verb:** open/close valves, replay the week. Warm, narrative, child-friendly.
- **Risks:** organic causation invites probabilistic intuitions (plants "tend to" grow) — directly contradicts determinism (F2); replay-from-start feels unnatural for a garden; lamp strip with multiple outputs strains the metaphor; contingencies ("what if it hadn't rained Tuesday") drift toward real-world causal folk-theory the grader doesn't share.

### Scoring (rubric weights from the brief)

| Criterion (weight) | A Glowbox | B Signal Yard | C Night Garden |
|---|---|---|---|
| Faithfulness (40) | 39 | 34 | 24 |
| Source difficulty preserved (15) | 14 | 13 | 9 |
| Immediate understandability (15) | 13 | 13 | 14 |
| Depth & scalability (10) | 9 | 8 | 6 |
| Minimalist elegance (10) | 9 | 7 | 7 |
| All-ages accessibility (5) | 5 | 4 | 5 |
| Emotional/aesthetic appeal (5) | 4 | 4 | 5 |
| **Total** | **93** | **83** | **70** |

## 6. Selected abstraction

**Frame A (Glowbox), with Frame B's lane map embedded as the white-box view.** This is not a compromise — it is the source's own architecture: the spec says the black-box track shows only switch and light panels while the white-box track shows the trellis beside them (E16, E17). Glowbox = panels; the lane map = trellis; the sealed lid = black-box. Frame B alone fails black-box; Frame C fails determinism. Frame A also makes the probe mechanic natural (cranking a music box re-plays it identically — determinism is *felt*), and the curtain makes the causal window physical.

---

## 7. Meaning map

| Technical source element | Visual representation | Player name | Interaction | State change | Feedback | Mechanic preserved | Difficulty link | Misread risk → prevention |
|---|---|---|---|---|---|---|---|---|
| Input cell (t,i) | lever in grid cell; up=ON ●, down=OFF ○ | lever | tap to flip (window only) | scenario edited; flip counter ±1 | lever animates; counter updates; edited cells get a ring ◉ | candidate vocabulary {0..k}×Lit(I); count-only distance | trace diversity = rows; k = columns | "flips are saved" → run always replays from col 0, marble animation makes it obvious |
| Output occurrence (t,o) | lamp dot: ✸ lit, · dark | lamp | none (not tappable) | recomputed on crank | flash animation on crank | outputs determined, not edited (input-only intervention) | — | tapping a lamp → gentle shake, no state change |
| Effect X^k o | lamp with star ring ⊛ under column marker ▼ | the star | none | — | pulses until solved | point effect at fixed step | k visible as star column | — |
| Window {0..k} / steps > k | dim curtain over later columns | the curtain | levers behind it don't flip | — | curtain ripples on tap | later inputs can't cause earlier flash | n − k = curtain extent | "curtain = locked content" → tooltip-free ripple + tutorial layout |
| Probe / run | brass crank button | crank | press | −1 spark; lamps recompute; counter reported | full replay animation, marble runs left→right; result card: ⊛ lit? + "levers changed: m" | deterministic replay; one press = one scenario | β_max = spark meter | "one good run proves it" → result card stamped "THIS TIME"; submit card stamped "ALWAYS?" |
| Budget β_max | spark meter ⚡⚡⚡ | sparks | spent by crank | decrements | dims one spark | budgeted probes force reasoning | direct knob | — |
| Count-only distance | "levers changed: m" chip | flip count | — | — | updates live while editing | distance = # changed input cells only | closeness-order knob (hidden in core) | counting lamps → lamps have no counter anywhere |
| Prevent answer (valid cause, singleton) | one scissors token ✂ on a lever | stop-mark | drag onto exactly one lever | — | second scissors politely refuses | Prop. pivotal: minimal necessity causes are singletons | mode knob | multi-cell necessity answers → UI holds ONE scissors, by theorem |
| No-pivotal-cell verdict | round button ⊘ "nothing alone stops it" | the shield | press instead of placing scissors | — | treated as a full answer; victory chime if correct | the verdict of Prop. pivotal | overdetermined instances | "⊘ = give up" → button styled gold, equal weight to scissors |
| Actual cause (AC1–AC3) | gold star tokens ★ on levers | star-marks | place on cells (at their observed values) | — | submit grades witness or union | Def. actual cause | mode knob; \|Γ*\| | conflating with Pin → contingency rehearsal UI below |
| Contingency (W,w) | "ghost panel": player sets *other* levers anywhere, then cranks a PAIR (candidate in place / toggled) | the what-if pair | two cranks, auto-paired (costs 2 sparks) | — | side-by-side result cards: in-place ⊛✓ / toggled ⊛✗ | AC2(a)+(b) two arms; pair pricing per spec | budget pressure doubles in Credit | players testing only one arm → the pair button always runs both |
| Sufficient set | padlocks 🔒 on levers | locks | place locks; crank scrambles unlocked levers to any chosen setting | — | result card per scenario; submit asks "always?" | Def. determining set; grader holds the ∀ | \|Γ*\|, mode | "one surviving run = proof" → "ALWAYS?" stamp + budget teaches sampling ≠ proof |
| Subset minimality | grading rule; hearts | tries ♥♥ | submit | −1 heart on fail | "not quite — could fewer marks work?" / "a mark isn't needed" style result (no cell revealed) | non-minimal superset scores 0 | \|Γ*\| | — |
| Attempts | hearts ♥ | tries | — | decrement | — | few submissions; solved if any is fully correct | — | — |
| Trellis (white-box) | lane map: dots in lanes, arrows between columns, observed path drawn thick, goal node ringed | the lane map | view-only; tapping highlights routes | — | crank animates the marble along the current route | white-box track ships the device | #states = lanes; transitions = arrows | looks interactable → flat matte styling, no affordance |
| Black-box track | lid closed over the lane map | sealed box | — | — | — | discovery track; identifiability per generator | track knob | — |
| Grader | hidden | — | — | — | binary solve chime / heart loss | native predicate grading | — | — |
| Modes | three tabs ✂ / 🔒 / ★ with one-line plain prompts | Stop / Lock / Star | select per puzzle (fixed by instance) | — | prompt line under tab | the three causal objects | mode knob | — |

Pure presentation-layer affordances (cosmetic, no effect on the system): marble animation, chime, lever sounds, the reset-to-observed button (re-establishes τ, which the player could do by hand; adds no information), the "THIS TIME / ALWAYS?" stamps.

---

## 8. Core puzzle grammar

- **Play space:** one board = lever grid (|I| rows × n+1 columns) + lamp strip(s) + star + curtain from column k+1; white-box adds the lane map below.
- **Player-controlled:** lever cells in columns 0..k; mode marks; crank; submit; shield (Prevent only); reset-to-observed.
- **Non-player:** lamps, lane map, star, curtain, counters.
- **Goal:** satisfy the mode prompt — ✂ "flip ONE lever so the star goes dark — everything else as recorded" / 🔒 "lock the FEWEST levers so the star shines no matter what the rest do" / ★ "star every lever that truly decided the flash."
- **Obstacles:** distractor levers and steps (trace diversity, n), delay (k), overdetermination, joint guards, dense wiring, spark scarcity, sealed lid.
- **Resources:** sparks (runs), hearts (attempts).
- **Allowed actions / disallowed actions / transitions / feedback / win / invalid behavior:** as in the meaning map; all state transitions are deterministic replays; win = grader-verified native credit; invalid actions are softly refused and never consume resources.
- **Undo/reset:** flipping levers is freely reversible; reset-to-observed is free; marks are freely movable until submit; cranks and submits are the only consumables (as the source prices them).
- **Hints (optional, presentation-layer):** three tiers per instance (attend → relate → almost solve), generated from the answer key but phrased visually; never name the grader's quantifiers.
- **Mastery (optional):** solve with zero sparks spent (the source's β=0 "pure deduction" regime); all-causes variant for experts (source scoring variant).
- **Instantiation:** an instance = (device, τ, target, mode, track, β_max, attempts) drawn from the generator pipeline (mainTB §3, "A Benchmark Generator"); new puzzles are new instances of the same grammar, stratified by the knob table and filtered for triviality.

---

## 9. Visual legend

```
LEVERS                 LAMPS                 MARKS & VERDICT
●  lever ON            ✸  lamp flashed       ✂  stop-mark (Prevent; max 1)
○  lever OFF           ·  lamp dark          🔒 lock (Pin)
◉  lever flipped       ⊛  THE STAR (target)  ★  star-mark (Credit)
   from recorded       ▼  target column      ⊘  "nothing alone stops it"
░  curtain (past k)

METERS                 BOARD FURNITURE        RESULT STAMPS
⚡ spark (1 run)        [CRANK]  run button    THIS TIME — crank result
♥  try (attempt)       [RESET]  back to       ALWAYS?  — submit confirm
Δn "levers changed"             recorded run  ✔ solved   ✗ try lost

LANE MAP (white-box only)
o lane node    ═══ recorded path    --- other route    (⊛) goal node
```

Shape + fill carry all meaning; color is reinforcement only (gold = goal/marks, blue = recorded path, gray = curtain). Lamps are round, levers are square-celled, marks are token-shaped — three families distinguishable in grayscale.

---

## 10. Base UI rendering (white-box, mid-size board)

```
┌──────────────────────────────────────────────────────────────────┐
│  ★ STAR IT      moment:  0    1    2    3 ▼  4    5             │
│  "star every   ┌────┬────┬────┬────┬─────────┐                  │
│   lever that    │ ●  │ ●  │ ○  │ ○  │░░░░░░░░░│  ← lever A       │
│   decided the   ├────┼────┼────┼────┼─────────┤                  │
│   flash"        │ ○  │ ○  │ ○  │ ●  │░░░░░░░░░│  ← lever B       │
│                 └────┴────┴────┴────┴─────────┘                  │
│                   ·    ✸    ·    ⊛   ░░░░░░░    ← lamp: GLOW     │
│                                                                  │
│   lane map ┌────────────────────────────────┐                    │
│   (view)   │ o═══o    o    (⊛)   o          │                    │
│            │   \---o═══o═╱--o    o          │                    │
│            └────────────────────────────────┘                    │
│                                                                  │
│  ⚡⚡⚡⚡⚡⚡    Δ0 levers changed     ♥♥                              │
│  [ CRANK ]   [ RESET ]                      [ SUBMIT ★ ]         │
└──────────────────────────────────────────────────────────────────┘
```

Black-box track: identical, with the lane map replaced by a closed lid `▓▓ sealed ▓▓`. Small screens: lane map collapses behind a flip-up handle; the lever grid and lamp strip never scroll horizontally for k ≤ 5 (cells shrink, symbols don't).

---

## 11. Core interaction rendering (flip → crank → watch)

Puzzle 1 device (button → lamp next step). Recorded: button ON at 0; GLOW at 1 (the star).

```
BEFORE (as recorded)            EDIT (flip the lever)           AFTER CRANK (−1 ⚡)
moment   0    1▼                moment   0    1▼                moment   0    1▼
button │ ●  │    │              button │ ◉  │    │              button │ ◉  │    │
GLOW     ·    ⊛                 GLOW     ·    ⊛(old)            GLOW     ·    ·
⚡⚡⚡  Δ0                        ⚡⚡⚡  Δ1                        ⚡⚡   Δ1
                                                                ┌────────────────┐
                                                                │ THIS TIME      │
                                                                │ star: DARK ✗   │
                                                                │ levers changed:1│
                                                                └────────────────┘
```

The player just *demonstrated* counterfactual dependence with one flip — the Prevent predicate, felt before it is ever named.

---

## 12. Progressive instance gallery

All eight instances below move ONLY along source knobs (E14/E16). Devices for 1–6 are the paper's worked Puzzles 1–5 verbatim; 7–8 extend along declared knobs.

**Knob trajectory:** `k: 1→2→2→0*→1→2→3→4 · rows: 1→2→2→2→2→2→2→2 · states: 2→3→3→2→2→3→4→4 · β: 8→8→6→6→6→6→4→4 · mode: ✂→✂→✂→🔒→✂+★→★→🔒→★ · track: open…open→sealed`
(*Instance 4 uses the paper's Puzzle 4, which the spec keeps only as a teaching isolate of the necessity/sufficiency split; the spec's trivial-instance filter would exclude it from a graded corpus, so GLOWBOX uses it as an untimed lesson level, not a scored one.)

### I1 — "One Lever" (Tutorial; Prevent) — Puzzle 1
k=1, 1 lever, 2 states, β=8, ✂.
```
moment   0    1▼          ✂ goes on the only sensible cell:
button │ ●  │    │        flip button@0 → star dark. Δ1.
GLOW     ·    ⊛           Answer: ✂ on (0, button).
```
Harder than nothing; teaches flip/crank/star/scissors. Aha: the lever *before* the flash matters, not at it.

### I2 — "The Idle Lever" (Practice; Prevent) — Puzzle 2
**Knobs up: k 1→2, rows 1→2 (trace diversity), states 2→3.**
```
moment   0    1    2▼
a      │ ●  │ ○  │ ○  │     b@1 is recorded ON — but flipping it
b      │ ○  │ ●  │ ○  │     changes nothing (crank shows DONE still ✸).
DONE     ·    ·    ⊛        Answer: ✂ on (0,a).
```
Aha: a lever can be ON during the run and still not matter; recency-bait (b@1 sits next to the star) fails.

### I3 — "Two Roads" (First constrained; Prevent with the shield) — Puzzle 3
**Knobs up: overdetermination (structure), β 8→6.**
```
moment   0    1▼
a      │ ●  │    │   flip a → still ✸ (b carries it). flip b → still ✸.
b      │ ●  │    │   flip BOTH → dark, but ✂ holds only ONE lever…
FIRE     ·    ⊛      Answer: ⊘ "nothing alone stops it."
```
First instance where the *verdict* is the answer. Aha: "no single stopper" is a discoverable, correct fact (Prop. pivotal's empty case).

### I4 — "The Gate" (Lesson level; Pin introduced) — Puzzle 4
**Knobs up: mode → 🔒, \|Γ*\| = 2.** k=0 isolate (unscored lesson; see * above).
```
moment   0▼
ask    │ ●  │    Lock ask only → crank with stop scrambled ON → star dark ⇒ not enough.
stop   │ ○  │    Answer: 🔒 ask@0 AND 🔒 stop@0 (lock the OFF too!).
GRANT    ⊛
```
Aha: locking a lever at OFF is meaningful — sufficiency needs the whole guard.

### I5 — "Two Roads, Starred" (Medium; Prevent vs Credit on one board) — Puzzle 3 revisited
**Knobs up: mode → ★ (the core object enters).**
Same board as I3. The what-if pair: hold b OFF (ghost), crank pair on a → in-place ⊛✓ / toggled ⊛✗ ⇒ a is a decider. Symmetrically b. Answer (union task): ★ on (0,a) AND ★ on (0,b).
Aha — the game's thesis: where the scissors found *nothing*, the stars find *both*. Overdetermination made visible to a child.

### I6 — "The Long Echo" (Medium-hard; Credit across time) — Puzzle 5
**Knobs up: k 1→2 with mode ★ (delayed credit assignment — "the case the benchmark is built for").**
```
moment   0    1    2▼
a      │ ●  │ ○  │ ○  │   Deciders sit at DIFFERENT moments:
b      │ ○  │ ●  │ ○  │   ★ (0,a) and ★ (1,b).
FIRE     ·    ·    ⊛      (✂ would again say ⊘.)
```
Aha: causes spread across time; the pair-crank discipline scales.

### I7 — "Hold It Steady" (Advanced; Pin at depth, scarce sparks) — new instance
**Knobs up: states 3→4, transitions denser, k→3, n→5 (curtain context), β→4, \|Γ*\|=2.**
Device: GLOW at t+1 iff lever a was ON at t−1 *and* t (a 3-state counter + idle lever c). Recorded: a ON at 0,1,2; c ON at 4 (behind the curtain); GLOW at 2 and 3; target = GLOW@3.
```
moment   0    1    2    3▼   4    5
a      │ ●  │ ●  │ ●  │ ○  │░●░│░○░│     Answer: 🔒 (1,a) + 🔒 (2,a).
c      │ ○  │ ○  │ ○  │ ○  │░●░│░○░│     a@0 is a red herring — it fed the
GLOW     ·    ·    ✸    ⊛   ░░░░░░░      EARLIER flash, not the starred one.
```
Aha: two flashes, one star — pin the pair that feeds *this* one. Four sparks forbid scrambling all 2⁶ in-window settings.

### I8 — "The Sealed Box" (Expert / stress test; black-box Credit) — new instance
**Knobs up: track → sealed, k→4, β=4, mixed structure (overdetermination + guard), per-cell union task.**
Device (hidden): FIRE@4 iff (a@0 OR a@1) AND b OFF@3. Recorded: a ON at 0 and 1, b OFF throughout, FIRE@4.
```
moment   0    1    2    3    4▼
a      │ ●  │ ●  │ ○  │ ○  │    │   ▓▓▓ lane map sealed ▓▓▓
b      │ ○  │ ○  │ ○  │ ○  │    │
FIRE     ·    ·    ·    ·    ⊛      Answer (union): ★(0,a) ★(1,a) ★(3,b·OFF)
```
Solution structure: b@3 is pivotal outright (empty contingency, 1 pair); a@0 and a@1 each need the other held OFF (2 pairs) — exactly 4 sparks if every crank is purposeful. Aha: a star on an OFF lever; deduction under a sealed lid with zero waste.

**The gallery in one picture — same grammar, growing along source knobs only:**

```
I1 ▦            I3 ▦▦           I6 ▦▦▦           I8 ▦▦▦▦▦ ▓sealed▓
   ✂ 1 lever       ✂→⊘ 2 levers    ★ deciders        ★ union, OFF-cell,
   k=1             overdetermined   across time       guard+overdet, β=4
```

---

## 13. Three fully specified instances

### 13a. Tutorial — I1 "One Lever" (Prevent)

Rendering: §11 & §12-I1. **Source mechanics:** valid cause Def. (E4), Prop. pivotal (E7), probe (E12). **Knobs:** k=1, |I|=1, 2 states, β=8, ♥2, white-box.
**Start:** button ON@0; GLOW@1 starred; lane map: 2 lanes, recorded path to goal node.
**Goal:** ✂ on (0,button). **Legal:** flip button@0/@1, crank, reset, place 1 ✂, submit. **Illegal (refused):** flipping past curtain (none here), tapping lamps, second ✂.
**Solution path:** flip button@0 → crank → star dark → ✂ there → submit. **Alternative:** pure deduction from lane map, zero sparks (mastery). **Dead ends:** ✂ on (1,button) — flipping it never changes GLOW@1; grader rejects, −1♥.
**Feedback:** crank card "THIS TIME star: DARK ✗ / changed: 1"; submit chime ✔.
**Hints:** (1) the star's column pulses, then the column *before* it; (2) ghost replay shows button@0 edge feeding the goal lane; (3) lever flips itself in preview, star previews dark — player must still place ✂ and submit.
**Why fun:** one flip, total clarity, instant cause-and-effect. **Why faithful:** literally Puzzle 1 with checker semantics intact. **Prototype next:** crank animation timing; ✂ drag affordance.

### 13b. Midgame — I5 "Two Roads, Starred" (Credit, witness-or-union)

Rendering: §12-I3/I5. **Source mechanics:** actual cause Def. (E9), contingency pair pricing (E12), divergence from necessity (E7/E20), set-valued answers (E13). **Knobs:** k=1, |I|=2, β=6, ♥2, mode ★, white-box.
**Start:** a ON@0, b ON@0, FIRE@1 starred. **Goal (union task):** ★(0,a), ★(0,b).
**Legal:** flips in column 0..1, what-if pair cranks (2⚡), single cranks, ★ placement, submit. **Illegal:** ⊘ (that's a ✂-mode answer; tab shows ★), starring lamp cells.
**Expected path:** single flips show neither alone stops it (2⚡); ghost: hold b OFF, pair on a (2⚡) → decided; symmetry argument for b (0⚡, deduction — or spend last 2⚡). Submit both stars.
**Alternatives:** witness variant accepts {★(0,a)} alone or {★(0,b)} alone — the checker accepts *any* correct minimal witness (E13).
**Dead ends / invalid:** starring both PLUS extra cells = non-minimal union, scores 0; starring only one in union mode = incomplete.
**Feedback:** pair card shows both arms side-by-side; failed submit: "every star must have decided it — and no decider may be missing."
**Hints:** (1) "the scissors found nothing here… but the star asks a different question"; (2) ghost panel opens with b pre-held OFF; (3) the a-pair runs itself, star placement left to player.
**Why fun:** the I3→I5 reversal is a genuine plot twist. **Why faithful:** exactly the spec's flagship divergence (Puzzle 3, ll. 1275–1309). **Prototype next:** ghost-panel UX; pair-result card layout.

### 13c. Advanced — I8 "The Sealed Box" (black-box Credit, per-cell union)

Rendering: §12-I8. **Source mechanics:** black-box track + identifiability (E16), actual cause with non-actual contingencies (E9), budget as reasoning-forcing (E12), union granularity (E13).
**Knobs:** k=4, |I|=2, β=4, ♥2, mode ★, sealed lid.
**Start:** a ON@0,@1; b OFF@0..4; FIRE@4 starred. **Goal:** ★(0,a) ★(1,a) ★(3,b-at-OFF).
**Legal/illegal:** as I5; lane map absent.
**Expected path (4⚡, zero waste):** pair on b@3 (others as recorded) → toggled arm kills star ⇒ ★(3,b). Hold a@1 OFF as ghost, pair on a@0 ⇒ ★(0,a). Deduce ★(1,a) by symmetry of the two observed a-cells (or burn ♥ insurance). Submit union.
**Alternatives:** pair a@1 under a@0-OFF first; any order of the three tests.
**Deadlock/invalid:** spending pairs on a@2 (recorded OFF, not a candidate at actual value for this union — starring it fails actuality), or on cells past the curtain (refused).
**Feedback:** standard; on failed submit with a superset: "one of your stars never decided anything."
**Hints:** (1) "one lamp-killer hides at a moment where nothing seems to happen" (draws eyes to b@3); (2) reveals that the two a-cells *cover for each other* (relation, no cells named); (3) runs the b@3 pair, leaves the a-pair and placement to the player.
**Why fun:** detective closure — three different *kinds* of decider (lone pivot, mutual cover pair) under a sealed lid with exactly enough sparks. **Why faithful:** composes only spec structures (guard = Puzzle 4 pattern, overdetermination = Puzzle 3/5 pattern, black-box = §agent track); answer key checkable by the spec's finite grader. **Prototype next:** verify identifiability within β=4 (roadmap V5 analogue) before shipping.

---

## 14. Success and invalid-action renderings

```
SUCCESS (submit correct)                INVALID ACTION (soft refusal)
┌──────────────────────────┐            ┌──────────────────────────┐
│        ✔ SOLVED          │            │  lever behind curtain:   │
│   ⊛ → ☀ bursts gold      │            │  ░◉░ → ░●░ (springs back)│
│   marks settle & shine   │            │  curtain ripples, thunk  │
│   ⚡ left: 2 → mastery ◇? │            │  no ⚡ no ♥ consumed      │
└──────────────────────────┘            └──────────────────────────┘

FAILED SUBMIT (−1 ♥)                    SECOND SCISSORS (Prevent)
┌──────────────────────────┐            ┌──────────────────────────┐
│  ✗ not quite   ♥♥ → ♥    │            │ ✂ #2 hops back to tray   │
│ "could fewer marks       │            │ tray glows: "one only —  │
│  do the job?"            │            │  or press ⊘"             │
└──────────────────────────┘            └──────────────────────────┘
```

Refusals never punish; only submissions spend hearts (and only cranks spend sparks) — exactly the source's resource accounting.

---

## 15. Accessibility and all-ages design notes

No technical vocabulary anywhere (the words automaton, trace, cause, counterfactual, sufficient never appear; the prompts are "stop it / lock it / star it"). No reading required before play: I1 is solvable from the pulsing star and the single lever. No time pressure — the source defines none, so none exists. Fully self-paced; lever edits and mark placement freely reversible; reset is free; only crank and submit consume, both shown as physical meters (⚡, ♥) understandable pre-literacy. Object/state/action distinction by shape family (square lever cells, round lamps, token marks); ON/OFF by fill and lever posture, never color alone; edited-vs-recorded by the ◉ ring. Hints are opt-in and tiered. Early boards are tiny (1–2 levers, 2 columns). Rules never change across 100 levels — only the source knobs move. Input is tap/drag only. Experts get the β=0 no-crank mastery diamond and the all-causes variant — both straight from the spec's evaluation regimes.

---

## 16. Faithfulness checklist (player rule → source rule)

| Player-facing rule | Source mechanic | Evidence |
|---|---|---|
| Levers in rows, moments in columns; only levers move | inputs I vs outputs O; input-only intervention | E1, E5 |
| Same levers ⇒ same lamps, every crank | (F2) input-determinism | E2 |
| Any lever combination cranks fine | (F3) input-totality | E2 |
| Curtain after the star's column | causal window {0..k} | E6 |
| Flip counter counts levers only | count-only closeness on input cells | E3 |
| Crank costs a spark; result says "THIS TIME" | budgeted probe evaluates one scenario | E12, E18 |
| ✂ holds exactly one lever | minimal necessity causes are singletons (theorem) | E7 |
| ⊘ is a full, winnable answer | no-pivotal-cell verdict | E7, E20 |
| 🔒 can lock OFF levers; submit asks "ALWAYS?" | sufficiency over all admissible completions; ∀ is the grader's | E8, E18 |
| ★ needs a what-if pair (2 sparks) | AC2(a)+(b), contingency with non-actual values; pair pricing | E9, E12 |
| Marks sit on observed values only | actuality clause (AC1 / clause i) | E4, E9 |
| Marks can't touch lamps | anti-circularity (structural) | E4, E5 |
| Spam marks score 0; few hearts | subset-minimality; attempt rule | E13 |
| Witness OR union tasks; any correct witness wins | native set-valued grading | E13 |
| Lane map view-only (white-box) / sealed (black-box) | trellis depiction; two tracks | E16, E17 |
| No greedy "auto-prune" helper exists | non-monotonicity of validity | E10 |
| Difficulty moves only along §4 knobs | difficulty-knob table + trivial filter | E14 |
| No adversary, no timer, no randomness | one-player frozen device; exclusions explicit | E2, E11 |

Removed during design (untraceable): a "lamp-history scrubber" that previewed counterfactual lamps without cranking (would leak the grader's simulation for free, violating budget semantics); a combo meter (no source basis).

---

## 17. Rubric score

| Criterion | Score | Notes |
|---|---|---|
| A. Source faithfulness | **38/40** | Devices 1–6 are the spec's own worked puzzles; modes, budget, grading, verdict, tracks all verbatim. −2: I7/I8 are new devices — composed strictly from spec patterns and knob moves, but their keys still need the spec's checker run on them (the spec itself demands this for any instance). |
| B. Source-defined difficulty | **14/15** | Progression moves only along the knob table + track; trivial-instance filter respected (I4 demoted to unscored lesson). −1: closeness-order knob deliberately unexposed in core corpus. |
| C. Visual abstraction quality | **14/15** | Structure-preserving throughout (direction→left-right time; dependency→lane map & delay; conservation→sparks/flip counter; invalid→soft refusal). −1: Credit's ∃-quantifier remains the subtlest read despite the pair UI. |
| D. Clarity & learnability | **9/10** | I1 playable with zero text; staged mode unlocks; stamps separate evidence from proof. |
| E. Scalability & depth | **9/10** | Generator-backed instance family; nine knobs; two tracks; three scoring variants. |
| F. UI/UX & accessibility | **5/5** | Shape-coded, reversible, self-paced, small-screen plan. |
| G. Visual deliverable | **5/5** | Legend, base UI, core interaction, 8-instance gallery, success/invalid renders, knob trajectory, plus interactive HTML mockup (companion file). |
| **Total** | **94/100** | Thresholds met (A≥34 ✓, B≥12 ✓, C≥12 ✓, ≥80 ✓). |

Weaknesses to watch: (1) Credit-mode quantifier intuition needs playtesting; (2) I7/I8 keys must be certified by the formal checker before release; (3) black-box identifiability within β must be generator-enforced (spec roadmap V5).

---

## 18. Iteration 2 — The Deduction Layer

*Response to playtest critique: v1 was solvable by trial-and-error (flip until dark, mark the last flip); nothing let the player **see** the causal structure before acting.*

### 18.1 Diagnosis, in source terms

v1 shipped only the black-box panels and treated the crank as the sole information channel — but the spec's **primary track is white-box**: "the human sees the trellis … with the wiring diagram on the table beside you" (E16, E17). The trellis is the parity-game graph run through synthesis and unrolled in time; omitting it removed exactly the artifact that makes deduction possible. Turing Tumble works the same way: the whole mechanism is visible, so the player predicts the marble's path mentally and runs it only to confirm.

### 18.2 The information discipline (what may be shown for free)

The line between deduction aid and leaked simulation:

| Shown free (static / local — readable off the shipped device) | Never free (global — this is what a spark buys) |
|---|---|
| The full trellis: all nodes, all edges, all gate labels | The composed path under any *edited* lever setting |
| The observed run's blue path (it's the given trace) | Recomputed lamps for an edited setting |
| **Local gate evaluation:** under the current levers, each edge renders open (solid) or shut (dashed) — equivalent to reading one label against one column | Whether the *star* survives an edit |
| Which edges a lever gates (pulse on flip — syntactic `uses` info) | The grader's ∀/∃ verdicts |
| Lamp **staleness**: once levers differ from the last run, lamps dim to "stale" | — |

Local evaluation is honest: it is one label lookup the player could do by eye; the puzzle is the **composition** — chaining open gates across columns is precisely simulating the automaton, the ability the benchmark measures (E12: β=0 ⇒ "the player must simulate the device in their head"). The board hands the player the gears, never the path.

### 18.3 New core loop: read → chalk → crank → confirm

1. **Read** the wiring; find which gates the recorded blue path depends on (e.g. I2's "from q_a both b-gates reach ⊛" is now *visible* — the distractor is readable, not discoverable-by-trial).
2. **Flip** levers to a hypothesis; gates re-render open/shut locally; lamps go stale.
3. **Chalk** (new, presentation-layer): tap nodes to sketch the path you predict the marble will take. Free annotation — affects nothing.
4. **Crank** (−1⚡): the marble animates down the true path; chalk is settled — "◇ called it!" or "not quite." The spark now *verifies a stated prediction* instead of fishing.
5. **Mark & submit** as before; solving with zero sparks spent earns the ◇ pure-deduction diamond (the spec's β=0 regime as a mastery tier).

```
   moment 0        moment 1▼            ░ moment 2 ░
                 ┌──(q✲)── goal ◎       ░░░░░░░░░░░
        b ●  ════╡   ⊛                  ░ after the
   (q_a)═════════╡                      ░ star —
   ╱    b ○  ----┘  ← BOTH b-gates      ░ cannot have
(q0)                  reach the star:   ░ caused it ░
   ╲ a ○ ----(q0)---- b is idle. READ,  ░░░░░░░░░░░
              any     don't crank.
   levers:  a ● b ○   a ○ b ●   ░░
   DONE:      ·          ·      ⊛
```

### 18.4 Why this is the faithful version, not a softer one

The trellis-as-board makes the picture and the mechanics the same object: the mockup's simulator now *walks the drawn graph* (nodes/edges are the single source of truth), so the rendering cannot diverge from the device — mirroring the spec's identity between the anatomy figure and A_HOA unrolled. Determinism (F2) and totality (F3) become visible board properties: exactly one open gate leaves every node (verified mechanically for all 2^(|I|(n+1)) settings per level). The black-box track is unchanged — sealing the lid now *means* something: it removes the readable wiring and turns the same instance into the discovery task (E16), the knob v1 accidentally applied everywhere.

**Difficulty knobs gain their intended visual teeth:** #states = lanes on the board; transition count = edge density; k = columns of composition the eye must chain; β = how many predictions you can afford to verify. None of this adds mechanics — chalk, gate rendering, pulses, and the marble are presentation-layer (cosmetic per §7's closing rule); every consumable and every grading predicate is untouched.

### 18.5 Carried into the instance gallery

I1–I6 unchanged in content, now stated as read-first puzzles (I2's prompt: "from q_a, both b-gates reach it — read before you crank"). I7's two-flash counter and I8's sealed lid become the payoff of the layer: I7 is a pure reading puzzle over a 4-lane trellis; I8 is the same loop with the map withheld, where chalk becomes the player's hypothesis notebook.

---

## 19. Iteration 3 — Direct Manipulation: everything on the board

*Response to playtest critique: controls floated below the board with no visible link to the wiring; FLIP/MARK was a hidden mode; "crank" read as an abstract button. The automaton showed through.*

### 19.1 Three moves

**1. The switch is wired to its gates.** The detached lever grid is gone. Each switch (one per input × moment) sits inside the board under its column, and a colored wire — one color and dash pattern per input — runs from the switch up to every gate it controls. Flipping a switch flashes its wires and pulses its gates; tapping a *gate* flashes back down to its controlling switches. The mapping question ("which control belongs to which wire?") is answered by literally drawing the wire — the bomb-defusal read. Faithfulness: a wire is the static syntactic fact "input *i* appears in this transition's guard," part of the shipped device (E16/E17), revealing nothing the HOA text doesn't.

**2. The budget is a hopper of marbles.** "Crank ⚡" becomes a visible stack of marbles beside the start node; you tap one to drop it through the machine and watch it roll the gates you set. Spent marbles stay in the hopper, grey — the budget's history is physical. This is pure reskin of the probe (E12): same cost, same information, same determinism; but now "you only have so many tries" is something a child reads at a glance, exactly as Turing Tumble's marble supply does.

**3. The answer lives next to the thing it names.** No MARK mode: every switch carries a small socket showing a ghost of the active mode's token (✂/★). Tap the socket to set your mark. The submission *is* the board state — which is precisely the spec's requirement that answers be "read straight off the panel… gradable identically for people and agents" (E12, end).

A switch whose wires go nowhere (e.g. the in-window but inert button@1 in level 1) is now *visibly* unconnected — dead-wire deduction for free, replacing what used to require a wasted probe.

### 19.2 Player-language shift

The framing verb moves from "stop the flash" to **block / steer the marble's path** — Prevent is "flip ONE switch so the marble misses the star," Credit is "star every switch that steered it," Pin is "lock switches so it can't miss." Same predicates, maze language. The goal node ⊛ glows only when the currently shown run reaches it; lamps-as-a-strip return only for multi-output instances.

```
 marbles      moment 0      moment 1      moment 2▼      ░ moment 3 ░
  ◍                        ┌○ q_a ═══ b● ═╗⊛              ░
  ◍            (q0)═ a● ═══┘   ╚═ b○ ════╝(goal)          ░ curtain
  ◌ spent          ╲a○--------○ q0 --any--○ q0            ░
                     ┊╱wire      ┊┊╱wires
                  [a ●](✂)    [b ●](✂)     ← switches + sockets in-board
```

### 19.3 What did not change

The mechanics are untouched: same trellis-walk simulator (picture = device), same count-only Δ counter, same budget accounting, same native grader (singleton pivotality, ⊘ verdict, HP actual causation with AC2(b) robustness — re-verified against the paper's five worked answers after the rewrite), same curtain, same chalk prediction. Iteration 3 is entirely §7's presentation layer doing its job: recognition over recall, natural mapping between action and result, no control without a visible referent.

### 19.4 Open design questions for the next pass

(a) **Pin mode UI** — locks should clamp the switch handle itself (a padlock over the pill); prototype next. (b) **Multi-input gates** (level 3's "a● or b●") still carry text labels; candidate replacement: two wires entering a visible OR-junction bead before the gate, removing the last words from the board. (c) **Larger boards** (I7/I8): wires need lane-routing to avoid spaghetti — consider rendering wire bundles with a shared trunk per column. (d) Sound: gate clicks and marble rolls would carry the open/shut distinction non-visually.

---

## 20. Iteration 4 — The road is the control, the cut is the answer

*Response to playtest critique: (1) semantics lived in text labels ("a● or b●"); (2) parallel transitions shared one visual path; (3) control wires won't scale; (4) experiment-then-mark was two systems where one belongs — "you should just cut the wire."*

### 20.1 One strand per input choice

The trellis now draws **one road per (junction, input valuation)** instead of one edge per guard formula. Level 3's single edge labeled "a● or b●" becomes a visible *fan*: three separate roads into the star, one escape road out. Each road carries a wordless **dot badge** — one colored dot per switch it reads (filled = on, hollow = off; absent dot = that switch is ignored on this road). Consequences:

- **Overdetermination is geometry.** "No single flip escapes" is readable as "every neighboring road still lands on the star" — the ⊘ verdict becomes something you *see*.
- **Irrelevance is geometry.** A switch that doesn't matter simply has no dot on the roads that decide — level 2's distractor is two twin roads (b●/b○) arriving at the same place.
- **Parallel transitions get parallel strands** (distinct bends), never one overloaded line.
- **Labels are gone.** The only text left on the board is junction names, removable too.

Fidelity note: this is the same trellis at input-valuation resolution — each strand is one transition of A_HOA under one assignment of that step's inputs. Branching factor per junction is 2^(inputs read), which the source's *trace diversity* and *transition count* knobs already govern; the fan IS those knobs made visible.

### 20.2 Tap the road; siblings re-gate together

Tapping a road sets that moment's input cells to the road's valuation. All roads at that moment re-render in sync — shared inputs across lanes (the thing the wires used to point at) are now *felt* as linked gates rather than diagrammed. The switch widgets, control wires, and sockets are deleted entirely; nothing on the board exists except junctions, roads, the hopper, and the star.

### 20.3 The submission is the board: diff-as-answer

The mark step is removed. **Your answer is whatever differs from the recorded run when you press SUBMIT** — shown live as an answer strip of chips. In Prevent this is exactly "cut the wire": switching off the recorded route severs it (a visible ✂ snip at the break), the marble's escape is on the board, Δ1 is the claim. In Credit, you leave exactly the deciding cells changed. This is *more* faithful than sockets were: the spec's answer format is literally a set of (timestep, input) cells "stated at actual values — the grader supplies the flips" (E12/E13); the diff names precisely those cells. Guard rails: Prevent refuses Δ≠1 (or take ⊘); minimality and correctness remain the hidden grader's.

Trade-off, recorded honestly: in Credit, contingency experiments and the final claim both live in board state, so the player must tidy the board to exactly their claim before submitting ("leave the board showing your claim"). Playtest whether this reads as natural cleanup or as friction; fallback is a one-tap "keep as answer" pin on the answer-strip chips, not a return to sockets.

### 20.4 The frame is a skin

The cut gesture is theme-agnostic, as the playtest noted: bomb wire to snip, vine to prune, rail switch to throw, circuit trace to break — all the same geometry (roads, junctions, one starred terminal, a budget of test runs). The shipped game can offer skins freely because §7's meaning map binds mechanics to *structure* (strands, dots, cuts, marbles), not to any one fiction. GLOWBOX remains the neutral reference skin.

### 20.5 Verification

After the rewrite: determinism (F2) and totality (F3) are now **structural** — the test suite enumerates all 2^(|I|·(n+1)) settings per level and confirms exactly one strand matches at every junction; graders re-verified against the paper's five worked answers (pivots, ⊘ cases, and credit unions including the cross-time {(0,a),(1,b)}).

### 20.6 Scaling note (replaces the wire-routing concern)

Strand count grows as 2^(inputs *read at that junction*), not 2^|I| globally — synthesized controllers read few inputs per state, and the source's trivial-instance filter plus knob stratification control the rest. For dense instances (I7/I8): collapse unread-input strands (already done — no dot, one strand), bundle same-target strands with a shared trunk that splits near the badge, and let the curtain hide post-window structure. The failure mode to watch is >8 strands at one junction; the generator should report max fan-out as a difficulty/legibility statistic alongside the source knobs.

---

## 20.7 Iteration 4.1 — Gesture inversion: cut the dot, don't choose the detour

*Playtest: "I have to click the alternate path to reroute instead of clicking the path I want to turn off… in Long Echo I should turn off the first two wires, not reroute-then-cut-the-cross-wire. Make sure we're not drifting off spec."*

**Spec-drift audit, first.** The graded object never moved: in every version the submission is the set of changed input cells vs. the recorded run, candidates are cells at actual values, distance is count-only, and the Long Echo key is exactly {(0,a),(1,b)} — re-verified after this change. What drifted was the *gesture*: v4.0 expressed "remove this cell's value" as "select the sibling road," which inverts the player's causal intent (choosing a replacement instead of negating a cause) and, in Long Echo, makes the answer feel like path-planning rather than cutting the wires that carried the cause. Gesture-level drift matters even when the math doesn't move, because the gesture is the player's theory of what they're doing.

**Fix.** The dot *is* the cell, so the dot is now the control: **tap a dot to flip that switch cell** (cut it off its recorded value, or restore it). All roads held by that cell re-gate at once; a ✂ appears where the recorded route is severed. On one-dot roads, tapping the road body equals tapping its dot. Nothing else changed: diff-as-answer, ⊘, marbles, chalk, grading all identical. Long Echo now plays exactly as the user described the true solution: cut the a-dot on the first taken road, cut the b-dot on the second — board shows two snips, submit.

A pleasant consequence in The Fan: cutting the a-dot on the taken three-dot... two-dot road visibly fails (the marble's lane re-gates onto the a○b● road, still starbound), and so does cutting b — the player *performs* the overdetermination argument dot by dot, which is precisely the two single-flip checks the ⊘ verdict quantifies over.

## 20.8 Iteration 5 — Guard wires: dots only where the device actually listens

*Playtest: "Why does each wire have two switches? Cutting one wire shouldn't change another dashed wire to solid — all open connections should just be solidly connected."*

Both symptoms came from drawing strands at *valuation* resolution: every road carried the full input assignment (hence two dots on every wire of the Fan), and exactly one strand per junction was "selected," so flipping a switch *moved the selection* — dashed wires turning solid on their own. v5 redraws the trellis at **guard** resolution, which is what the automaton actually reads:

- **A wire carries only the literals that hold it open.** The Fan's three two-dot strands collapse to *two one-dot wires* — a's wire and b's wire, independently feeding the star. Overdetermination is finally drawn as what it is: two independent carriers. (Multi-dot wires still exist and now *mean* something: Puzzle 4's guard is one wire held by two dots, req filled + cancel hollow — a wire genuinely held by two switches.)
- **Solid = carrying. Cuts are local.** A wire is solid iff all its dots are satisfied; tapping a dot re-gates only the wires that read that cell. Nothing else changes appearance. (The one principled exception: a cell can appear with opposite polarity on two wires, which then visibly trade — same colored dot on both, readable.)
- **The gutter.** Where the marble falls when nothing carries it is no longer a peer "road" that turns solid — it is a faint, invariant dotted gutter (the residual transition), lit gold only when a run actually takes it. Cutting wires never turns anything on.
- **Uncuttable wires teach irrelevance.** Level 2's distractor moment is now a single wire with *no dots* — nothing holds it, nothing can cut it. "b doesn't matter" is read off the board in one glance.

**Fidelity.** Guards are exactly the HOA transition labels (Boolean formulas over AP — E1); drawing one wire per disjunct with only its read literals is the standard DNF rendering of those labels, and synthesis yields sparse guards, so dot counts stay low (this also retires most of §20.6's fan-out worry). Determinism and totality remain structural and machine-checked: the test now verifies that all simultaneously-carrying wires from a junction share a target and that a gutter exists exactly where needed, over every possible setting; graders re-match the paper's five worked answers. The cut gesture, diff-as-answer, ⊘, marbles, chalk, and grading are unchanged.

## 20.9 Iteration 5.1 — The tape returns: restoring B2 and the wrong answers

*Playtest: "It's not visually clear that the q0s are connected. Also, right now the only available choices are the answers — there are no incorrect choices."*

The second observation caught genuine spec drift. The spec's board shows four things, and **B2 — the switch panel** (the full observed input grid) is one of them. Iterations 4–5 deleted it: once interaction lived only on wire dots, the clickable cells collapsed to the cells the device *reads* — which, on guard-minimal wires, is approximately the answer set. The candidate space K is supposed to be **all in-window cells** (that's what trace diversity counts, and what makes minimality grading bite: "spam every cell scores 0" is vacuous if only the right cells are tappable).

**Fix 1 — the recorded tape.** A compact punch-tape strip under the trellis shows every switch cell at every moment at its current value (color/fill grammar identical to wire dots), each tappable to cut (blue ring + ✂) or restore. Tape cells and wire dots are the same cells, synced both ways. Now level 5 offers a@1, a@2, b@0, b@2 as live wrong choices; level 1 regains its inert-cell lesson (a@1 is cuttable and useless); curtained cells refuse with the curtain card. The wires remain the deduction surface — the tape is the *claim* surface, which is precisely the spec's division (light/switch panels = observation, trellis = white-box wiring).

**Fix 2 — rails, not ghosts.** Unconditioned transitions (the q0→q0 connections and other drains) were styled nearly invisible, so the lower lanes read as disconnected. They are now thin solid rails: clearly connected, visibly switchless (no dots = nothing to cut), still lighting gold only when a run takes them.

Verification unchanged and re-run: determinism/totality structural checks pass over all settings; graders match the paper's five worked answers.

## 20.10 Iteration 6 — One theme, almost no words, and the right headline objective

*Playtest: (1) "wires don't carry marbles — you've confused your themes"; (2) "way too much text; the design needs to speak for itself — one objective line, shown once"; (3) "'cut one wire' is a singleton solution; TCE isn't limited to singletons."*

**One physics.** The skin is now coherently electrical: a **pulse** travels the wires to a **bulb** (⊛); the probe budget is a **battery** (tap to send a test pulse; pips drain). Cutting wires, dots as contacts, plain rails, the tape — all native to circuits. Marbles, hoppers, and gravity are gone. (Per §20.4 this is a skin swap only; no mechanic moved.)

**Text austerity.** Deleted: the explainer paragraph, the footer essay (now a code comment), per-level prompts, button prose, verbose error cards. What remains: one objective line **per mode, shown only on that mode's first level** —

> ✂ *Keep the bulb dark — one cut. (⊘ if no single cut can.)*
> ★ *Leave cut exactly the cells that lit it — causes can be many.*

— plus the two-chip fill legend and single-word feedback. Everything else is taught by the board: the tape invites tapping, cuts show ✂, the battery shows ⚡, the bulb glows or doesn't. Tabs carry the mode icon so repeated modes need no text at all.

**The singleton clarification (fidelity, not just framing).** "One cut" is the *Prevent* objective, and its singleton shape is a theorem, not a design choice: under (F2)–(F3) every minimal count-only necessity cause is a singleton or the verdict is ⊘ (Prop. pivotal). But Prevent is the spec's *diagnostic* mode — TCE's core object is Credit (actual causation), which is genuinely multi-cell (the union task; Puzzles 3 and 5 have two-cell answers across switches and across time). The Credit objective line now says so in seven words ("causes can be many"), and the mode ordering — three ✂ levels, then ★ — is the spec's own pedagogy: necessity first because it's the cheapest entry point, actual causation as the destination. A shipped corpus would weight toward Credit, exactly as the paper designates TRACE-Credit the core configuration.

Re-verified post-rewrite: structural determinism/totality over all settings; graders match the paper's five answers.

## 20.11 Iteration 7 — One question: the TCE question

*Playtest: (1) the tape reads as the detached toggles again — wires should be the only interactive surface; (2) "every possible input should be interactive, or there is no puzzle"; (3) no letter labels; (4) why is the curtained moment there at all; (5) two unexplained objectives — "TCE asks what the cause is, not whether there is a single cause."*

**The mode decision (the big one).** The player-facing game now asks exactly one question on every level: **★ leave cut exactly the cells that made it shine — causes can be many.** That is TCE itself: the Credit object (HP actual causation) at per-cell-union granularity, the mode the spec designates as core and conjectures to match TempoBench's labels. *Prevent* — "is there a single cut?" — is the paper's theoretical diagnostic, not a player question; carrying it into the game forced an unexplained objective switch and the ⊘ verdict button. Both are gone from the player surface (they remain benchmark configurations for agent evaluation, as the spec defines). The payoff is conceptual cleanliness: overdetermination is no longer a special verdict to declare — it is simply a puzzle whose answer has two cells. You cut one carrier, test, the bulb still shines, and the *aha* is "cut both." The collapse phenomenon the paper proves (Prop. pivotal) is now something the player experiences rather than labels.

**Wires are the only interactive surface — and wrong choices live on wires.** The tape (iteration 5.1's B2 strip) is deleted again, this time correctly: instead of a separate claim surface, the four devices are redesigned so that **every routing cell appears as a dot on some wire**, including distractor cells, which sit on the *counterfactual* (dashed) wires — the routes not taken. The machine-checked guarantee per level: no uninteractive routing cell, and at least one interactive decoy (L1: one decoy; L2: three; L3: a third switch on a dead-end wire; L4: two). The earlier "only choices are answers" problem is solved inside the wiring, not beside it. One honest note: cells in the effect column itself (t = k) are inert in this Moore-style trellis rendering and are not shown — the spec's trivial-instance filter independently discards same-column causes, so nothing gradable is lost.

**Letters and curtain deleted.** A switch is identified by its color alone (the legend is two unlabeled chips: filled = on, hollow = off); junction names are gone; boards now end at the effect column (n = k), so no curtained dead column appears. Trace-length distractor context (n > k) remains a difficulty knob for the full game; when used, post-window structure should be *cropped*, not dimmed — the curtain was answering a question no player asked.

**Verification.** New suite per level, over all 2^(|I|·(n+1)) settings: determinism (simultaneously-open wires agree on target), totality (a rail exists exactly where needed), full interactivity of routing cells, presence of decoys, and union correctness — L1 {a@0}, L2 {a@0}, L3 {a@0, b@0}, L4 {a@0, b@1}.

## 20.12 Iteration 8 — Root cause, not symptoms: a coherent board ontology

*Playtest: "Why do switches have two colors on one wire? Why does a dashed wire coexist with a switchless solid line? The charge meter has no button. A three-dot wire has no reason. You keep introducing a new problem every time you fix one."*

**Self-critique first (all four observations were correct).** (1) The two-dot wire in level 1 and the three-dot wire in level 3 were *fabricated guards*: I invented transitions the device had no reason to have, purely to manufacture wrong choices — corrupting the machine to patch the UI. (2) The dashed-wire-plus-rail pair to the same node was an unminimized guard plus a leftover drain; minimized, it is one wire with one dot. The rail/wire distinction was scaffolding for my own redundancy. (3) The battery silently became the run button in iteration 6 with no affordance. (4) The meta-failure: each iteration patched the previous symptom locally instead of re-deriving the board's ontology, so the decoy requirement collided with guard-minimal wires and I resolved it by inventing structure.

**The ontology, derived once.** Three kinds of object, each existing only when the device gives it meaning:

- **Fork** — a junction read by one switch. Drawn as *one* tappable dot at the junction mouth (fill = current value), two branches with small fixed value-tags. Tapping throws the points: the engaged branch is solid, the other dashed, ✂ on a severed recorded branch. "Dashed becomes solid" is now visibly *the player throwing a lever*, not spooky action.
- **Guard wire** — a wire held by more than one dot exists *only* when the device truly conjoins switches, and then the dots are the wire's meaning (level 3's dark wire: "the pulse falls here only when both are off" — the escape condition, which is also the witness that both cells are causes).
- **No rails, no fabricated guards.** Every junction is covered by its forks/wires alone (totality is machine-checked); nothing switchless runs parallel to something switched.

**Honest decoys.** Wrong choices are now real machine structure: switches that genuinely reroute the pulse *between states with the same outcome* — several states may flash the same bulb, so a decoy fork visibly moves the pulse without deciding the light. This is not a trick; it is exactly the spec's #states/transition-count difficulty knobs (richer internal dynamics to simulate). Level 2 has two decoy forks (b at moment 1 reroutes between two flashing states; a at moment 1 reroutes between two dark ones); level 4 has one, and its decoy (a@1 on the high road) interacts with the cause structure: whether b@1's fork matters depends on which lane a@0 sent the pulse down — the contingency structure of the actual cause, drawn.

**Battery = TEST.** The battery is labeled TEST, hover-highlights, and its pips are the budget. One word of text, justified by the affordance failure.

**Verification (re-derived for the no-rail ontology):** totality and determinism now mean "every junction has a carrying wire under every setting, and all carrying wires agree on a target" — checked over all 2^(|I|·(n+1)) settings per level; unions: L1 {a@0}, L2 {a@0} (decoys a@1, b@1), L3 {a@0, b@0}, L4 {a@0, b@1} (decoy a@1).

## 20.13 Iteration 9 — The routing ontology (the correction the design needed)

*Playtest raised twelve issues; read together they exposed one root error: a "cut the wires" fiction stretched over a system whose true semantics is routing. Point 12 named it: "unless you explicitly change it from cutting wires to changing the input — then we're thinking a different design language, maybe flipping a switch to reroute a train."*

### 20.13.1 The root error, stated plainly

In the source, an input cell is binary and the controller is input-total (F3): flipping a cell never *removes* a transition — it *selects the other one*. "Cutting" was a lie at the edges, and every visual paradox flowed from it: dashed wires "turning on" (the sibling engaging), an off-wire looking live (observed-path styling), solid-vs-dashed meaning three different things (carrying / recorded / shown-run). The faithful physical model of a deterministic, input-total binary machine is **a railway switch: every junction routes one of two ways, always; nothing is ever off — just not where the train goes.**

### 20.13.2 Point-by-point resolution

| # | Issue | Resolution |
|---|---|---|
| 1 | New junction dot | Deleted. The junction **is** the lever; its alignment is its state. No dots exist anywhere. |
| 2 | Dot sizes inconsistent | Moot — all dots, tags, and badges deleted. |
| 3 | Battery without purpose | Deleted. In the white-box track the wiring is fully shipped, so the board may simulate live; a budgeted test is meaningless there. β remains a difficulty knob of the black-box and agent tracks (where the machine is hidden and probes are the only information channel). The human-scored resource is attempts (♥), per the spec's attempt rule. |
| 4, 8 | Two lit bulbs | The spec has **one lamp**, possibly flashed from several states. The board now has one bulb; flash-states' tracks converge into it. Gold goal-nodes abolished. |
| 5 | Dashed line into a lit bulb | Gone with #4: tracks into the bulb are just tracks; the bulb alone shows lit/dark, live. |
| 6 | Two-switch junctions | Abolished structurally: compound guards are drawn as **chains of one-input junctions** (Shannon expansion — the same transition function, decomposed). No multi-dot anything can recur at any difficulty. |
| 7 | Cut colors uninformative | Correct — per-switch colors carried no information here (no cell is tested at two junctions). All color coding deleted. (When higher-tier instances test one cell at several junctions, those junctions throw together and share a tint — color returns only when it means linkage.) |
| 9, 11 | Solid/dashed inconsistent; "is off→dashed even coded?" | One coded rule now: **aligned branch = connected and full-strength; unaligned branch = visibly disconnected at the junction (gap) and dimmed.** The live route adds a single gold flow animation. Three visual states, one source of truth (the current grid). |
| 10 | White vs blue wires | Blue observed-path overlay deleted. The recorded run **is** the board's initial alignment; a blue ring marks each junction thrown from recorded — which is simultaneously the claim display. |
| 12 | Cut vs reroute logic | Adopted wholesale: the verb is **throw**, the answer is the set of thrown junctions, ✂ is gone. Identical graded object (diff from recorded = cells at actual values, grader supplies flips). |

### 20.13.3 What the live board changes — and the lesson it bought

With routing alignment visible, the route and bulb are deducible by eye, so they update live (white-box; the spec's β=0 regime is exactly "simulate the shipped device yourself"). Crucially this makes **darkening the bulb explicitly *not* the goal** — the goal is naming every decider, and the level set now teaches that distinction mechanically:

- **L3 (the gate, Puzzle-4 structure at k=1):** either single throw darkens the bulb, but the union is **both** — submitting the one throw that darkened it fails. Aha: "what broke it" ≠ "what decided it." |
- **L4 (overdetermination, Puzzle 3):** *no* single throw darkens it; each cause is pivotal only with the other thrown — the player physically performs the contingency. |
- **L5 (Puzzle 5):** deciders at two different moments, plus a decoy junction that reroutes between same-outcome tracks (the spec's #states/transition knobs as honest distractor structure).

Machine-checked per level over all settings: every route terminates (totality), every cause is throwable at some junction, decoys present where intended, unions = L1 {a@0}, L2 {a@0}, L3 {a@0, b@0}, L4 {a@0, b@0}, L5 {a@0, b@1}.

### 20.13.4 Board inventory after iteration 9

Circles (junctions — tappable), tracks (with alignment gaps), one bulb, small ground stubs, blue claim-rings, ♥, ↺, SUBMIT, and a single objective sentence on level 1: *"Throw exactly the switches that decided the light."* Nothing else. Eleven UI concepts from iterations 2–8 (lever grids, control wires, sockets, tape, marbles, battery, chalk, per-switch colors, value dots, observed-path overlay, cut glyphs) are deleted.

## 20.14 Iteration 10 — Level 3 was not a mistake; diff-as-answer was

*Playtest: "Throwing the first switch darkens the bulb, but the game says 'not quite' and demands the second switch with no apparent reason. What is the design trying to show? What is the underlying HOA? Is it a mistake example?"*

### 20.14.1 The underlying device

Level 3 is the paper's **Puzzle 4 — the gate** (request/cancel), lifted to k=1 to clear the trivial-instance filter: the transition into the flashing state requires switch-1 ON **and** switch-2 OFF. The paper's checker-verified verdict for exactly this structure: flipping *either* cell alone kills the flash, so **each is a singleton actual cause** (pivotal at the other's actual value, W=∅), and the per-cell union Γ^ac — the granularity TempoBench grades and the object conjectured to match CORP's key — is **both cells**. "What can break it" (either, alone) and "what decided it" (both) genuinely differ on gate instances. That divergence is a feature the benchmark exists to probe, so the grading is correct.

### 20.14.2 The real flaw: the claim cannot be a board state

Diff-as-answer assumed the answer set is expressible as one board configuration. The verification table shows where that assumption breaks: on L1/L2/L4/L5 the union happens to equal the unique minimal darkening set, so leaving the board "showing your claim" worked *by coincidence*. On the gate it cannot: {both thrown} is not a minimal darkening configuration, and in it the second junction sits on an unvisited branch — the "no apparent reason" the playtest saw. Structurally: **a union of causes is justified by several different experiments, and one board state cannot witness two experiments.** The spec knew this all along — its own design separates the two: Credit answers are *"marked cells,"* demonstrated by *pairs of runs* (candidate in place vs. toggled). Diff-as-answer was the drift, introduced in iteration 4 and surviving because the simple instances masked it.

### 20.14.3 The repair: throw to test, star to claim

- **Throw** (tap a junction / a track): free experimentation; route and bulb update live; ↺ restores the recording.
- **Star** (tap the small ★ beside a junction): the claim. Stars persist across ↺ — knowledge survives the experiment that produced it. The submission is the star set, graded against Γ^ac as before.
- The blue ring now marks only "thrown from recorded" (experiment bookkeeping); the ★ is the only graded object.
- Discoverability: the first time the player's throw toggles the bulb in level 1, the star slots pulse once — the demonstration moment is exactly when a star becomes meaningful (the spec's pair-of-runs, enacted: throw → light toggles → that junction decided it → star it → restore → hunt on).

Gate level, replayed under the repair: throw switch 1 → dark → ★ → ↺ (lit again) → throw switch 2 → dark → ★ → ↺ → submit {★,★}. Every star now has an *apparent reason*: the player earned each with a visible toggle. The bulb is the instrument; the stars are the answer; darkening was never the goal.

Verification re-run after the change: graders and unions identical (the graded object never moved — only the gesture that names it).

## 20.15 Iteration 11 — Witness grading: any true cause wins

*Playtest: "You're forcing the player to identify two independent minimal causes, not one. The spec allows any minimal answer to count… with countless possible answers this is not a sustainable modality of play… The issue isn't the design — it doesn't need a star. The issue is the grading logic when there is more than one possible answer."*

**The spec re-read confirms this.** The scoring section defines three task variants and is explicit about the witness task: *"submit one set; full credit iff it is correct **and subset-minimal** … the checker accepts **any** correct witness, not a fixed string,"* with the recommendation *"witness or per-cell union … depending on whether the corpus targets a single explanation or TempoBench-style per-cell scoring."* The spec also motivates set-valued grading precisely because *"answers are genuinely non-unique"* — grading against one stored answer "would mark a correct minimal answer wrong for merely differing from it." I had locked the game to the union variant; for human play targeting a single explanation, the witness variant is the spec-sanctioned choice, and the only scalable one: on rich instances with many incomparable causes, demanding the exhaustive union turns play into bookkeeping (and iteration 10's stars were UI built to service that wrong choice).

**The change is grading-only.** Stars deleted; iteration 9's interaction restored verbatim (throw to test; thrown set = claim; ↺; live bulb). The grader now evaluates the thrown set as a witness: it wins iff it is **one genuine minimal actual cause — any of them**. Implementation generalizes the HP check from singleton candidates to candidate *sets* (AC2(a) necessity flipping the whole set under some contingency; AC2(b) robustness; AC3 minimality checked over all proper subsets), which also makes jointly-acting multi-cell causes gradable when instances have them.

**Replay of the contested levels.** Gate (L3): throw either switch → dark → submit → ✔ (the other switch is an equally correct answer; both pairs rejected as non-minimal — the spec's "spam scores 0"). Overdetermination (L4): {a} alone or {b} alone wins — including with the bulb still lit at submit, which is the level's real aha: a switch can have decided the light even though throwing it alone doesn't darken it (its backup covers). Machine-enumerated over all possible submissions per level: L1 {a₀}; L2 {a₀} only (decoys rejected); L3 {a₀} or {b₀}; L4 {a₀} or {b₀}; L5 {a₀} or {b₁} — and nothing else.

**Where the union variant lives now:** in the benchmark configuration for agents (TempoBench-style per-cell scoring), as the spec assigns it — not in the human play loop.

## 20.16 Iteration 12 — Which Halpern–Pearl? Accept either reading

*Playtest: on the overdetermination level, throwing both switches (bulb dark, Δ2) was rejected. "This is the correct answer… we need both 'any one genuine minimal cause' AND multi-switch causes to work. Fixing 3 shouldn't have broken 4."*

### 20.16.1 What actually happened

Nothing in iteration 11 broke level 4 — the grader faithfully implements the variant the paper picked, and that variant *rejects* the pair. The source is explicit (mainTB, "Why this is Halpern–Pearl, and which Halpern–Pearl"): it adopts the **original/updated** HP definition (contingencies may take non-actual values), under which overdetermination's causes are the two **singletons** and the pair fails AC3 minimality — and it states the road not taken in so many words: *"under the modified definition Puzzle 3's cause would be the joint pair {(0,a),(0,b)}, not the two singletons we report."* The player's submission was precisely the **modified-variant** answer. So this was neither a code bug nor a wrong instance: it was the grader silently enforcing a variant choice the player cannot perceive, and rejecting an answer the source itself certifies as the other legitimate HP reading. (The paper's own confidence in its choice is conditional — alignment with CORP's contingency discipline is open roadmap item V2.)

### 20.16.2 The repair: dual-reading witness grading

On exogenous input cells the modified definition collapses to something perfectly playable: **a minimal set of throws that extinguishes the bulb** (joint flip with everything else as recorded, no proper subset sufficing). The grader now accepts a witness under **either** reading:

- **Decider** (original/updated): one minimal actual cause — AC2(a) necessity under some contingency, AC2(b) robustness, AC3 minimality. May leave the bulb lit (overdetermination's deep aha).
- **Extinguishing set** (modified): a subset-minimal joint flip that darkens the bulb — the natural discovery path.

Supersets fail under both (minimality is shared); decoys fail under both. Failure feedback now distinguishes the one coachable case: if a correct witness hides inside a too-large submission, the card says *"A smaller claim is hiding in yours"* — the spec's minimality rule, taught instead of enforced silently.

### 20.16.3 Verified acceptance sets (full enumeration of every possible submission)

| Level | Accepted | Rejected (examples) |
|---|---|---|
| 1 | {a₀} (both readings) | a₀+decoy pairs |
| 2 | {a₀} (both) | decoys a₁, b₁ and all pairs |
| 3 gate | {a₀} or {b₀} (both readings agree) | {a₀,b₀} — smaller claim hides inside |
| 4 overdet. | {a₀} (decider) · {b₀} (decider) · **{a₀,b₀} (extinguish)** | triples/supersets |
| 5 echo | {a₀} (decider) · {b₁} (decider) · **{a₀,b₁} (extinguish)** | decoy a₁, supersets |

### 20.16.4 Faithfulness accounting

For a shipped benchmark corpus, one variant must be declared per corpus (the paper chooses original/updated pending V2); dual acceptance is the right call for the *human game*, where the variant distinction cannot be communicated nonverbally and both readings are spec-documented members of the HP family over the same device. The benchmark configurations section of the doc stands unchanged; this is a play-surface grading policy, recorded here as a deliberate, source-grounded deviation-with-justification rather than silent drift.

---

## 21. Next prototype tasks

1. Run the spec's finite checker over I7/I8 to certify their answer keys in all three modes (per §"Computing and certifying the answer key").
2. Playtest the what-if pair UI (Credit) with children and adults; measure whether "THIS TIME / ALWAYS?" stamps prevent the one-run-proof fallacy.
3. Implement the deterministic replay engine + native grader behind the HTML mockup for all 8 instances (mockup currently covers I1, I3/I5, I2).
4. Build the lane-map renderer from HOA input (white-box track) with the trellis layout of the spec's anatomy figure.
5. Enforce black-box identifiability within β at generation time before shipping any sealed-lid instance.
6. Calibrate spark budgets per instance against the source rule: humans solve reliably, cheapest brute-force probing does not.
