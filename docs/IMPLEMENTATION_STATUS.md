# TRACE v5 implementation and acceptance ledger

The public lab demo is separately versioned `trace.demo.v1`. It adds browser-local grading/progress and a continuous feedback loop over the same certified tasks. See `DEMO_PROTOCOL.md` for its scoring/exposure contract and `DEPLOYMENT.md` for Pages. The v5 server study described below remains available unchanged. Public demo records are not authenticated study outcomes; hosted collection, revised learning analysis, empirical difficulty and the recruited comprehension pilot are milestone two. Current demo checks must be read from source-bound demo/release reports, not inferred from the historical v5 browser report.

The production pipeline is now **imported Mealy machine + observed trace + target → deterministic certified task → shared human/agent service**. The optional source-dataset constructor is independent of compilation and play. The exact answer remains any inclusion-minimal set satisfying guarantee AND supported prevention (`trace.gp.v2`).

V5 corrects v4's misleading per-transition terminal bulbs. Semantic machines and answer sets remain unchanged; the proved output-only final projection now feeds one target lamp or the dark exit. Earlier outputs use status indicators. The original screenshot's A · 2 is unnecessary given A · 1 = 0, but remains relevant on another route. The interface must express that conditional distinction.

## Delivered components

| Component | Implementation | Acceptance evidence |
|---|---|---|
| Input contract | Total deterministic Boolean-input/Boolean-output machines; positive observed target; finite prefix; strict unsupported-field rejection | `docs/INPUT_FORMAT.md`, importer and mutation tests |
| General transformation | Executable Lean decision-tree constructor and equality reduction, preserving every round and every minimal explanation | `formal/Trace2/Compiler.lean`, clean formal report |
| Import and package | Deterministic JSONL import, per-transition binding, Python/Lean canonical certificates, byte-indexed four-file package | `benchmark/compile.py`, compiler/audit tests, reproducibility report |
| Standalone dataset production | Seeded machines, traces and targets; optional earlier-round-dependence filter | `benchmark/construct.py`, current dataset card |
| Common task and grading | No stored key needed; arbitrary valid minimal answers accepted; typed no-explanation verdict | `core.py`, `game.py`, `runtime.py`, independent quantified oracles |
| Human interface | One target lamp/dark exit, earlier output indicators, linked full cell labels, time layers, recorded replay, viewport navigation and shared examples | `web/`, actual browser report |
| AI transport | Same public task and conditions, timed isolated adapters, source-bound durable sessions | adapter, HTTP and session tests |
| Resource behavior | No fixed dimension caps; two-row decision recurrence, streaming proof records and lazy package access; optional operator budgets | larger finite fixtures and explicit resource boundary |
| Research support | Separate 1,024-item pool and 64-item panel; allocation, audit logs, regrading and registration gate retained | protocol/analysis tests; no actual trial findings |

## Evidence and its limits

`results/release_checks.json` is the current integrated build/test/corpus report. `results/browser_checks.json` records actual browser checks; interpreter agreement alone is not evidence of correct drawing or interaction. `results/reproducibility.json` binds constructor output and repeated compiler bytes. `results/baseline_summary.json` contains non-learning instrument measurements only. `results/pdf_checks.json` binds the final manuscript rendering. A report is evidence only when its status and source/data hashes match the claim; never reuse a historical PASS.

The kernel proof covers the general finite constructor and G/P reasoning. JSON parsing/array assembly, native execution, Python orchestration/grading, browser interpretation and rendering remain separately tested boundaries. No proof claim covers the entire application or establishes perceptual equivalence.

The generated release uses structural sampling strata, not a validated difficulty scale. Exact labeled machine duplicates are excluded in this release; general imports may legitimately reuse a machine with different traces. Semantic/isomorphism deduplication and held-out mechanism generalization are not established. More states or longer traces do not necessarily make a task harder.

No fixed semantic dimension limit means arbitrarily large *finite* inputs are admitted. Explicit input alphabets, output size, stack, memory and elapsed computation still matter. The current implementation is local and streaming; it does not claim a distributed solver, universal compression or physically unbounded execution.

No recruited-human findings, live-model findings, institutional determination or actual preregistration have been produced. Complete the comprehension/accessibility/enjoyment pilot before freezing the actual study. Registered collection and empirical difficulty calibration remain gates in `RESEARCH_ROADMAP.md`, not software deliverables that can be checked off by synthetic tests.

## Preservation

`archive/v4-multiple-targets/SNAPSHOT.json` binds the pre-correction source, data, evidence, screenshot and two consistent SQLite backups. Original raw logs remain in place. `archive/v3-switchlight/SNAPSHOT.json` binds 619 preserved entries, including a consistent SQLite backup; original raw logs remain in place. `archive/v2-textbook` and the separately preserved original repository remain untouched. Superseded reports, generators and answer inventories are retained with their original sources. Detailed current generated certificates/screenshots/raw computational baselines belong under ignored `artifacts/`; raw study logs are private records, not disposable build output.
