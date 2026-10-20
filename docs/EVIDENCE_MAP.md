# Claims and the evidence that supports them

| Claim | Implementation / evidence | Boundary |
|---|---|---|
| Exact finite G/P meaning, any inclusion-minimal answer | `core.py`, `game.py`; Lean Semantics/Deletion/Binding/Certificates | JSON interpretation and Python execution are tested, not kernel-proved |
| General machine-to-switch transformation preserves outputs and explanations | Same executable `compileRoundReduced` used by Lean CompilerRuntime; Compiler theorems | JSON/array assembly, native runtime, display and interaction remain trusted/tested |
| Output-only terminal display preserves the scored target | Executable Lean `compileTerminal`, terminal/mixed-execution theorems; strict Python projection checks | Only post-target state is omitted; earlier routing and semantic replay remain exact |
| One visual goal matches the output predicate | Common target/dark endpoints; four-case screenshot regression and actual browser inspection | Renderer tests do not establish human comprehension; pilot remains required |
| Concrete imported board matches source | `level.validate_board` checks every state/input transition at every round | Polynomial in explicit machine/level size; not word enumeration |
| Concrete canonical answer is justified | Python recurrence checker and Lean checked-table/query binding | Optional certificate persistence does not change checking |
| Arbitrary valid submitted answer is accepted | Common `grade`; independent quantified small fixtures, adversarial tests | A canonical answer is never the scoring key |
| Human/AI task and action parity | Shared public projection/session service, adapter and HTTP tests | Information parity is not identical perceptual cost |
| Repeatable compilation and provenance | Deterministic source/semantic hashes, source-bound manifests, immutable session identities | No graph-isomorphism canonicalization claim |
| Large finite inputs are supported | No semantic dimension caps; two-row decision computation, indexed JSONL, streaming checker, viewport | Explicit alphabets and complete answer inventories can be exponential; practical resources remain finite |
| Human ease, enjoyment, difficulty or AI advantage | Actual pilot and registered matched-panel study | Not established by software tests, Lean or synthetic sessions |

Fast checks cover implementation contracts and targeted examples. Formal verification proves statements over all compatible finite instances. Deep audits enumerate deliberately small instances and search for mismatches. These are complementary obligations, not interchangeable proof counts.

Detailed generated artifacts belong under ignored `artifacts/` or immutable external release storage. Current concise reports live in `results/`; historical reports stay with their archived source. A report is usable only when its recorded source/data identities match the claim.
