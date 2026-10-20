# Current evidence

This directory contains concise, source-bound release summaries. Detailed generated tables, witnesses, browser screenshots and build output belong under ignored `artifacts/` or immutable release artifact storage. A command's verbosity never changes its scientific checking.

- `release_checks.json`: current clean formal build, software tests, concrete-data checks and browser interpreter audit.
- `release_manifest.json`: hashes for current source, data, compact evidence and optional detailed evidence bundles.
- `browser_checks.json`: actual browser checks and their exact scope, separate from interpreter checks.
- `pdf_checks.json`: final manuscript build/render inspection, not empirical evidence.
- `reproducibility.json`: exact source and four-file package reproduction, with the release temporal filter checked.
- `baseline_summary.json`: measured non-learning instrument baselines; private raw rows remain under `artifacts/`.
- `archive_preservation_v5.json`: frozen v4 snapshot integrity, including the screenshot and two preserved playtest backups.

Only files that exist with PASS and matching recorded identities constitute completed evidence. Reports may be absent while a release is under construction. Historical v4 reports stay in `archive/v4-multiple-targets/results`. Historical v3 reports and raw computational baselines are preserved with their sources under `archive/v3-switchlight/results`; v2 remains in its own archive. Never substitute an archived PASS for a current failed check.

No report here establishes enjoyment, human ease, psychometric validity, or live-model performance. Those require the actual study gates in RESEARCH_ROADMAP.md.
