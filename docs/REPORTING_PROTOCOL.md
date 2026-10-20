# TRACE analysis and reporting protocol

No empirical outcomes are asserted here. Synthetic instrument sessions and computational baselines must remain separate from humans and evaluated language models.

The rules below govern `trace-study-v5`. Public `trace.demo.v1` progress is editable browser/agent-local state, not an authenticated raw study export. Do not feed it into this fixed-panel confirmatory procedure, relabel retries as first attempts, or pool it with v5 trials. A learning-enabled collection release requires its own exposure-aware assignment, event schema and analysis. Published v5 test and panel items are public benchmark material, not concealed holdouts.

## Identity and regrading

Analyze immutable raw exports and retain input byte hashes. Identify each outcome by session and item. Record dataset, forms, semantics, protocol, source identities and actual interaction limits. Use `--dataset PACKAGE_DIR` to select the compiled package matching the logs. Reject incompatible releases, duplicate outcomes, mixed budgets within a system/condition, and scores that disagree with recomputation.

A system label does not identify its configuration by itself. Provider/model identity, generation settings, prompt/adapter identities, regime and declared registration metadata must be consistent within an analyzed system. Distinct evaluator invocations have distinct run IDs. Preserve returned provider model IDs and truncation/transport outcomes.

Each ordinary submitted set is regraded for G, P and deletion minimality directly from the machine/trace/target. Stored keys and complete answer families are unnecessary. Any valid minimal answer is correct. Canonical-solution F1, precision and recall are retired because multiple accepted explanations need not share their cells.

## Fixed-item estimand

For the fixed item set J, average eligible response correctness within each item, then average equally across J. Report each item's denominator. A missing item makes the intended full-panel estimate unavailable, rather than reducing J silently.

For the default release, the matched gap is agent accuracy minus human accuracy on the same 64 items and condition. Full 1,024-item agent scores are a separate table. An imported package can have a different explicitly frozen panel and full pool. Report the exact item set and budgets with every statistic; never silently substitute the default counts. A human–AI contrast requires matching instructions and interaction limits, and it does not establish equal perceptual effort between visual and structured interfaces.

## Independent units and conservative uncertainty

A human participant is one cluster. An agent run cohort is one cluster across all forms/items belonging to that run/repetition; it must not be split into artificial independent form clusters. Fresh context per item is an operational isolation rule, not a proof of statistical independence.

For a fixed, outcome-independent observation design, write the equal-item estimate as a sum of cluster contributions. Cluster c has contribution range of width

w_c = sum over its observed items j of 1/(|J| n_j).

The weights sum to one when coverage is complete. Under independent clusters, Hoeffding's inequality gives a two-sided error radius

epsilon = sqrt(log(2/alpha) * sum_c w_c^2 / 2).

Intersect the resulting accuracy interval with [0,1]. For a gap between independent populations, use the combined squared weights and intersect with [-1,1]. These are conservative conditional bounds. They do not cover unmodeled dependence, adaptive model selection, informative dropout, benchmark distribution shift, or arbitrary extrapolation to unseen items. A small number of agent run cohorts can produce a nearly uninformative bound; report that directly.

Confirmatory use requires an explicit eligibility/design review and preregistration. The implemented gate is `benchmark.analyze --confirmatory --registration runs/registered_analysis.json`. Begin from `docs/analysis_registration.template.json`; its draft status, blank identities, null counts and false attestations deliberately fail validation. A local JSON record is not itself registration.

The supported confirmatory design is one condition and one declared agent system on the fixed test panel, with a fixed equal number of complete human clusters per form and complete full-panel agent run cohorts. The gate checks registration time before collection; dataset, forms, protocol, study-source, analysis-source and agent-configuration identities; planned cluster counts; interaction limits; and the original session, trial-start and outcome audit events. It rejects mixed configurations, incomplete clusters, exclusions, withdrawals and incomplete raw exports. Preserve those records; do not remove them to make the gate pass. Other designs or deviations require a separately justified analysis and are exploratory under the current implementation.

The current template uses `trace.analysis-registration.v2`, with `limits={"attempts":1,"seconds":480,"probes":0}` for the default reasoning condition. Record the actual positive finite time and nonnegative probe budget; reasoning requires zero probes. Session records, trial records, and deadlines must match the registered values. Legacy schema v1 remains accepted only with its original 480-second and 0-or-8-probe defaults. Neither a valid JSON template nor a passing gate establishes that external preregistration or institutional approval occurred.

The researcher must attest to authentic registration, independent clusters/populations, fixed allocation/sample/stopping, noninformative missingness and complete export. Software validates the record and observable constraints, not the truth of these scientific assumptions. Accepted output remains explicitly conditional on these attestations; it is not an unconditional guarantee.

The available cluster bootstrap is exploratory. Resample whole participants or whole agent cohorts, preserving their responses across forms. Do not claim its percentile intervals have nominal 95% coverage merely because 10,000 draws were requested. Hypothetical calibration scenarios document finite-sample behavior and assumptions; they are not measured study results or universal validation.

## Dispositions and secondary measures

Report started, completed, correct, wrong, nonminimal, malformed, timed-out, technically excluded and withdrawn records with clear denominators. Preserve request IDs and rejected extra-attempt events; do not count retransmissions of the same idempotent request as new answers.

For ordinary parsed responses report:

- guarantee pass/fail;
- prevention pass/fail;
- valid-but-nonminimal rate;
- exact explanation accuracy.

For invalid formats and no-answer verdicts, respect the schema's applicability fields rather than inventing an explanatory-set diagnosis. Report latency with the actual timeout cap, simulator use, provider limits, and operator resource exhaustion separately. A resource failure is not a no-explanation verdict. Computational baselines have no participant time limit and must be identified separately from timed participant runs.

Descriptive strata can include horizon, state count, input count and measured explanation sizes. The package does not enumerate all accepted explanations or compute exact random-subset chance rates by default. Accepted-family counts require an explicit bounded audit and its scope; do not infer them from the one checked canonical example. Structural size is not an empirically validated difficulty label. Do not infer the participant's internal method from answer shape.

Report navigation event counts separately from causal accuracy and G/P diagnostics. They are debounced, best-effort client reports with server timestamps, not all physical actions or time spent reasoning. Telemetry is not awaited before submission, so the last event can be absent. The structured agent adapter does not produce equivalent browser gestures. State instrument coverage and missingness; do not use missing agent events to infer lower reasoning effort or missing human events to infer no navigation.

## Primary and secondary hypotheses

Register one primary model–human contrast. Declare remaining models, probe effects, family strata and sensitivity analyses secondary or exploratory, with a multiple-comparison policy if formal testing is planned. A confidence interval containing zero is not proof of equivalence. Ceiling performance limits benchmark discrimination. A favorable gap is not evidence of general intelligence or general temporal-causal superiority.

## Required result tables

1. Current dataset version, source/manifest hash, retained items, precise split and selection definitions, certificate/validation outcomes.
2. Human recruitment/disposition and agent request/run disposition; model configuration and independent cluster counts.
3. Equal-item exact accuracy and eligible uncertainty on the matched panel; a separate full-agent table.
4. Guarantee, prevention and minimality errors; malformed/timeout/technical rates; timing/probes with budgets and denominators; navigation counts in a separate descriptive field.
5. Optional probe contrast under matched allocation and otherwise matched protocol, or explicit statement it was not run.
6. Prespecified/exploratory error analysis, limitations, deviations and missing coverage.

Computed deterministic baselines over the full fixed corpus do not need fabricated sampling intervals.

## Reproduction and release

Use `benchmark.analyze --dataset PACKAGE_DIR --scope panel` for comparisons and `--scope full` for the agent-only pool. Omitting `--dataset` selects the current `data/` package. Preserve summary output, normalized rows, generated TeX, raw-file hashes and source/protocol identity. Validate that computed groups match the registered configurations.

Enrollment, compensation, consent, manually coded errors and permitted deletion require operator records; the analysis cannot infer them. Release only records permitted by the actual consent/data policy. Keep credentials, participant contact mappings and identifying text private.

Link each paper number to a generated field and immutable input identity. Old v1 union logs, rejected v2 table-interface playtests, v3 board-first outcomes, and v4 ambiguous-target display outcomes cannot be pooled with v5. Even when an answer contract is shared, construction, presentation and teaching differ. Historical records remain under their preserved releases, including `archive/v2-textbook`, `archive/v3-switchlight` and `archive/v4-multiple-targets`. Current random and all-switch baselines select from the public input inventory, which includes every original cell; a cell skipped by a simplified decision tree is still available. Report raw source/dataset identity with every analysis.
