# TRACE human–agent study protocol — registration draft

Status: prepared instrument and analysis plan, not an institutional approval, completed pilot, preregistration, or finding. Use dataset trace-mealy-v5 and protocol trace-study-v5. The validated G/P semantics remain trace.gp.v2.

## Question and population

The primary question is how accurately humans and specified AI systems identify one inclusion-minimal temporal explanation that guarantees a recorded outcome when fixed and permits prevention by changes confined to that explanation. The hypothesis that the task is easy for humans, or that agents perform worse, is untested.

For the default release, the primary comparative estimand is equal-item-weight exact explanation accuracy over the predesignated 64-item shared panel. Full-agent accuracy over 1,024 test items is reported separately. Imported packages require their own explicitly identified panel, forms and sampling plan. Neither scope supports automatic generalization to all controllers or temporal causal reasoning; structural size labels are not a validated difficulty scale.

## Locked default contract

| Element | Contract |
| --- | --- |
| Semantics | G(C) universal fixing guarantee AND P(C) existential supported prevention |
| Answer | Any inclusion-minimal valid cell set; no minimum-cardinality requirement |
| No-answer case | Separate no_explanation verdict, correct only when the target cannot be prevented |
| Public information | Complete visible routing graph, labelled switches and recorded positions/path, five common visual demonstrations, and equivalent Mealy encoding |
| Human display | Linked switches, alternative routes, recorded signal, earlier output status indicators, one shared target lamp and dark exit, and selectable blue marks; technical encoding is optional |
| Primary condition | reasoning: no counterfactual simulator probes |
| Optional condition | probe: eight counterfactual simulator queries |
| Budget | 480 seconds per item, one scored response |
| Feedback | Practice correctness and examples; scored receipt/status only |
| Tools | Humans: provided interface and blank paper; agents: declared model context, plus common simulator only in probe arm |
| Excluded aids | External code, web, calculators, other AI, repository/key access and outside assistance |

Selecting an explanation is separate from editing an experimental input. Replaying the recorded signal exposes no new counterfactual information and costs no simulator query. Agents receive the same semantic graph, recorded path, labelled switches and alternatives. The optional technical drawer exposes the equivalent machine to humans as well. Every original input cell remains selectable, including those skipped by simplified decision trees. Copies of an identical full time/channel label share one cell identity; the same channel at different moments is distinct. Earlier output indicators may change; the designated target moment alone determines the event. All successful terminal routes join the same target lamp, including routes absent from the recording. The output-only terminal display is included in the common public task; its reduction never changes earlier routing or the intervention domain.

Both interfaces use the same imported machine/trace/target package and session service. The package compiler is separate from the optional dataset constructor. The runtime grades directly without stored answer keys or enumerated answer families. Structured AI observations and a visual human interface have information parity; equal perceptual effort or token cost is not established. Register the modality and measure display burden in the pilot.

The defaults above are study settings, not software limits. Prespecify any changes to time, probes, forms, or instruction material; apply them to both populations being compared. Log the actual session limits and bind them in schema-v2 registration. Keep one scored response. Do not change a participant's budget after seeing performance.

The task asks for one answer, not the complete family or its union. A selected zero refers to its recorded zero value. Prevention can change some or all selected cells; flipping every selected cell is not required.

## Administrative record before recruitment

The responsible investigator supplies institution, determination/approval/exemption identifier and date, research/rights contacts, adult recruitment population, compensation and withdrawal treatment, data retention/access/release conditions, and deletion deadline. The participant materials retain explicit incomplete fields until these are supplied. Consent/contact/payment records stay separate from puzzle logs.

Recruit consenting adults under the completed institutional procedure. Do not collect identifying or demographic fields without a prespecified purpose and applicable permission. A convenience sample supports claims about that sample.

## Pilot and comprehension

Use 6–10 adults on pilot items only. Measure understanding of both quantifiers and inclusion-minimality, time burden, navigation, keyboard/accessibility behavior, and technical reliability. Use the shared five-board visual curriculum (direct route, both switches, alternative route, linked switches, extra marks) before timing. It includes every visible completion of those small demonstrations and preserves the OR/AND/XOR distinctions. The general game also needs explicit pilot checks for changing intermediate outputs, a single fixed target, linked copies with identical full labels, and the complete input inventory. Test whether participants understand the goal by watching and acting, without needing the technical drawer. Record help requests and whether they can trace unseen routes without simulator queries. Record clarifications without screening people based on accuracy.

Revisions must apply to both human and agent materials. Version changed wording, timing, data and scoring, then repeat affected checks. Pilot participants do not enter the main sample. Pilot accuracy is descriptive, not a confirmatory human–AI contrast.

## Assignment and session

The default shared panel has 16 four-item forms, eight items per structural sampling stratum. Each participant receives two common practice items and four scored items, with no repeated test item. Imported packages may have different form lengths or no designated practice items; specify and pilot the intended sequence before recruitment. Assign forms and rotations by a saved randomized schedule. Exact position balance requires coverage divisible by the form length; otherwise position counts differ by at most one. Assign the optional probe condition between participants.

A session includes the completed information/consent step, the shared untimed visual demonstrations, practice, scored items with breaks between them, and debrief. Both modalities retain the same demonstrations, a solved practice example and personal feedback, including a correct submitted alternative. Practice feedback is not an exhaustive list of answers. Practice failures may reveal a counterexample route; scored failures do not. For a removable mark, a pair of displayed executions can illustrate the same target with either value. The pair is explicitly an illustration, not proof of a universal guarantee or of global irrelevance; the exact grader verifies both obligations after removal. Both modalities receive the same practice evidence. The configured clock continues once an item starts. No unscripted solution hints or extra time. The default two-practice/four-scored sequence allows up to 48 minutes of timed items, plus instruction and breaks; actual burden must be measured in the pilot and stated in participant materials.

## Sample, stopping and missingness

Eight independent human judgments per panel item requires 128 usable participants per condition. This is a coverage target, not a power guarantee. Register the actual sample and reserve cap, precision rationale, recruitment deadline, replacement rules, and insufficient-coverage handling before inspecting main outcomes.

Do not recruit until a favorable contrast appears. Keep incomplete eligible sessions according to the registered rule. Poor performance is not an exclusion. Models default to five isolated repetitions per item; repetition is not a new benchmark item or automatically an independent draw from a population of models.

Technical failures and withdrawal can create outcome-dependent missingness. Statistical code cannot repair that assumption. Record the actual disposition and report a restricted descriptive estimate or unavailable full-panel result when coverage/eligibility fails.

## Outcomes

Exact accuracy is 1 for any valid inclusion-minimal answer and 0 for incorrect, nonminimal, malformed, late, or timed-out answers. An empty ordinary answer is incorrect. Only a separately typed no-answer verdict addresses nonexistence.

Secondary diagnostics distinguish guarantee failure, prevention failure, and valid-but-nonminimal answers. These can overlap for validity failures. Format-invalid responses and timeouts have separate counts; they are not causal counterexamples. Cell F1 against a single canonical explanation is not a current outcome.

Timeouts are scored wrong, with elapsed time capped at the item limit for capped-time summaries. A verified infrastructure outage preventing an evaluable attempt may be a technical exclusion. Refusal, malformed model output and output truncation are task failures, not outages.

Navigation is recorded separately as descriptive interface activity. Pan, zoom, direct navigation, overview, start and replay events carry a client-reported view and server elapsed time. The client debounces these records and does not delay an answer waiting for telemetry; a final event can be lost or rejected after submission. Counts are not exhaustive physical actions, durations spent reasoning, or evidence of equal interface cost. Navigation neither resets the deadline nor consumes a probe. Report instrumentation failures and do not infer no navigation from missing events.

Withdrawal immediately closes the session, including before the first trial and between trials. Unstarted items do not become timeouts. Retention/deletion of completed outcomes follows the actual participant record.

## Analysis and freeze

Follow REPORTING_PROTOCOL.md. Preserve participant clusters and complete agent run-cohort clusters across forms. Do not gain nominal replication by splitting a single agent run into form-level pieces. Report independent cluster counts and coverage.

Conservative fixed-design concentration bounds require independent clusters and outcome-independent coverage; exploratory bootstrap intervals do not establish nominal coverage. Register the selected confirmatory procedure and assumptions after planning, before main results.

Freeze code/source hashes, dataset/forms, semantic/protocol versions, prompts, returned model identities, settings, primary model comparison, multiplicity policy and exclusions. Record every deviation and whether outcomes had been inspected. Populate the manuscript only from actual locked evidence.

No human-solvability ceiling is imposed on extended agent tasks. Larger finite machines and horizons can be imported, subject to actual computational resources. Compare populations only where matched observations exist; agent performance on unmeasured human ranges does not establish the location of the human limit.
