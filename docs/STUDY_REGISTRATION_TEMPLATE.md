# Study freeze and registration record — complete before main testing

**Frozen item sets:** 1,328 total = 16 tutorial + 32 pilot + 256 development + 1,024 held-out agent-test items. The matched human–agent analysis uses a predesignated 64-item panel (eight items per test structural stratum, 16 four-item forms). Full-pool agent scores use 1,024 items and are reported separately. All references below to human test coverage or J in a human comparison mean this 64-item panel. Eight judgments per panel item require 128 usable humans per condition; this is a coverage target, not established power.
This is an operator record, not an assertion of preregistration. Complete it after the pilot, archive the frozen version in a stable registry or approved immutable record, and record the resulting identifier. Do not backdate decisions or leave test-informed changes unreported.

## Identity and release

| Field | Value |
| --- | --- |
| Study title / study ID | `[COMPLETE]` |
| Responsible investigator / institution | `[COMPLETE]` |
| Required institutional determination identifier/date | `[COMPLETE]` |
| Public registration or immutable-record URL/identifier/date | `[COMPLETE AFTER ARCHIVING]` |
| Dataset version and complete manifest hash | `[COMPLETE]` |
| Code revision and protocol version | `[COMPLETE]` |
| Pilot sample and disposition report | `[COMPLETE]` |
| Date final test release was locked | `[COMPLETE]` |
| Had any main test outcomes been inspected before this record? | `[YES/NO; explain]` |

## Fixed primary analysis

- Task: `explanation`; equal-item-weight exact-set accuracy over the frozen 64-item shared panel; agent-only 1,024-item results are reported separately.
- Primary condition: `reasoning` (zero probes), 480 seconds, one scored submission, public complete switchboard and recorded path, shared visual examples and optional equivalent machine encoding.
- Human–agent gap sign: agent accuracy minus human accuracy, in percentage points.
- Uncertainty: Register the conservative fixed-design bound and its independence/coverage eligibility assumptions; whole agent run cohorts remain intact across forms. Any cluster bootstrap is exploratory unless separately justified and registered. The test items are fixed.
- Primary model/system ID: `[COMPLETE ONE SYSTEM]`.
- Additional systems/contrasts and multiplicity plan: `[COMPLETE; secondary unless declared otherwise]`.
- Optional `probe` condition: `[RUN / NOT RUN]`; between-participant allocation with eight probes, otherwise identical protocol.

## Recruitment and allocation

| Decision | Value fixed before main outcomes |
| --- | --- |
| Recruitment population/channel | `[COMPLETE]` |
| Eligibility and any behavior-based exclusion | `[COMPLETE; no performance-based exclusions]` |
| Compensation and withdrawal policy | `[COMPLETE]` |
| Four-item form schedule and allocation seed/hash | `[COMPLETE]` |
| Matched panel item count J | 64; verify against the final frozen manifest |
| Target usable participants per condition | `[COMPLETE]` |
| Target independent human judgments per item/condition | `[AT LEAST 8 BY DEFAULT; document precision decision]` |
| Precision simulation or fixed-resource rationale | `[COMPLETE WITH ASSUMPTIONS AND OUTPUT]` |
| Reserve recruitment cap and replacement rule | `[COMPLETE]` |
| Stop rule/date and insufficient-coverage handling | `[COMPLETE]` |
| Pilot participants excluded from main sample | `[CONFIRM]` |

A minimum coverage target is not a power guarantee. Register a feasible fixed sample and acknowledge its precision; do not recruit until a desired result appears.

## Agent configuration

For every system, attach the completed record from [AGENT_PROTOCOL.md](AGENT_PROTOCOL.md), including exact snapshot, full prompt, adapter revision, settings, token cap, tools, timeout and repetitions. Default: five isolated repetitions per item. Record paid-inference budget and operator authorization separately from credentials.

## Data and deviations

Specify data access, retention, withdrawal/deletion process, public-release permission and handling of identifying free text. Store consent/contact/payment records separately. Preserve technical failure evidence; score ordinary wrong, invalid and timed-out attempts as failures. Log deviations with date and whether outcomes had been seen.

**Investigator sign-off and date:** `[COMPLETE]`

**Independent protocol check, if performed:** `[NAME/ROLE, DATE, FINDINGS; do not invent]`

## Machine-readable analysis gate

Complete `analysis_registration.template.json` as a separate actual registration record before collection. Its shipped draft values intentionally cannot authorize confirmatory output. Bind the frozen dataset, forms, protocol, study source, analysis source and agent configuration; record the actual registry identity/date, fixed sample counts and scientifically reviewed assumptions. The current gate supports one condition/system, equal complete human clusters per form and full-panel agent run clusters without exclusions or withdrawals. Keep excluded or withdrawn records in the audit ledger; never omit them to obtain an eligible result. See REPORTING_PROTOCOL.md for the exact supported design and limitations.
