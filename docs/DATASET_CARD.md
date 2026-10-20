# TRACE general-Mealy corpus v5

The current package is `trace-mealy-v5`, using unchanged `trace.gp.v2` explanation semantics and `trace-study-v5` sessions. It is a pre-trial research instrument, not a validated human difficulty scale.

Publication status: the v5 package is now public source material and can be exported to the `trace.demo.v1` lab demo. Tutorial/pilot/development/test labels retain their original construction assignments; they no longer imply concealed evaluation data. Demo users may access the full exported pool. Future controlled studies must record prior exposure and use separately reserved material when claiming evaluation on unseen tasks. The 64-item panel and 1,024-item full pool remain distinct statistical scopes, not independent secret sets.

## Composition and provenance

The standalone `benchmark.construct --release` producer uses seed 20261019 and emits 1,328 machine/trace/target records: 16 tutorial, 32 pilot, 256 development, and 1,024 test. The first 64 interleaved test items form the matched human–AI panel; full-test agent accuracy and matched-panel comparison have distinct estimands. Every item then passes through the same general Lean compiler used for external imports. No source board recipe is required.

The test set crosses state counts {2,4}, Boolean input counts {2,3}, and horizons {3,5}: eight strata, 128 test items each. Interleaving yields eight panel items per stratum. Tutorials use two states, one input and horizons 2–3; pilots use two states/two inputs/horizon 3. Development uses the same structural ranges as test with separate random streams and distinct exact machines. These ranges are corpus choices, not software limits.

Machines are sampled as total explicit transition tables; positive observed traces are sampled without changing the machine. Exact labeled machine duplicates are rejected by the producer. For this release, fixing all final-round inputs does not guarantee the target. Upward closure therefore implies that every accepted explanation includes an earlier-round cell. This selection uses one exact backward query rather than all-answer enumeration.

There is no claim that different machines are nonisomorphic or induce distinct causal behavior. Structural strata can overlap behaviorally, and size does not guarantee increased difficulty. Family labels describe sampling dimensions, not independent mechanism families. Generalization to unseen mechanisms requires additional grouping/held-out studies; the fixed-panel comparison does not establish it.

## Answer contract and artifact

All Boolean input words through the target are permitted, including changes from recorded zero values. A correct answer is any inclusion-minimal set satisfying G AND supported P. Minimum cardinality, a complete answer family, and the union of explanations are different tasks. A separate `no_explanation` verdict is supported by the tool even though release selection excludes invariant-positive targets.

V5 recompiles the exact v4 source records: machines, observed words, targets, IDs, assignments and mathematical answers are unchanged. Only the certified presentation and package/protocol identities change. The pre-correction display and evidence are preserved in `archive/v4-multiple-targets`.

The compiler preserves each source output at each round under every input assignment. Same-cell visual copies are linked. Equal decision subtrees are removed by a proved simplifier; all original input cells remain selectable. A visible control can be irrelevant in a particular state or even globally. This is not the v3 condition that every displayed control is relevant. Earlier output status indicators can change; only the specified target moment determines the event. The mandatory `trace.display.v1` projection discards successor states after that moment and merges identical output-only terminal subtrees. Its ON routes reach one shared target lamp; OFF routes reach one dark exit. A skipped switch remains selectable and may matter in another route.

`data/source.jsonl` retains original dataset records. `dataset.json` indexes `items.jsonl`; `forms.json` and `manifest.json` bind assignments, source/compiler identity and certification scope. Task records contain no keys, recipes or stored detailed certificates. The package loads one verified item at a time.

## Certification and empirical limits

Every compiled state/input decision is checked against its source transition, including unobserved alternatives. One canonical answer or absence certificate per item is checked in Python and Lean. Any submitted answer is independently graded; the generated canonical answer is not a scoring key and is not included in the public task.

The general transformation theorem and formal recurrence/minimality results cover arbitrary compatible finite dimensions. Exhaustive tests cover declared small windows only; larger cases receive local transition verification and targeted execution probes. Detailed evidence is an optional private artifact, with compact current summaries in results/.

The original v3 data, source and evidence are preserved in `archive/v3-switchlight`. Its test counts, baseline numbers and playtest records do not validate this v5 instrument. No recruited humans, live evaluated models, institutional determination, registration or empirical difficulty calibration is claimed. The pilot must test comprehension, navigation and nonlatching/linked-switch interpretation before main trials.
