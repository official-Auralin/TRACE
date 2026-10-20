# TRACE construction and finite explanation proofs

This directory proves the general executable Mealy-to-switch-tree construction, its output-only terminal display projection, and the finite guarantee-and-prevention task used by TRACE. The same `compileRoundReduced` and `compileTerminal` definitions covered by the proofs construct the trees shipped by the compiler CLI. It uses the total Mealy machine definitions and replay locality results from the preserved `review_reverse_parity` project; its two prerequisite source files are vendored without edits. See `PROVENANCE.json` for exact source paths and SHA-256 hashes.

From the TRACE root, run:

```sh
bash formal/verify.sh
```

The script requires Lean **4.24.0** and its C toolchain, removes only `formal/.build`, compiles every local module afresh with warnings treated as errors, and audits every named theorem's axiom dependencies. Set `LEAN_BIN` to the pinned toolchain's `bin` directory when it is not at the configured local path. It also builds native `formal/.build/trace-compile` and `formal/.build/trace-check` executables. Missing tools and failed checks are errors; nothing is silently skipped. The compact `formal/proof_checks.json` binds source and executable hashes; detailed generated products stay under ignored `formal/.build/`. The permitted foundational dependencies are `propext`, `Classical.choice`, and `Quot.sound`; proof admissions, custom axioms, and compiler-trust proof tactics are rejected.

The complete project verification command, `python3 -m benchmark.verify`, also invokes formal verification and exercises the independent Lean certificate runner on release data. Proof compilation and running certificates are different evidence: a clean proof build alone does not assert that any particular JSON file was checked.

For deterministic construction after the clean build:

```sh
formal/.build/trace-compile < machines.jsonl > boards.jsonl
```

Each input line contains `machine`, `observed`, and `target_step`. The machine has the existing `inputs`, `states`, `initial`, and total Boolean transition-table fields. The supplied recording may extend beyond the target; the board covers its prefix through that target. Each output line is a raw `trace.board.v2` object with `initial`, `states`, `inputs` (a count), `horizon`, and `layers[time][state]`. Switch nodes have `cell`, `zero`, and `one`; output leaves have Boolean `value` encoded as 0/1 and `next` state. The compiler does not select a replacement recording or generate data. Outputs may turn off and on; each leaf advances exactly one machine round. Identical branches are reduced by a proved semantics-preserving function. The full time/channel cell inventory remains the intervention domain, including cells irrelevant in some branches.

The same object also includes `display: {version: "trace.display.v1", terminal: [...]}` with one projected tree per state at the target round. Its switch nodes retain the same `cell`, `zero`, and `one` fields. Its leaves are exactly `{kind: "outcome", value: 0|1}`: they describe failure or success of the shared target, not distinct lamps or successor states. The proved `compileTerminal` maps semantic leaves to their outputs and then reduces equal branches. An output-constant terminal route consequently has no switches even when its different machine transitions reach different post-target states. Earlier semantic trees stay unchanged because a different successor there may change the target. The complete semantic `layers` remain available for replay and preserve every state, including the state after the target transition. The display intentionally does not preserve that final state as a visual distinction.

For an independent certificate run:

```sh
formal/.build/trace-check records.jsonl
```

Each nonblank line is `{"item": PUBLIC_ITEM, "certificate": GAME_CERTIFICATE}`. `-` instead of a path reads standard input. Both executables process one record at a time. The checker rejects at the first invalid record with a nonzero exit code and prints a final JSON status/count only on success. Empty input is rejected. There are no fixed maximum state, channel, horizon, or cell counts. Dimensions must be finite and positive where required, the target must lie in the recording, and the explicit table must be total. Available memory, stack, elapsed time, and the explicit alphabet size still constrain execution. Operator budgets and termination by an operating system are not mathematical invalidity or a no-explanation verdict.

The checker validates the complete machine table, exact normative semantics object, actual execution, every recurrence row at every state, required query coverage, positive witnesses, negative claims, and strict answer shape. `QueryLookup.lean` proves canonical-key injectivity, insertion of checked roots, lookup binding, and candidate/deletion coverage. The runtime uses those exact lookup and coverage functions. It consequently does not recompute the exponentially recursive reference oracle after checking the tables. All input words through the target are covered by the recurrence, including changes from an observed zero. The effect is the output of the target transition before the state update.

See `PROOF_COVERAGE.md` for the theorem-to-implementation map and `TRUST_BOUNDARY.md` for the precise remaining assumptions. This directory does not assert a proof of the entire Python application, browser interface, study design, or arbitrary synthesis-strategy reversal.

The archived v3 board-first compiler was outside the Lean theorem inventory. The general semantic constructor and terminal display projection are proved. The latter preserves the target under every intervention, and therefore preserves guarantee, supported prevention and every inclusion-minimal explanation when the cell domain is unchanged. JSON adapters, serialization, executable compilation/runtime, browser drawing and interaction, and orchestration are separately tested boundaries; the proof does not establish that a browser draws one unmistakable target or that a participant understands it. A clean build proves the generic claims, not that any particular release or study has passed its operational checks.

The native constructor command is a low-level component. Its JSON decoder does not reject all extra fields. Dataset imports must pass through `python3 -m benchmark.compile`, whose strict source contract rejects unsupported targets, constraints and derived fields before invoking the native constructor. Native success alone is not a certified public package.
