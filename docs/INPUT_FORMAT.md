# Source dataset and compiled package contract

The source dataset is UTF-8 JSONL, one complete finite task per nonblank line. No game recipe, board, answer key or certificate is accepted as source input.

```json
{"id":"one-switch","split":"tutorial","machine":{"inputs":["A"],"states":1,"initial":0,"transitions":[[{"next":0,"output":0},{"next":0,"output":1}]]},"observed":[[1]],"target_step":0}
```

Required machine fields: unique nonempty input names, positive state count, in-range initial state, and exactly one transition for every state and Boolean input valuation. `transitions[q][v]` uses `v = sum(bit[r] * 2**r)`. Each transition contains only `next` and binary `output`. Output is emitted using the old state and current inputs before changing state.

The trace consists of binary rows of the declared width. `target_step` is a nonnegative zero-based index inside the supplied trace; its output must equal 1. If a longer recording is supplied, the entire recording is validated and the target prefix is compiled. Prefix locality justifies this restriction; the input-file and source-record hashes preserve its provenance. Optional `observed_outputs` and `observed_states` must exactly match full source replay.

Optional fields are `id`, `split` (tutorial/pilot/development/test), `family` and `provenance`. IDs are unique in a package. Unknown fields are rejected, including alternative target or constraint specifications. Arbitrary LTL targets, nonbinary outputs, nondeterministic/partial machines and environment-constrained intervention languages need an explicit extension, never silent conversion. TempoBench file-format conformance is not required for the current reasoning benchmark.

All Boolean assignments through the target are admissible. Selected cells retain their actual values, including zero. Cell `t*m+r` is the same input everywhere it appears. The answer is any inclusion-minimal G/P set, or the separate `no_explanation` verdict when no such set exists.

# Deterministic compilation and evidence

For identical validated records, compiler version and configuration, compilation emits identical semantic trees and task IDs. Byte-identical source files and fixed compiler/formal source reproduce the complete package manifest. Equivalent JSON whitespace does not change the task, but does change the raw source-file provenance hash in that manifest. This is not a claim of graph-isomorphism canonicalization under renamed states or channels.

The Lean executable constructs reduced decision trees per time/state. Leaves emit the original output and select the next state. Branches with identical subtrees can be removed under a proved equality; the full original cell inventory remains selectable. The independent Python adapter checks every tree against every source transition, not only the recorded path.

Every general board also requires `display: {"version":"trace.display.v1", "terminal":[...]}`. Each terminal tree uses original switch cell IDs and output-only leaves `{"kind":"outcome","value":0|1}`; it never carries a successor state. The native Lean constructor projects and reduces the final semantic trees. Python independently validates the exact projection and every final transition output. Missing or forged projections are rejected. Both human and AI public tasks receive this field, alongside the unchanged semantic layers and cell inventory. This is derived compiler output, not an additional source-dataset requirement.

A package uses `dataset.json` with an indexed task descriptor, `items.jsonl` with byte-addressed task records, `forms.json`, and `manifest.json`. Each index entry binds the item ID, relative path, byte offset/length, canonical item digest, split and family. The dataset hash binds the descriptor; every loaded item is hash-checked and validated. Forms are independently hash-bound. Compilation writes the package only after all requested certification succeeds.

Default operation checks canonical answer certificates in Python and Lean without embedding them in tasks. `--emit-certificates PATH` saves private detailed records outside the package. `--verbose` only changes console output. A compact manifest records exact checked scope and source identities; a hash alone is not a proof.

# Resources

There is no fixed state/channel/horizon/cell-count validity cap. Explicit transition tables already contain `states * 2**inputs` entries. Every instance and target window is finite. The compiler offers an optional timeout for waiting for the first Lean constructor response and for the certificate-checker subprocess. It is not an overall wall-clock limit: Python solving/certification, pipe writes and reading a complete response are outside that timer. Use an external job scheduler or process supervisor for an overall computation budget. Generation offers a sampling-attempt budget (0 means unlimited). An exhausted budget or interrupted computation is incomplete, never a no-explanation verdict.

The current implementation does not promise distributed execution of a single query or succinct symbolic-machine support. Independent instances can be compiled/evaluated in separate jobs and packages. Scrolling, zooming and viewport rendering avoid requiring a whole level on one screen; they do not prove that every finite machine is easy to understand.
