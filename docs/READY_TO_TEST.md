# TRACE v5 testing handoff

The current game imports finite Mealy-machine/trace/target records into a common human–AI task. Its semantic transformation and executable checks are separate from the still-required usability, human difficulty and live-model studies. Consult the current [acceptance ledger](IMPLEMENTATION_STATUS.md) and source-bound reports for technical status; archived v3/v4 test counts do not describe this release.

## Play the default tutorial form

Start the restricted service in the active repository:

```sh
cd '/Users/bobby/Documents/Academics/CU-Classes/PL Lab/Fall26/TRACE'
python3 -m benchmark.server --port 8877 --db runs/play-v5.sqlite3 --dataset data
```

In another terminal:

```sh
cd '/Users/bobby/Documents/Academics/CU-Classes/PL Lab/Fall26/TRACE'
python3 -m benchmark.session create --db runs/play-v5.sqlite3 --dataset data --cohort baseline --participant local-play-v5 --split tutorial --form tutorial-01 --seconds 480 --base-url http://127.0.0.1:8877
```

Open the returned private URL. The default tutorial form has four puzzles with feedback, preceded by five untimed visual examples. A puzzle's timer starts when opened; one answer is accepted. Practice feedback supplies an example and diagnostics, not a complete answer inventory.

Follow the recording and mark switches that explain why the highlighted target light is on. Holding those recorded settings must guarantee the target; changing only marked settings must allow it to turn off. Leave no unnecessary marks. Earlier ON/OFF indicators are not goals. All successful final routes reach the same target lamp. Identical full time/channel labels refer to one cell; the same channel at another moment is distinct. Use pan, zoom, overview or Moment/Route/Go for a larger board; the switch strip retains every original input, including tests skipped by a simplified route. Replaying the recording is not an experiment.

For the default study rehearsal, create a separate baseline session with `--participant local-pilot-v5 --split pilot --form pilot-01`. It has two practice items and four scored items with correctness withheld. `--condition probe --probes 8` tests the optional probe arm. `--seconds` and `--probes` are configurable study budgets, not limits on machine size. Keep operator sessions separate from research databases.

## Play the external-machine example

```sh
bash formal/verify.sh
python3 -m benchmark.compile examples/external-loop.jsonl --output runs/external-example
python3 -m benchmark.server --port 8878 --db runs/external-example.sqlite3 --dataset runs/external-example
```

In another terminal:

```sh
python3 -m benchmark.session create --db runs/external-example.sqlite3 --dataset runs/external-example --cohort baseline --participant external-play --split tutorial --form tutorial-01 --base-url http://127.0.0.1:8878
```

This independently supplied example contains loops, multiple inputs and nonlatching outputs. Its tutorial form has one item. The AI evaluator can use the same package with `--dataset runs/external-example`; no dataset constructor runs during play or evaluation. Compilation output directories must be new or empty.

## Reproduce the technical checks

```sh
python3 -m benchmark.verify --dataset data --output artifacts/release-checks-v5.json
python3 -m benchmark.verify --dataset data --deep --output artifacts/deep-checks-v5.json
```

The integrated gate builds Lean, runs focused software tests, checks the package, and compares browser interpretation with source execution over the stated scope. Deep mode adds bounded exhaustive regressions. Run `bash formal/verify.sh` separately when checking only the formal development. Use the pinned toolchain in [formal/README.md](../formal/README.md).

`--verbose` controls diagnostic detail; it does not weaken checks or save certificates. Add `--emit-certificates PATH` only when detailed private evidence should be persisted. Ordinary packages contain no answer keys or detailed certificates. Exact current counts and bounds belong in the resulting report, not a claim that every large input was exhaustively tested.

`node tests/browser_smoke.mjs` runs synthetic real-browser sessions with Playwright/Chromium as described in the [runbook](RESEARCHER_RUNBOOK.md). Renderer/navigation checks are also available in `tests/general_browser_smoke.mjs`. Screenshots and reports are generated artifacts. Rebuild and inspect the manuscript separately when it changes.

## Before a recruited pilot and main comparison

Complete the actual institutional determination, contacts, compensation, retention and withdrawal fields before recruitment. Pilot with 6–10 consenting adults on pilot items, using the standardized materials. Observe comprehension, target-time interpretation, linked switches, navigation, accessibility, enjoyment and burden; accuracy alone cannot diagnose interface understanding. Navigation telemetry is debounced and best effort, not a complete record of actions or reasoning time.

Revise both modalities when the pilot identifies a problem. Preserve logs, version changes, and repeat affected checks. The five small teaching boards do not by themselves establish that the larger general presentation is intuitive.

Before main outcomes, freeze package, instructions, budgets, model configurations, sampling, stopping, exclusions, multiplicity and analysis. Register the design and verify provider transport on development data. Report the default 64-item comparison separately from the 1,024-item agent pool; imported packages must state their own scope. Structured AI and visual human interfaces share information without established equality of perceptual effort.

Serve participants only through `benchmark.server`. Keep source data, private evidence, archives and previous outcomes outside participant access. Preserve `archive/v4-multiple-targets`, `archive/v3-switchlight` and older releases; their records do not validate or pool with v5. Populate empirical manuscript slots only from actual appropriately collected evidence.
