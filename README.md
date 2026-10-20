# TRACE — Temporal Reasoning And Causal Explanation

TRACE turns a finite Mealy machine, an observed input trace, and a target output at a specified time into a switch-and-light puzzle for humans and AI agents. The same task, cell identities, interaction rules and grader serve both interfaces.

Mark one inclusion-minimal explanation: fixing its recorded values guarantees the target light; changing only marked values can prevent it. Any valid minimal alternative is accepted. This is temporal causal explanation, not minimum-cardinality optimization. Visual examples teach the two conditions. There is one target lamp: every successful final route reaches it, and every failed final route reaches the dark exit. Earlier outputs appear as status indicators.

## Play the public lab demo

The [GitHub Pages demo](https://official-auralin.github.io/TRACE/) is the public, learning-enabled mode. It gives immediate feedback, supports retries and explicit solution reveals, and continues through the available public puzzle pool. Progress is saved on the current browser; TRACE does not upload demo scores. First submissions, eventual completion and assistance are separate. Structural bands describe machine size, not a measured difficulty scale.

Build and serve only the public artifact locally:

```sh
python3 -m benchmark.demo --output artifacts/pages-demo
python3 -m http.server 8890 --directory artifacts/pages-demo
```

Open `http://localhost:8890`. Use a new output directory that does not already exist for each build. The export imports the existing certified package; it neither constructs new machines nor ships stored answer keys. The browser's exact grader is a tested implementation of the same G/P recurrence, not a new Lean proof. The public code and editable local records make this a lab demonstration, not a secure research collection system. See [the demo protocol](docs/DEMO_PROTOCOL.md) and [deployment instructions](docs/DEPLOYMENT.md).

## Run the separate server study mode

```sh
python3 -m benchmark.server --port 8877 --db runs/play-v5.sqlite3
```

In another terminal:

```sh
python3 -m benchmark.session create --db runs/play-v5.sqlite3 --cohort baseline --participant local-play-v5 --split tutorial --form tutorial-01 --base-url http://127.0.0.1:8877
```

Open the returned private participant link. Use a new database/session for the new release; v3 and v4 playtest records are preserved. The default reasoning condition has no experiments. The optional probe condition is a separate study condition. Timers and probe budgets are configurable operator choices, not mathematical size limits.

Only `benchmark.server` should serve research participants. The explicitly exported Pages demo is a separate mode. Never serve the repository as a static directory: researcher artifacts and raw records are private. The server's v5 study mode retains its original single-response, receipt-only scored trials; the demo's continuous feedback is not silently substituted into that protocol.

## Import a machine and make a game

Build the pinned Lean tools once, then import the supplied example:

```sh
bash formal/verify.sh
python3 -m benchmark.compile examples/external-loop.jsonl --output artifacts/example-package
python3 -m benchmark.server --dataset artifacts/example-package --port 8878 --db runs/example-v5.sqlite3
```

Create its play link using `benchmark.session create --dataset artifacts/example-package --db runs/example-v5.sqlite3 --cohort baseline --participant example --split tutorial --form tutorial-01 --base-url http://127.0.0.1:8878`.

The example is an independently specified integration fixture, not an item received from TempoBench's authors. It has loops, three Boolean inputs, and recorded outputs `1,0,1`. Its target depends on earlier input choices. The compiler preserves every input intervention, including routes absent from the recording.

Input is JSONL: each record supplies `machine`, `observed`, and `target_step`; optional `id`, `split`, `family`, recorded outputs/states and provenance are documented in [the input contract](docs/INPUT_FORMAT.md). The initial contract is a total deterministic Boolean-input/Boolean-output machine, with an actually positive output at the target. It does not silently import constrained interventions or arbitrary temporal formulas.

## Construct a dataset independently

```sh
python3 -m benchmark.construct --count 20 --states 4 --inputs 3 --horizon 8 --seed 42 --output artifacts/source.jsonl
python3 -m benchmark.compile artifacts/source.jsonl --output artifacts/custom-package
```

Dataset construction is optional and never runs during import or play. External datasets use the same compiler. `--temporal` requires earlier-round dependence; `--max-attempts` is a configurable sampling budget. Size has no preset semantic cap, but each instance and target window must be finite and fit the chosen infrastructure.

A compiled package contains four files: `dataset.json`, `items.jsonl`, `forms.json`, and `manifest.json`. Byte indexing loads one task at a time. No answer key, source recipe or detailed certificate is needed for play. `--verbose` changes logging; `--emit-certificates artifacts/proofs.jsonl` saves detailed private evidence without weakening or strengthening validation.

## Verify and evaluate

```sh
python3 -m benchmark.verify
python3 -m benchmark.verify --deep --output artifacts/release-checks.json
python3 -m benchmark.evaluate --help
```

Verification combines a clean Lean build, software tests, source/level correspondence, concrete certificate checks and the deployed browser interpreter. Deep mode additionally runs exhaustive small-instance audits. It does not claim exhaustive enumeration of large tasks. Real-browser checks and their scope are reported separately.

The default corpus has 1,024 agent-test items and a distinct 64-item matched panel. Their estimands remain separate. Human ease, empirical difficulty, enjoyment and live-model performance require actual trials; technical verification supplies none of these findings.

## Repository map

| Location | Responsibility |
|---|---|
| `benchmark/core.py`, `game.py`, `level.py` | Input contract, backward G/P grading, public level interpretation |
| `benchmark/compile.py`, `formal/Trace2/Compiler.lean` | Import orchestration and the proved executable semantic constructor |
| `benchmark/construct.py` | Optional standalone source-dataset construction |
| `benchmark/runtime.py`, `server.py`, `session.py`, `web/`, `adapters/` | Common task service, human puzzle and agent transport |
| `benchmark/demo.py`, `demo/` | Curated Pages export, exact local grading, continuing play and local agent session transport |
| `formal/`, `tests/`, `benchmark/reference.py`, `verify.py` | Formal proof, independent oracle and verification |
| `data/` | Current task package; generated details are kept elsewhere |
| `docs/`, `tex_files/`, analysis commands | Research protocols, manuscript and analysis |
| `results/` | Compact current evidence and links to detailed artifacts |
| `artifacts/`, `runs/` | Ignored generated artifacts and private operator records |
| `archive/` | Locally preserved superseded releases and private evidence; excluded from public Git and Pages |

Start with [the algorithm](docs/ALGORITHM_SPEC.md), [claim-to-evidence map](docs/EVIDENCE_MAP.md), [dataset card](docs/DATASET_CARD.md), and [formal trust boundary](formal/TRUST_BOUNDARY.md). The [research roadmap](RESEARCH_ROADMAP.md) keeps institutional, pilot, registration and collection gates explicit.

GitHub updates use small validated commits; Pages deploys only the curated artifact after verification. The published corpus is public benchmark material. Future concealed-item or mechanism-generalization claims need separately reserved data. Original repository history and local archives are preserved. Attribution is recorded in `formal/PROVENANCE.json`; a software/data reuse license has not yet been selected.
