# TRACE — Pre-Build Validation Plan

*An actionable, peer-review-grounded plan for the work that must be completed (or explicitly scoped out) before the production builds of the human game, agent harness, and benchmark corpus are valid. Organized as gates; each item is falsifiable with a stated success criterion. Items marked **[mainTB Vn]** are the paper's own roadmap obligations; items marked **[G]** are gaps surfaced by the demo-build process or by a peer-review pass of mainTB.*

---

## 0. Overall assessment (reviewer's summary)

mainTB is unusually honest about its own conditionality — it states outright that *"every TempoBench-equivalence claim rests on (F1)–(F3) and Conjecture 1, to be discharged by roadmap steps V1–V2"* and that if either fails, TRACE "stands as an independent trellis-causation benchmark." A rigorous reviewer would accept the formal core (the finite specialization, Prop. pivotal, the three-object taxonomy) but would treat the following as **blocking** for any claim of TempoBench parity or benchmark validity: the unverified CORP correspondence, the unaudited F1–F3 assumptions, the unresolved HP-variant discipline (which the demo build independently rediscovered as a *gameplay-visible* fork), the absence of any HOA-derived worked instance (all five worked puzzles are hand-built), and the unmeasured grader complexity envelope. None are fatal; all are checkable; the paper survives review only with V1–V3 discharged and claims conditioned accordingly.

---

## Gate A — Semantic foundations (blocks everything)

> **STATUS (2026-06-10, see `Verification/GateA/results/REPORT.md`):**
> - **A1: PASS** (checker self-validated on 6 labelled controls incl. named-label HOA syntax; the one real TempoBench artifact passes F1op/F2/F3 at 1.0). *Remaining:* re-run over the full corpus when delivered.
> - **A2 definitional: RESOLVED** — CORP uses Halpern's *modified* variant (output-resets to actual values, toggleable); Conjecture corp is definitionally unsupported as stated (`A2_definitional_note.md`).
> - **A2(ii) empirical: MEASURED(n=1), per-cell F1 = 1.0 both variants.** *Remaining (external):* full TCE dataset — pulled from HuggingFace as outdated; N. Holzer is re-preparing it (ETA days). On arrival: drop JSONL in `GateA/external/`, re-run; the decisive rows are the overdetermined ones. Also confirm with him whether keys were generated with CORP contingencies on or off.
> - **A3: PASS + decision record issued.** Benchmark corpora declare ONE `hp_variant` (TempoBench-alignment ⇒ `modified`, per A2 definitional; credit-assignment stance ⇒ `original`; the alignment default is finalized at A2(ii)). *Update (2026-06-12):* with the mode-explicit construction adopted (see Gate C status), the canonical human CREDIT IT surface poses only the original/updated object as a demonstrated decider — dual acceptance no longer governs the canonical play surface; it survives only in the labeled sandbox archive (`TRACE_play.html`).
> - **A4: PASS — RESOLVED in production:** Mealy edge-rendering shipped (`build_player.py`/`build_modes.py` draw and test the column-k cells the device reads); any remaining undrawn cell is proven effect-irrelevant per instance by Gate C P_CAND (release-blocking CI).
>
> **Gate B is unblocked.** Per the dependency rule below, only *TempoBench-alignment claims* (and the corpus-default `hp_variant_policy` in A3) wait on A2(ii); grader, generator, parity, and identifiability work consume our own oracle and artifacts. Every B-deliverable that touches alignment carries the conditional wording mainTB already uses.

### A1. Artifact audit: F1–F3 **[mainTB V1] — Priority: HIGH, first**
- **Problem.** All equivalence claims, Prop. pivotal's collapse, the engine's totality assumption, and the game's "throw always works" physics presuppose: (F1) the released HOA files are implementations, not specification monitors; (F2) input-determinism; (F3) input-totality. None has been checked against actual TempoBench artifacts. F1 is the riskiest: if artifacts are monitors, the construction "does not apply to those artifacts" (mainTB's own words).
- **Action.** Parse every released TempoBench HOA file. Per file, mechanically test: F2 (for each state, input valuations select ≤1 successor with a unique output completion); F3 (each state, every input valuation has a defined successor); F1 (structural heuristics: I/O partition preserved from TLSF, transducer shape, no acceptance-restricted behavior; corroborate by re-synthesizing a sample from the SYNTCOMP source with ltlsynt and diffing languages).
- **Success.** Quantified pass rates per assumption; failing files quarantined; Prop. pivotal and Conj. 1 scope statements rewritten with the measured fraction. **Engine consumes only the passing set.**

### A2. CORP / TempoBench correspondence: Γ^ac vs shipped keys **[mainTB V2] — Priority: HIGH**
- **Problem.** The central alignment claim is a *conjecture*. The paper's chosen HP variant (original/updated, non-actual contingencies) is asserted to match CORP's discipline but flagged as unverified — there is even a TODO comment in the source about checking Coenen et al.'s contingency semantics.
- **Action.** (i) Resolve the definitional question first: extract from Coenen et al. (ATVA 2022) and the CORP paper whether contingencies may take non-actual values; record the answer in mainTB at the existing TODO. (ii) Run TempoBench's Algorithm 1 (`corp`) on a stratified sample of A1-passing instances; compute Γ^ac with our oracle; compare per-cell.
- **Success.** Published agreement rate with every disagreement dissected as a failure case. On systematic disagreement: revise Def. actual (or its variant) or *narrow the claim* to "independent trellis-causation benchmark" — and update the game's `hp_variant_policy` defaults accordingly. **The demo's iteration-12 finding makes this urgent:** the variant choice is not academic — it decides which player answers are correct on every overdetermined instance.

### A3. HP-variant decision record **[G — from demo iterations 11–12] — Priority: HIGH (paired with A2)**
- **Action.** After A2, issue a one-page decision record: which variant each consumer uses (paper default original/updated for benchmark corpora; dual-acceptance for human play as documented in the implementation spec §4.2), and add to mainTB a short subsection acknowledging the play-surface policy so the paper and the game cannot drift apart again.
- **Success.** `hp_variant_policy` values in the instance schema are governed by a written rule, tested in CI.

### A4. Mealy/Moore window reconciliation **[G — demo §2.3] — Priority: MEDIUM-HIGH**
- **Problem (historical — resolved, see status box).** The candidate window is 0..k (Puzzle 4's cause sits at t=k), but the demo's junction-graph rendering made the bulb depend only on inputs 0..k−1, so the human and agent candidate spaces differed at column k. Production resolved this with Mealy edge-rendering plus the per-instance P_CAND effect-irrelevance proof.
- **Action.** Either implement edge-output rendering (Mealy bulb on the final transition, making column-k cells testable) or formally restrict corpora to causes in 0..k−1 and prove the trivial-instance filter implies no information loss for shipped instances. Update grader `cellsIn` to match.
- **Success.** A theorem-or-config note: human-testable cells ≡ agent-candidate cells, per instance, verified by the parity audit (D2).

---

## Gate B — Grader and generator (blocks corpus production)

> **STATUS (2026-06-11, see `Verification/GateB/results/REPORT.md`):**
> - **B1 grader: PASS.** Production grader (oracle + minimality; Prevent implemented directly from Def. valid via closest-removal search) matches the validated reference on all five worked puzzles and the real TempoBench instance; Prop. pivotal is *checked against the raw definition*, not assumed; witnesses accepted, supersets rejected. **Profiled envelope published:** ≤1s/key at (|I|,k) up through (2,3) and (3,1); (2,4) and (3,2) land in 1–10s; Credit-original is the exponential mode exactly as the cost analysis predicts.
> - **B2 generator + corpus: PASS** (prototype: random Mealy, F2/F3 by construction — corpus realism *not* claimed). 139 generated / 107 retained (23% discard). Findings: **Credit-vs-Pin per-cell unions agree 107/107** (supports the equality mainTB leaves open); **original-vs-modified variant keys diverge on ~59%** of retained instances (the Conjecture-corp risk class is common); no-pivot verdicts split 11 overdetermined / 4 unconditional-discarded. **Standing rule discovered:** search caps censor keys and corrupt statistics (49 phantom divergences at cap 3 vs 0 at full depth) — lift caps or certify per instance.
> - **B3 identifiability: PASS** on controls (known-identifiable accepted; observed-run-only refused); measured admission rate with 3 probes on random 2-state devices: **0/10** — the black-box gate is severely restrictive, as anticipated.
> - *Remaining in Gate B:* re-run B2 statistics on real SYNTCOMP/ltlsynt artifacts when the TempoBench dataset arrives; extend B3 beyond the 2-state family; production-optimize the grader within the published envelope.

### B1. Production grader + profiling **[mainTB V3] — Priority: HIGH**
- Implement the oracle-based checker (validity oracle + minimality; all four objects incl. set-valued AC2 with AC2(b) robustness, exactly as the demo grader, but against the expanded HOA product rather than toy junction graphs). Measure runtime vs (|I|, k) per mode; **publish the tractable envelope** that the verifiable-reward claim is then restricted to. Include ≥1 fully worked HOA-derived instance end-to-end — a reviewer rightly notes all current worked examples are hand-built.
- **Success.** Envelope table; one real-artifact instance reproduced in the paper; demo levels re-certified by the production grader (regression: the iteration-10/12 acceptance tables must reproduce exactly).

### B2. Generator (P1–P6) + corpus statistics **[mainTB V4] — Priority: HIGH**
- Build the pipeline; add the demo-derived stages: Shannon/BDD layout emission, legibility stats (max fan-out), decoy inventory, trivial-instance filter, and the CI verification harness (implementation spec §8 — totality/determinism, render-equivalence, key certification, **full-submission-enumeration audit** on small instances).
- Report: instances per stratum; no-pivotal-cell frequency split overdetermined vs input-unconditional; **Credit-vs-Pin per-cell agreement rate** (a disagreement instance is publishable evidence for the Credit choice); discard rates.
- **Success.** A prototype corpus (≥100 instances) where every instance passes the harness; statistics table drafted into mainTB.

### B3. Black-box identifiability **[mainTB V5] — Priority: MEDIUM**
- Implement the admission check: all devices consistent with the observed run + β-reachable probe information agree on the native answer. Report restrictiveness. Black-box instances ship only after this gate.
- **Success.** Checker + measured admission rate; black-box scoring documented as identification+reasoning.

---

## Gate C — Parity (blocks the "same game" claim)

> **STATUS (2026-06-11, see `Verification/GateC/results/REPORT.md`):**
> - **C1: PASS** on 9 instances (5 worked puzzles, the real TempoBench artifact, 3 generated): observation equivalence (the board is a pure function of the agent observation and behaviorally identical on every input assignment); submission round-trip (every possible board submission ↔ agent JSON answer format with identical grader verdicts — exhaustive); probe parity; candidate-space safety (every human-unreachable cell proven effect-irrelevant in every context — no correct answer is human-inexpressible).
> - **C2: DECIDED** — white-box humans play the live board (β=∞; attempts are the scored resource), with a budgeted/static white-box arm retained for the pilot so the paper's construct is measured rather than amended away; black-box and agent budgets finite and declared.
> - **C3: PROTOCOL + MATERIALS** — 2×2 spatial/textual design for the modality confound; agent observation JSONs emitted from the same instances the human board renders (equivalence covered by C1). Board-image automation for the agents-with-board arm remains.
>
> **Gate D is unblocked** (pilot design ready); D's only external dependency remains the TempoBench dataset for alignment-claim arms.
>
> **STATUS (2026-06-12) — mode-explicit construction adopted.** The Visible-Verification construction (`TRACE_puzzle_construction_proposal.md`, now marked ADOPTED) is implemented and verified: canonical human game = `TRACE_stop/pin/credit.html` (no embedded keys; live verdicts proven equal to the oracle for every possible player action by `verify_modes.py`); deterministic mode assignment + versioned quality gate for arbitrary inputs (`mode_assign.py`, `build_from_inputs.py`, `verify_mode_assignment.py`); P-SUB parity now audited **per variant policy** (original / modified / legacy union). The D1 pilot should compare the mode-explicit surface against the sandbox archive on the P3/P4/P5 strata, and include the budgeted white-box arm (C2).

### C1. Four-consumer parity audit **[G + mainTB §agent] — Priority: HIGH**
- Tests, per instance: (i) human board observation ≡ agent JSON observation (information content, both tracks); (ii) human submission (thrown set) serializes to the agent answer format and grades identically; (iii) probe semantics: battery test ≡ `probe()` (cost, returned fields); (iv) attempt accounting identical; (v) candidate-cell spaces identical (A4).
- **Success.** Automated parity suite green over the prototype corpus; any intentional asymmetry (white-box human live simulation vs agent's textual HOA) documented as presentation, with information-equivalence argued explicitly.

### C2. White-box budget decision **[G — demo iteration 9 deviation] — Priority: MEDIUM**
- The demo removed the probe budget from the white-box *human* game (live board); the paper's design budgets probes in both tracks. Decide: amend mainTB (white-box human β=∞, budget meaningful only black-box/agent) or reinstate an optional budgeted white-box human mode for the calibration study. Either is defensible; parity requires agents in white-box-live conditions get equivalent free simulation (they do — they can simulate the shipped HOA), but the *measured* construct changes. Record the decision; reflect it in V6/V7 design.

### C3. Modality confound **[mainTB's own caveat] — Priority: MEDIUM**
- Plan the controlled condition: humans-with-JSON and agents-with-rendered-board arms in the pilot/baselines, so spatial-vs-textual encoding doesn't masquerade as a human–agent gap.

---

## Gate D — Empirical validation (blocks release claims)

### D1. Human pilot & calibration **[mainTB V6] — Priority: MEDIUM (after A–C)**
- ARC-AGI-2 recipe: panel, time limit, standard attempt budget; retain evaluation instances only if reliably solved by multiple participants; per-stratum solve rates vs knobs. Include the gate/overdetermination strata explicitly (the demo shows these carry the conceptual load) and test whether the one-sentence objective suffices (design law L9).
- **Success.** Calibrated evaluation set; "approachable for humans" measured, not assumed.

### D2. Agent baselines **[mainTB V7] — Priority: MEDIUM**
- Both tracks; tool-less vs code-equipped declared; generator's search as ceiling; native/TS/AP per configuration; probe usage; no-pivotal-cell recognition (Prevent config). Primary metric: native solve rate; report the per-stratum human–agent gap.

### D3. Release packaging **[mainTB V8] — Priority: LOW (last)**
- Corpus, checker, canonical keys, JSON protocol, versioned with A–D results reproducible.

---

## Gate E — Paper hardening (peer-review items not covered above)

| # | Issue | Fix | Priority |
|---|---|---|---|
| E1 | All worked evidence is hand-built (Puzzles 1–5); no artifact-derived example | discharged by B1's worked instance | High (dup of B1) |
| E2 | "Memorization-proof" and "hard for models" rest on TempoBench's TCE-hard numbers at a different granularity | keep the existing hedge; add D2 numbers before any hardness claim in the abstract | Medium |
| E3 | Non-monotonicity (Rem. nonmonotone) shows exact heuristics fail, not that approximations score low — paper says so, but the difficulty narrative sometimes leans harder | audit claims wording once D2 data exists | Low |
| E4 | Closeness order "must be declared per corpus" — ensure schema field exists and is consumed | add `closeness: "count-only"` to schema; CI-check | Low |
| E5 | Per-cell Credit≡Pin equality is open; the Credit-core argument is lineage-based | B2's agreement statistic; if a divergent instance is found, feature it in the paper | Medium |
| E6 | Black-box "underdetermination ≠ bad reasoning" needs the V5 gate before any black-box numbers are reported | sequencing rule: no black-box results before B3 | Medium |

---

## Execution order & dependencies

```
A1 ──► A2 ──► A3                (semantics; ~blocks all claims)
 │       │
 ▼       ▼
B1 ──► B2 ──► B3                (grader → generator → black-box gate)
 │       │
 ▼       ▼
A4 ──► C1 ──► C2, C3            (parity; A4 feeds C1)
              │
              ▼
        D1 ──► D2 ──► D3        (humans → agents → release)
        E-items folded into the nearest gate
```

**Definition of "ready for development" of the production game:** A1–A4 decided, B1 grader passing the demo regression suite, and C1 parity suite specified — everything else can proceed in parallel with the build. **Definition of "valid benchmark":** all gates through D2, with mainTB's claims re-conditioned on the measured results.

**Revised sequencing (2026-06-10):** A1 checker, A2 definitional, A3, A4 are decided; A2(ii)-at-scale is an asynchronous external dependency (dataset re-preparation upstream) that re-enters at two points only: (i) the corpus-default `hp_variant_policy` in the A3 record, and (ii) the wording of every TempoBench-equivalence claim (B1 report, B2 statistics, mainTB revisions). Gate B starts now; B-outputs that depend on (i)/(ii) ship with the conditional phrasing and are finalized within a day of the dataset arriving.
