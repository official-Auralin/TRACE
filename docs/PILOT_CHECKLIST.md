# Pilot checklist and disposition record

**Purpose:** validate readability, instructions, timing and operation before the main study. **Target:** 6–10 adults, pilot split only. **Not a purpose:** demonstrating a human–agent gap or selecting favorable test items.

## Before first pilot

- [ ] Required institutional determination and completed participant information/consent materials are on file.
- [ ] Package/forms hashes, pilot split, source/protocol revision, modality, actual time/probe budgets and any operator transport limits are recorded. The dataset constructor is not invoked during sessions.
- [ ] Public observations contain no answer keys or certification metadata.
- [ ] Browser, keyboard/mouse operation, desktop/mobile layout, text zoom and color-independent target markers are checked on the actual study machine. Pan, zoom, overview, direct moment/route navigation, and the full input inventory are reachable.
- [ ] An operator dry run has tested all/none selection, submission lock, timeout, optional probe exhaustion, refresh/reconnect and technical-failure logging.
- [ ] Consent and contact records are stored separately from trial logs.
- [ ] The operator can explain the difference between guarantee, supported prevention, and inclusion-minimality without adding a strategy hint.

## Per session

Record `pilot_id`, date, package/protocol version, condition, actual limits, form/items, browser/device, instruction duration, practice corrections, scored-item timings, navigation difficulties, technical issues and debrief themes. Use a pseudonymous ID. Navigation telemetry is debounced and best effort; its server timestamps and counts do not measure reasoning time or establish complete physical-action coverage.

- [ ] Consent obtained under the actual approved/determined procedure.
- [ ] Five visual demonstrations viewed without mandatory formal-rule reading; assigned practice items completed (two by default). Record whether the participant can identify recorded directions and alternatives, explain HOLD and CHANGE ONLY MARKED, and reject an extra mark. Include XOR and the difference between some confined change and flipping every selected cell. Practice feedback supplies examples, not every correct answer.
- [ ] General-game comprehension checked: output can change between moments; one target lamp alone determines the event; identical full time/channel labels share one cell; an original input remains selectable even when a simplified route skips its test.
- [ ] Without the technical drawer, the participant identifies the same goal for two distinct successful routes and when the lamp is off; an earlier ON status followed by final OFF is failure.
- [ ] Conditional relevance is checked: a final switch omitted on one route can remain decisive on another; a removal illustration does not imply that it never matters.
- [ ] No displayed switch distinguishes only post-target states; all successful final paths visibly converge on the target and all failed paths on the dark exit. Gold playback is interpreted as the chosen execution, not a second goal.
- [ ] Only the prespecified pilot form shown (four scored items by default); no main-test item or answer shown.
- [ ] No extra scored attempts or unlogged time extensions.
- [ ] Any timeout remains a timeout; ordinary errors are not technical exclusions.
- [ ] Operator records ambiguous crossings, hidden/off-screen mechanisms, playback confusion, target-time confusion, navigation burden, notation problems and any need to consult the formal drawer or run experiments to understand the task. Low accuracy alone does not establish an interface problem.
- [ ] Debrief asks whether the board feels like a puzzle, whether an answer can be reasoned out before submission, and about enjoyment, unclear instructions, technical problems and timing without revealing study hypotheses.
- [ ] Exported trial count, responses, limits and status match the session record. Missing final navigation telemetry is reported as an instrumentation limitation, not absence of navigation.

## Pilot review table

| Issue ID | Evidence / affected pilot IDs | Type | Proposed change | Shared human/agent impact | Version | Retest evidence | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `[fill from observations]` | | wording / layout / timing / technical | | | | | |

Report pilot accuracy descriptively only when useful for calibration and clearly separate it from the main sample. Do not report a precise power estimate based on a small pilot effect. If the pilot reveals a ceiling or near-chance endpoint, investigate the task and baseline mechanism before locking the main study; do not silently select only items producing the preferred population gap.

## Main-study go/no-go

- [ ] No unresolved display or endpoint issue can change a participant's information or score.
- [ ] The final protocol records matching finite time and probe budgets for the populations being compared, with one submission. The default is 480 seconds and zero or eight probes; changed limits are prespecified and bound in schema-v2 registration.
- [ ] The visual examples and practice are understandable without a formal manual, exploratory trial-and-error or unscripted individualized coaching. If that fails, revise the presentation and repeat the pilot before proceeding.
- [ ] Dataset and scoring changes, if any, have full certification and new release hashes.
- [ ] Pilot participants are excluded from main enrollment.
- [ ] Actual main forms, order allocation and optional between-participant probe assignment are saved. Default forms have four items; imported packages must identify their own panel and sequence.
- [ ] Main sample size, precision rationale, coverage target, reserve cap and stopping rule are fixed before viewing main results.
- [ ] Exact model/prompt/tool settings and analysis plan are fixed.
- [ ] Structured AI and visual human modalities are documented as information-matched, without claiming equal perceptual effort. Extended agent-only tasks are not presented as measured human comparisons.
- [ ] Registration/immutable protocol record identifier and timestamp are completed.

**Decision:** `[READY / REPEAT PILOT / STOP AND REPAIR]`

**Responsible investigator, date and evidence links:** `[COMPLETE]`

A checked template is not evidence that these actions occurred. Fill `TRIAL-PILOT` in the manuscript only after this record contains actual observations and decisions.
