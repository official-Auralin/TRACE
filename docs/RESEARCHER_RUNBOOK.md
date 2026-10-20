# TRACE researcher runbook

This runbook covers `trace-mealy-v5` packages and `trace-study-v5` sessions. The default dataset has 16 tutorial, 32 pilot, 256 development and 1,024 test items. Its matched human–AI panel has 64 items in 16 four-item forms; full-test agent accuracy is a separate estimand. Imported packages can have different sizes and assignments. Always use the actual package manifest and forms.

Work in the active Fall26/TRACE repository. The preserved original repository, Summer26 research and `../review_reverse_parity` are read-only sources. Technical checks establish software/formal properties, not approval, human usability, or model performance.

## 1. Complete the readiness record

Before recruitment, complete [STUDY_PROTOCOL.md](STUDY_PROTOCOL.md), [PARTICIPANT_MATERIALS.md](PARTICIPANT_MATERIALS.md), and the actual institutional determination. Before main testing, complete [PILOT_CHECKLIST.md](PILOT_CHECKLIST.md), freeze the study, and record preregistration. Live agent inference requires the researcher's configured account and an explicit run budget.

Record package/forms hashes, source identity, protocol, participant modality, interaction budgets and operator resource limits. The current task mode is `explanation`; the primary condition is `reasoning`. Technical readiness comes from current source-bound verification reports, not this document's existence.

## 2. Select or construct a package

The server imports a compiled package. It does not invoke the dataset constructor. Omit `--dataset` to use `data/`, or pass the same `--dataset PACKAGE_DIR` to the server, session tools, evaluator and analysis.

To compile the supplied independent external example into a new private package:

```sh
cd '/Users/bobby/Documents/Academics/CU-Classes/PL Lab/Fall26/TRACE'
bash formal/verify.sh
python3 -m benchmark.compile examples/external-loop.jsonl --output runs/imported-package
python3 -m benchmark.session forms --dataset runs/imported-package --split tutorial
```

The example contains loops, multiple inputs and outputs that turn off between illuminated rounds. It produces a one-item tutorial form. Successful compilation does not establish intuitive comprehension.

For new synthetic data, construction is a separate optional step:

```sh
python3 -m benchmark.construct --count 20 --states 4 --inputs 3 --horizon 5 --temporal --output runs/generated-source.jsonl
python3 -m benchmark.compile runs/generated-source.jsonl --output runs/generated-package
```

Existing compatible machine/trace/target records can be supplied directly as JSONL. The compiler validates the complete supplied recording and constructs the prefix through the chosen target; it does not resample a replacement trace. The supported event is output 1 at that finite target, with all Boolean input interventions permitted. Unsupported constraints or semantics must not be silently discarded.

The compiled package uses `dataset.json`, indexed `items.jsonl`, `forms.json`, and `manifest.json`. Records load and validate one at a time. They contain no stored keys, source board recipes or detailed answer certificates. Verification remains mandatory; `--verbose` changes console detail, and `--emit-certificates PATH` separately saves private evidence. Keep immutable official-release evidence under its manifest identity, outside participant artifacts. No preset state/channel/horizon cap is imposed; explicit transition tables, provider contexts and finite host resources still constrain feasible runs. Configure sampling/compilation budgets explicitly and preserve incomplete outcomes.

## 3. Start the restricted service and assign sessions

For the default pilot package:

```sh
python3 -m benchmark.server --host 127.0.0.1 --port 8765 --db runs/pilot-v5.sqlite3 --dataset data
```

In another terminal, list forms and create the assigned session:

```sh
python3 -m benchmark.session forms --dataset data --split pilot
python3 -m benchmark.session create --db runs/pilot-v5.sqlite3 --dataset data --cohort human --participant H001 --split pilot --form pilot-01 --condition reasoning --seconds 480 --base-url http://127.0.0.1:8765
```

Use the returned private URL on the study machine. Session creation is an operator action. IDs must not contain names, email addresses or student numbers; keep consent/contact/payment mappings separate. Session tokens are restricted operational data and do not belong in public reports.

Use a separate database and `--cohort baseline` for operator dry runs. For personal play with feedback on every puzzle, use `--split tutorial --form tutorial-01`. The default release supplies four tutorial puzzles; another package may supply a different count. Main test sessions require the completed study gates and a designated human-panel form. Preserve previous-release databases: the runtime rejects mixed package/source identities rather than upgrading old sessions silently.

Defaults are 480 seconds and one submission, with zero simulator probes for reasoning or eight for the optional probe condition. Set `--seconds N` and, with `--condition probe`, `--probes N` when a different matched budget was prespecified. The evaluator exposes the same settings. Refresh does not reset time or attempts. Operator transport limits are optional: the server has `--max-request-bytes`, and the evaluator has `--max-adapter-message-bytes`; neither has a preset size cap. Record configured values and resulting resource failures separately from mathematical answers.

The local service binds `127.0.0.1`. Remote recruitment requires the institution's completed deployment/access process and tested HTTPS setup. Serve only through `benchmark.server`; a repository-wide static server would expose private source, evidence, archives and records.

## 4. Conduct and document the session

Use the completed participant script and shared untimed examples. The default sequence has two practice items and four scored items. Imported packages can specify other forms or omit practice; review that sequence before recruitment.

The general game shows one output per moment. Earlier lights can turn off; only the highlighted target is judged. Repeated labels share a cell, and the inventory includes original inputs even when a reduced circuit skips a test. Pan, zoom, overview and direct moment/route navigation expose larger boards. The agent receives the same semantic information in structured form; equal visual effort or token cost is not established.

Practice feedback gives a solved example and diagnostics, including a concrete defeating run when available. It does not enumerate every accepted answer. Scored receipts withhold correctness. During scored items provide operational help only, without hints or extra time.

Navigation records are descriptive and best effort. The client debounces events and sends pending telemetry without delaying an answer; the final event can be lost or rejected after submission. Navigation does not consume probes or reset deadlines. Preserve these records, but do not treat their counts or timestamps as exhaustive actions or time spent reasoning.

After a session, check assignments, outcomes, attempts and dispositions. Never edit an answer or score to match recollection. Record metadata corrections and deviations separately. Withdrawal/deletion follows the completed consent policy without retaining deleted responses elsewhere. A documented infrastructure failure can be recorded with `benchmark.session technical-error`; ordinary mistakes, refusals and output truncation are not infrastructure outages.

## 5. Export and run computational baselines

```sh
python3 -m benchmark.session export --db runs/pilot-v5.sqlite3 --dataset data --output runs/pilot-v5.jsonl
python3 -m benchmark.evaluate --suite baselines --dataset data --split test --repetitions 5 --output runs/baselines-v5.jsonl
```

The suite runs random, all, none, latest, pivots and solver diagnostics. Only random uses the requested repetitions; deterministic strategies run once. The solver is an algorithmic oracle, not an unaided language-model result. Baselines grade directly and stream raw records. Exact chance rates and all-answer counts are omitted unless a separate bounded audit computes them.

Use new output paths and preserve partial logs after failures. Before release, inspect exports for privacy and scope under the actual consent policy. Keep permitted immutable raw evidence and use appropriately deidentified analysis inputs.

## 6. Configure and run a real agent

Follow [AGENT_PROTOCOL.md](AGENT_PROTOCOL.md). A nonsecret metadata file requires `provider`, `model_snapshot`, `generation`, and `registration_id`. Match `TRACE_MODEL` and `TRACE_GENERATION_JSON` to that record; generation must include a positive `max_completion_tokens`. Keep the credential in `TRACE_API_KEY`, outside tracked files, logs and command history. `TRACE_API_BASE` optionally selects a compatible provider endpoint.

After configuration, first run a development transport check:

```text
python3 -m benchmark.evaluate --adapter "python3 adapters/chat_completions.py" --system-id PINNED_SYSTEM_ID --metadata runs/system.json --dataset data --split development --max-forms 1 --repetitions 1 --seconds 480 --output runs/development-smoke.jsonl
```

Use the frozen complete main run only after its gates:

```text
python3 -m benchmark.evaluate --adapter "python3 adapters/chat_completions.py" --system-id PINNED_SYSTEM_ID --metadata runs/system.json --dataset data --split test --panel --repetitions 5 --seconds 480 --output runs/agent-panel.jsonl
```

Remove `--panel` for the full default 1,024-item pool. Five repetitions mean 5,120 scored items plus 2,560 practice items under the default two-practice/four-scored form policy; imported packages can differ. Probes can produce additional provider requests. Plan actual call/token costs before launch. Each item has a fresh context with shared teaching. Run every registered item/repetition, record failures, and do not retry scored mistakes for a better answer. Mock tests do not establish live provider compatibility or performance.

## 7. Allocate and analyze the registered design

```sh
python3 -m benchmark.plan_sample --dataset data --output runs/sample-planning-v5.json
python3 -m benchmark.allocate --dataset data --coverage 8 --condition reasoning --seed 1729 --output runs/main-allocation-v5.json
```

These are hypothetical planning and allocation outputs, not enrolled participants or achieved power. For the default panel, coverage 8 schedules 128 participants per condition with balanced rotations. Other form lengths are supported; exact position balance requires coverage divisible by form length. Apply each saved form, condition and rotation with `benchmark.session create`. Record non-enrollment and reserve replacements without consulting outcomes.

For exploratory summaries:

```sh
python3 -m benchmark.analyze --dataset data --input runs/human.jsonl runs/agent-panel.jsonl --scope panel --output-dir artifacts/matched-analysis
python3 -m benchmark.analyze --dataset data --input runs/agent-full.jsonl --scope full --output-dir artifacts/full-agent-analysis
```

For confirmation, complete and externally register the actual design before collection. The [schema-v2 template](analysis_registration.template.json) binds package/forms, source, analysis code, agent configuration, fixed sample and interaction limits. Its draft fields and false attestations intentionally fail validation.

```sh
python3 -m benchmark.analyze --dataset data --input runs/human.jsonl runs/agent-panel.jsonl --scope panel --output-dir artifacts/registered-analysis --confirmatory --registration runs/registered_analysis.json
```

The gate requires one condition/system, equal fixed human clusters per form, complete whole-panel agent run cohorts, original audit events, and no exclusions or withdrawals. Preserve inconvenient records; do not remove them to pass. Follow [REPORTING_PROTOCOL.md](REPORTING_PROTOCOL.md) for incomplete coverage, conditional uncertainty, and exploratory bootstrap limits. The investigator must verify registration authenticity and independence/design assumptions; software cannot establish them.

## 8. Verify and prepare the manuscript

```sh
python3 -m benchmark.verify --dataset data --output artifacts/release-checks-v5.json
python3 -m benchmark.verify --dataset data --deep --verbose --output artifacts/deep-checks-v5.json
```

The integrated gate includes the pinned Lean build. `bash formal/verify.sh` runs it separately. `--deep` adds exhaustive bounded regressions; `--verbose` changes logging only. `--emit-certificates PATH` separately persists private evidence. Consult the current report for exact counts, scopes and source hashes; older counts do not transfer.

For real-browser QA, install Playwright/Chromium in an isolated environment and run `node tests/browser_smoke.mjs`. `TRACE_PLAYWRIGHT_MODULE`, `TRACE_CHROME`, and `TRACE_PYTHON` select installed dependencies. Synthetic session reports and screenshots go under `artifacts/terminal-display-v5/session/`. `tests/general_browser_smoke.mjs` accepts a public compiled item JSON and output directory for renderer checks. These checks exercise interactions, privacy, timing, alternate answers and navigation; they do not establish enjoyment or comprehension.

Use [RESEARCH_ROADMAP.md](../RESEARCH_ROADMAP.md) for manuscript gates. Populate empirical slots only from actual locked evidence; verify every denominator, rendered page and source link. Declare unperformed arms and deviations. Keep formal, software and empirical evidence distinct, and preserve old releases without pooling their outcomes with v5.
