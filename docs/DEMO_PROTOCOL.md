# TRACE public lab demo — trace.demo.v1

This is the learning-enabled GitHub Pages demonstration, not the preserved `trace-study-v5` collection protocol. Its mathematical task remains `trace.gp.v2`; the source package remains `trace-mealy-v5`. The demo uses the same certified machine/trace/target and one-target visual projection. It does not construct datasets while someone plays.

## What is scored

A correct ordinary answer is any inclusion-minimal cell set satisfying guarantee AND supported prevention. Minimum cardinality is not required. Alternative correct sets receive identical correctness credit. The separate `no_explanation` verdict is correct when no permitted input assignment defeats the target; an empty cell set is not this verdict.

The local grader computes the exact backward recurrence over the explicit transition table. It neither samples completions nor compares an answer to a stored canonical solution. Normal feedback distinguishes failed guarantee, failed prevention, and redundant marks. Where available, a displayed counterexample or preventing execution obeys the corresponding fixing constraints. A single example does not prove a universal guarantee. Example answers are disclosed only through an explicit reveal action after an incorrect submission on the current attempt; the browser and agent transport enforce the same eligibility. The shared interactive teaching boards also start without pre-disclosed solutions.

## Learning and progress

The initial teaching material illustrates direct dependence, conjunction, alternatives, linked inputs and unnecessary marks. Practice continues with the same submission and feedback controls used later. Reviewing an example is assistance, not evidence that the player understood it. Comprehension requires observation and diagnostic pilot tasks, not a correct-guess screen or silent performance-based exclusion.

Every item has a stable identity within a hash-bound public package. Progress distinguishes:

- The first submitted answer, its correctness, and assistance already disclosed before that answer.
- Later submissions and eventual correct completion.
- Explicit retries, revisits and solution reveals.
- Draft selections and the current item, so refresh can resume rather than reset progress.

A retry or replay cannot replace the first submitted answer. An item encountered again is not a new unseen task. A first submission after earlier lessons/feedback is performance following that exposure, not untrained performance. Failed answers and later successful retries remain distinguishable. Time in this untimed demo is descriptive elapsed interaction time, not a claim about active reasoning or a matched timed research budget.

Players can continue through the exported pool, select structural bands and revisit earlier tasks. The scheduler selects unseen items when available and identifies finite-pool exhaustion; it does not silently recycle IDs as novel tasks. New certified packs can extend the pool. These operational choices impose no mathematical state/channel/horizon cap. Each imported task is finite and actual memory, explicit alphabet size and computation still constrain a particular device.

## Difficulty and transfer

Bands describe state count, input count and horizon. They are provisional navigation choices, not calibrated psychometric difficulty. Larger machines can have simpler causal structure; more drawing or scrolling can increase display burden independently of causal reasoning.

The next empirical phase should vary temporal dependence, conditional relevance, interacting inputs, redundant alternatives, output persistence and explanation structure. Compare controlled task pairs, then measure accuracy, assistance and burden. Audit simple last-round, all-switch and pivotal-switch strategies. Valid general reasoning strategies are desirable; the goal is to remove incidental dataset shortcuts, not defeat a successful general algorithm.

Exact labeled uniqueness is not semantic or mechanism uniqueness. Any claim about transfer to unseen causal mechanisms requires a documented grouping and held-out construction policy. The published corpus is public exposure; its historical test labels do not make it a concealed evaluation pool. Difficulty calibration and mechanism-held-out evidence are not supplied by the software release.

## Human and agent access

The browser and local agent transport use the same session engine, task data, exact grader, teaching examples, and feedback/reveal operations. The agent's observation retains its preceding public actions and feedback. Replaying the supplied recording is not a counterfactual experiment. Any counterexample shown after submission is feedback and becomes part of later exposure.

`demo/agent.mjs` is a local JSONL transport over the exported demo package. It does not call a model provider or sandbox a participant. Publicly available source includes an exact solver; a repository-aware agent is an operator, not a valid benchmark participant. Future model evaluation must specify what code/tools are available, retained context, context-window handling, token/compute/time limits and actual provider configuration. Shared facts do not establish equal perceptual effort or resource cost.

Start the local transport after exporting the site:

```sh
node demo/agent.mjs artifacts/pages-demo/catalog.json
```

Send one JSON object per line. `{"action":"next"}` opens an unseen puzzle;
`{"action":"submit","answer":{"cells":[0]}}` submits zero-based cell indices;
`{"action":"retry"}` unlocks another attempt after feedback. The alternative
answer is `{"verdict":"no_explanation"}`. `{"action":"reveal"}` discloses an
example after an incorrect submission. `snapshot` exports the local record;
`restore` accepts that snapshot in a `snapshot` field. Every successful response includes
the current public observation and accumulated feedback history. The transport's
`--help` lists lesson, selection and draft operations.

The existing `benchmark.evaluate` keeps the isolated-item `trace-study-v5` behavior. Do not silently combine its scores with humans playing the continuous demo. Fixed-sequence learning comparisons and adaptive free play require separately declared assignment and analysis.

## Storage and public deployment

Progress remains in the current browser's local storage, or the local agent process state. It can be edited, lost if site data is cleared, or unavailable when browser storage is blocked. It is not an authenticated or centrally collected record. Storage failure must be visible rather than represented as successfully saved progress. Package/version mismatches must not silently relabel earlier outcomes. There are no participant identifiers, analytics or score uploads in the demo.

GitHub serves the website and applies its own hosting/privacy practices. Local-only TRACE progress is not a claim that the hosting provider receives no ordinary web requests.

Only `benchmark.demo`'s explicit static export may be deployed. The repository root, operator configuration, archived databases, raw logs, private certificates and historical outcomes are not a website artifact. Task and teaching records use public allowlists; neither includes stored solutions or completion tables. The JavaScript grader is a tested trusted-code boundary, not a newly proved extraction.

## Milestone two: authoritative collection

The next milestone keeps this presentation while adding a hosted Python session service, durable storage, resume identities, exact server grading and an exposure-aware event schema. The first submission must be committed before its feedback is disclosed. Idempotent requests, retries, pauses, dropout, reveals, version changes and storage failures require explicit handling. Client-reported local correctness is never accepted as authoritative grading.

Before research collection, supply the actual institutional/participant-information record. Define free play versus fixed challenge sequences, eligibility without performance-based screening, retention/withdrawal, prior-exposure handling, and public-volunteer limitations. Separate first-submission accuracy, assistance, eventual completion and learning curves. Use common anchors or fixed matched sequences where comparative claims require them; do not reuse the v5 fixed-design confidence procedure for adaptive longitudinal records without a justified analysis.

The original 64-item matched-panel and 1,024-item full-agent estimands remain separate. Reserve new data when concealed exposure is required. No browser release establishes human ease, enjoyment, reliable difficulty, live-model ability, approval or preregistration.
