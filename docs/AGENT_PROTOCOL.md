# TRACE agent evaluation protocol

Evaluate the same finite explanation task and public information given to humans. The current package version is `trace-mealy-v5`, the session protocol is `trace-study-v5`, and the G/P semantics remain `trace.gp.v2`. No live model evaluation is asserted by the existence of this adapter.

## Frozen record

Before main evaluation identify system ID, provider, exact expected/returned model identity, generation parameters, output-token cap, inference date, prompt and adapter identities, dataset/protocol/source versions, regime, repetitions and registration. Marketing aliases without a reproducible snapshot must be disclosed as a limitation. Configuration changes require separate analyzed groups.

Develop prompts and transport on development items only. Freeze them before test results. Each scored item has a fresh context; prior test answers, private certificates and repository files must never enter it. Practice examples are shared intentionally with humans. Every observation includes the same five public demonstration boards, their displayed completion runs and cases, and any completed practice references. The browser exposes that material through its examples dialog. Practice references contain a solved example and personal feedback, including a submitted alternative when correct; they are not an exhaustive answer inventory.

Use `benchmark.evaluate --dataset PACKAGE_DIR` for an imported compiled package; omitting the option selects `data/`. The optional standalone dataset constructor is outside the evaluation path. The benchmark compiler preserves the supplied machine and the observed prefix through the target. The runtime reads hash-bound task records lazily, validates their machine/level correspondence, and grades answers directly. It does not require persisted keys or detailed certificates. Keep the same package identity and assignments for both populations.

## Exact rule content

A selected cell refers to its recorded Boolean value, including zero. Select one set C satisfying:
1. Holding all selected cells recorded guarantees the target under every change outside C.
2. Some assignment changing only within C prevents the target.
3. Removing any selected cell breaks at least one of the first two conditions.

Accept any inclusion-minimal explanation, regardless of whether another answer has fewer cells. Do not return the union of all answers. Prevention need not flip every selected cell.

Return `{"answer":{"cells":[...]}}`. If no input assignment can prevent the target, return `{"answer":{"verdict":"no_explanation"}}`. The default release excludes invariant-positive targets, but imported tasks can require this verdict. A blank cell set is not that verdict.

The machine starts at the same initial state on every hypothetical execution. Input cell ID is step * input_count + channel_index; channel indices follow machine.inputs. Transition row index is the sum of input_bit * 2^channel_index. Output is emitted before updating state. Earlier output indicators may change: the event is output 1 at the specified target moment. Recorded states and outputs are public to both modalities.

The common task includes the complete finite switch/light decision structure and the equivalent Mealy encoding. Multiple visual copies read one original cell. Simplified trees can skip a cell, but every original input remains selectable in the control inventory. All counterfactual transitions remain represented in the semantic forest. The shared `board.display.terminal` projection retains only final outputs and reduces identical terminal subtrees: every successful route reaches one target lamp, and every failed route the dark exit. It drops only post-target state distinctions. Copies with identical full time/channel labels move together; A at different moments denotes different cells. Practice removal examples are illustrative executions, not general irrelevance claims. The human view supports pan, zoom, overview, and direct navigation to a moment and route; the technical drawer exposes the machine. The included AI adapter sends structured task data. This establishes information parity, not equal perceptual effort, token cost, or an image-only comparison. Register modality and report this limitation.

The canonical runtime instructions and tutorial payloads provide the actual prompt content. Archive that content, not merely this prose template.

## Tools, time and response handling

Primary reasoning permits no external tools or simulator queries. The optional probe condition defaults to eight calls to the same simulator available to humans. No code execution, web, calculator, answer checker or filesystem is exposed to the evaluated model.

The clock starts before model delivery: the default 480 seconds per item includes queuing, generation and permitted tools. `--seconds` and `--probes` configure the finite session budgets; they must be prespecified, logged, and matched across a comparison. Exactly one scored response is accepted. A larger machine or horizon is not rejected for exceeding the default corpus dimensions. A model context window, provider token limit, or operator resource limit can still prevent an evaluable run. Record these constraints and dispositions rather than interpreting resource failure as a no-explanation answer.

The harness must not repair wrong coordinates, drop cells or retry incorrect answers. The optional `--max-adapter-message-bytes` is an operator transport budget; unset, there is no preset message-size cap. Record any configured transport limits alongside the study budgets.

A model response ending because of an output-length limit is invalid even if a syntactically complete answer appears in the partial text. Refusals and malformed actions are failures. Verified transport outages are recorded separately, without selectively rescuing ordinary wrong answers. Idempotent retransmission preserves the same request and original deadline.

## Included provider transport

adapters/chat_completions.py uses a Chat Completions-compatible HTTP endpoint. The researcher configures TRACE_MODEL, TRACE_API_KEY, TRACE_GENERATION_JSON with a positive token cap, and optionally TRACE_API_BASE. Credentials remain in the environment and outside logs.

The allowed actions are a final answer or, in the probe arm, {"probe":{"changes":{"0":1}}}. Only the allowlisted public observation and shared teaching material are sent. Returned model identity, finish reason, visible response, usage and safe provider request identity must be recorded and checked against the declared configuration.

Local mock-provider tests establish parser and protocol behavior. They do not establish compatibility with every provider or measure model performance. A configured development smoke run precedes a frozen main batch.

The shared service also accepts descriptive navigation telemetry. The structured adapter does not invent browser navigation events. Human navigation records are debounced and best effort, contain no correctness information, and consume no probes or additional attempts. Missing navigation events do not demonstrate absence of effort. Do not compare raw human navigation counts with absent structured-agent events as if they measured reasoning efficiency.

## Runs and analysis

Each evaluator invocation has a unique run identity; repetition IDs must not collide across invocations. A run/repetition cohort remains intact across its forms during analysis. Fresh item contexts do not create new item populations.

Default five repetitions per test item are a resource choice, not proof of independent model realizations or adequate precision. Record all requested trials, failures, aborted batches and uncovered items. Analyze distinct configurations separately.

For the default release, use the same 64-item shared panel for human comparisons; full-pool agent scores use 1,024 test items. Imported packages can define different finite item sets and forms. Declare their scope and sample design explicitly; extending agent-only difficulty does not provide a human baseline for those added items. Report exact explanation accuracy and obligation diagnostics; do not use F1 against an arbitrary accepted answer. Follow REPORTING_PROTOCOL.md for conservative conditional uncertainty and exploratory bootstrap limits. Schema-v2 registration binds the chosen interaction budgets as well as package and configuration identities.
