# TRACE lab demo on GitHub Pages

The first deployment milestone is a static lab demo with immediate feedback,
continuing play, and progress stored in the player's browser. It does not send
answers or scores to a TRACE collection service. The public interface uses
`trace.demo.v1`; the source tasks retain `trace-mealy-v5` and `trace.gp.v2`.

The collection backend is milestone two. Existing controlled study sessions
continue to use `benchmark.server` and their original protocol. Browser demo
records are neither authenticated research records nor substitutes for those
sessions. GitHub may maintain ordinary hosting access logs; the demo makes no
claim that the hosting provider records nothing.

## What is deployed

`python3 -m benchmark.demo` reads an already compiled package using the common
package loader. Each exported task is exactly the `public_item` projection used
by the study service: the machine, observed trace, target, and compiled public
board. Loading checks task hashes and the source/board correspondence. The
release workflow additionally runs the full software, formal, and certificate
verification; static export alone does not replace that gate.

The exporter copies only these allowlisted assets:

- `demo/index.html`, `app.js`, `engine.js`, `session.js`, and `style.css`;
- `web/board.js` and `web/style.css`, renamed `board-base.css` for the demo;
- generated `catalog.json`, `lessons.json`, `manifest.json`, `.nojekyll`, and one
  public JSON file per item under `items/`.

The artifact contains no server application, source package metadata, recipes,
answer keys, detailed certificates, private session links, research logs,
archives, or repository configuration. The five shared teaching examples expose
only their visible task, title, and caption initially. Teaching and ordinary
task files contain no solved answers or completion tables; the common browser
grader computes feedback or a solution only following the corresponding action.

All 1,328 current tasks are public in this demo, including the original tutorial,
pilot, development, and test splits. Those split names remain provenance labels;
they do not make the published test pool or 64-item matched panel hidden. A
future concealed evaluation needs fresh, unexposed items and a separate release
policy. The 1,024-item full test estimand and 64-item panel estimand remain
distinct in the existing study tools.

The catalog gives structural bands based on states, input channels, and horizon.
They are navigation groups, not empirically calibrated difficulty levels.
Export has no extra semantic size cap. Finite imported packages can be larger;
actual browser memory, rendering, network transfer, and grading costs still
limit a particular device. Dataset construction remains an optional standalone
step, never part of play or static export.

## Build and inspect locally

From the repository, using Python 3.10 or newer, Node 18 or newer, and the pinned
Lean 4.24.0 toolchain:

```sh
python3 -B -m benchmark.verify --output artifacts/demo-verification.json
python3 -B -m benchmark.demo --output artifacts/pages-demo
python3 -m http.server 8890 --bind 127.0.0.1 --directory artifacts/pages-demo
```

Open `http://127.0.0.1:8890/`. Serve this curated artifact directory, never the
repository root. The study client in `web/` still requires `benchmark.server`;
copying it unchanged to Pages would leave its `/api` requests without a server.

For an independently imported package, provide `--dataset artifacts/my-package`.
The exporter never invokes the dataset constructor or recompiles board recipes.
The output directory must not already exist; choose a new artifact name for the
next build. No existing user directory is erased or replaced.

Each item's filename is derived from its ID hash; an item ID is never used as a
filesystem path. All application URLs are relative so the same artifact works
at the GitHub project path `/TRACE/`. The catalog's `package_id` binds task
payloads, ordering, teaching content, semantics, and the demo protocol. Its
`build_id` also binds presentation assets. Cosmetic releases preserve compatible
local progress; changes to scoring or interaction semantics require a new
protocol version. The manifest lists the exact hash of every other artifact
file. No timestamps, absolute operator paths, or tokens enter this build identity.

## One-time GitHub setup

The intended remote is `git@github.com:official-Auralin/TRACE.git`; the intended
project site is <https://official-auralin.github.io/TRACE/>. Repository and
deployment status must be checked rather than inferred from these addresses.

If GitHub requires an administrator to finish enabling publication:

1. Open the repository's [Settings → Pages](https://github.com/official-Auralin/TRACE/settings/pages).
2. Under **Build and deployment**, set **Source** to **GitHub Actions**. Do not
   choose the repository root or `/docs` as a static branch publishing source.
3. Open [Actions](https://github.com/official-Auralin/TRACE/actions) and select
   **Verify TRACE and deploy demo**. Allow Actions for this repository if GitHub
   shows an explicit disabled-actions banner. Organization policy may require
   an administrator to allow the pinned official `actions/*` actions.
4. Once the validated changes are on `main`, open that workflow's run. It must
   pass its verification job before the deployment job becomes eligible. If
   you changed Pages settings after a failed setup attempt, rerun the workflow
   on `main` using **Run workflow**.
5. If the `github-pages` environment requests an approval, review and approve
   that deployment. Do not remove an existing review requirement merely to
   silence the prompt.
6. Open the URL printed by the completed deployment. Verify the new demo's
   version, instruction flow, first submission feedback, retry, next puzzle,
   and refresh/resume. A successful source push alone does not establish that
   these actions work on the live site.

The workflow uses GitHub's short-lived Pages deployment credentials. No personal
access token, study secret, backend account, or paid hosting service is required
by the static demo. GitHub Pages is a static hosting service and cannot execute
the existing Python/SQLite collection backend. See GitHub's documentation on
[custom Pages workflows](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
and [publishing sources](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site).

## Updates and release checks

`.github/workflows/pages.yml` checks pushes to working branches and pull requests.
On an eligible `main` revision, it deploys only after all prior steps succeed:

1. Install checksum-verified Lean 4.24.0, Python 3.12, and Node 22 on Linux.
2. Run `benchmark.verify`, including the clean Lean proof build, tests, package
   certificate checks, and source/browser execution comparisons.
3. Build two static artifacts and compare their bytes.
4. Exercise the game in headless Chromium under a project subpath.
5. Upload only `artifacts/pages-demo`, then deploy it using the Pages environment.
6. Request the deployed public catalog and validate its exact expected build ID,
   protocol, and item count, allowing a short bounded CDN propagation delay.

GitHub Actions are pinned to full official action commit IDs. Browser testing
uses pinned Playwright 1.64.1 in the runner's temporary directory; it is not a
runtime dependency of the game. Linux CI success and live-browser success must
be reported from actual completed runs, not from the existence of this workflow.

Keep changes small and push validated milestones to the working branch. Merge
the reviewed revision into `main` without rewriting history, then wait for
deployment and inspect the live game. Use a release tag for stable milestones.
For rollback, restore the relevant prior source/assets through an ordinary
reviewed commit and rerun the same gate; do not serve an unreviewed repository
snapshot. Private logs and historical archives remain preserved locally.

## Milestone two: authoritative collection

The next deployment phase needs a chosen host for the existing Python service,
durable storage and tested restoration, HTTPS and explicit origin handling,
session credentials, and version-compatible client/server requests. It must
implement immutable first submissions and separate retry/assistance records,
with matched human/agent instruction and feedback histories. Public adaptive
play needs a versioned analysis design; the fixed-form study analysis cannot
simply be applied to it.

Before research recruitment, complete the institution's required determination,
participant information, consent and retention policies, pilot gates, and
registration where applicable. The public lab demo collects none of that on
TRACE's behalf and supplies no evidence that these gates have been met. Local
scores can be edited or erased by the browser user; they describe play progress,
not verified unaided human performance.
