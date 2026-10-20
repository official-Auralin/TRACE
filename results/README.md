# Current evidence

This directory contains concise, source-bound release summaries. Detailed generated tables, witnesses, browser screenshots and build output belong under ignored `artifacts/` or immutable release artifact storage. A command's verbosity never changes its scientific checking.

- `release_checks.json`: the latest completed clean formal build, software tests,
  concrete-data checks and browser interpreter audit. Its source hashes identify
  the checked revision; a later source edit requires an affected-check rerun.
- `demo_checks.json`: the static `trace.demo.v1` artifact, repeatability and real
  Chromium interaction checks. Browser/agent adapters remain tested code outside
  the Lean kernel proof. The report identifies the exact package and build.
- `release_manifest.json`: a compact inventory of current source, data and
  evidence hashes, with current demo checks separated from retained historical
  evidence. It does not inventory every generated private artifact.
- `browser_checks.json`: retained `trace-study-v5` server-session and target-display
  browser evidence from the earlier release. It does not certify the new static
  demo or changed study-source identities.
- `pdf_checks.json`: latest completed manuscript build/render inspection for the exact
  files named in its hashes. It is not evidence for later manuscript edits or
  empirical findings; inspect hash identity before relying on it.
- `reproducibility.json`: retained v5 source and four-file package reproduction,
  with its stated historical constructor scope. It is separate from the new
  static artifact repeatability check.
- `baseline_summary.json`: retained non-learning computational instrument
  baselines over the v5 dataset. These are neither learning-enabled demo runs
  nor human or live-model results; private raw rows remain under `artifacts/`.
- `archive_preservation_v5.json`: frozen v4 snapshot integrity, including the screenshot and two preserved playtest backups.

Only files that exist with PASS and matching recorded identities constitute completed evidence. Reports may be absent while a release is under construction. Historical v4 reports stay in `archive/v4-multiple-targets/results`. Historical v3 reports and raw computational baselines are preserved with their sources under `archive/v3-switchlight/results`; v2 remains in its own archive. Never substitute an archived PASS for a current failed check.

Local verification, clean Linux CI, and live GitHub Pages deployment are separate
claims. A workflow file or a successful source push supplies no evidence that a
remote workflow or deployment completed. Consult actual run results and the
deployed build ID when reporting those outcomes.

The demo publicly exposes the current corpus, including the original test/panel
items. Existing split labels do not establish a concealed evaluation pool.
Browser-local learning records are editable personal progress and must not be
analyzed as authenticated study data with the fixed-design reporting tools.

No report here establishes enjoyment, human ease, psychometric validity, or live-model performance. Those require the actual study gates in RESEARCH_ROADMAP.md.
