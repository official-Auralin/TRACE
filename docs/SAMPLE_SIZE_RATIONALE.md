# TRACE item count and sample planning

The release contains 1,024 agent-test target events. A predesignated 64-item panel supports the human–agent comparison. They are different item populations; no trial repetition creates an additional benchmark item.

Four scored items per person and eight independent human judgments per panel item requires 64*8/4 = 128 usable participants per condition. A second between-participant probe arm requires its own coverage. This arithmetic establishes coverage, not power or precision.

The default five model repetitions supply five run/repetition cohorts across the full pool, not five times the number of forms as independent replication. Dependence across items within a run is preserved in analysis. More repeated deterministic calls cannot substitute for broader model or task generalization.

Use benchmark.plan_sample for explicitly hypothetical planning, and inspect current interval-calibration output where available. No old release simulation is presented as current evidence; reports must match the current v5 dataset hash. State every scenario's response distribution, cluster dependence, missingness assumptions, seed and simulation count.

The conservative fixed-design bound in REPORTING_PROTOCOL.md may be wide, especially with few agent cohorts. That is evidence about the limits of the sampling design, not an error to hide. Register a defensible fixed sample and acknowledged precision, or increase independently justified replication before outcomes are examined.

A 6–10-person pilot assesses comprehension and burden. Its small observed effect estimates cannot establish reliable superiority power. Freeze the sample, reserves, stopping rule and primary contrast after the pilot and before main test outcomes. Report actual achieved coverage and missingness.
