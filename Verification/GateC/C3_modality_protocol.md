# Modality-Confound Protocol (for the human pilot and agent baselines)

**The confound (mainTB's own caveat).** "The human reads a moving board; the agent
reads JSON... spatial-versus-textual encoding could itself shift the measured
human–agent gap, so a careful study should control for it."

**Design: 2×2 within the white-box track, same instances throughout.**
| | Spatial (board) | Textual (JSON/HOA) |
|---|---|---|
| Human | H-board (default play) | H-json: humans receive the agent observation, answer in the JSON format |
| Agent | A-board: agents receive a rendered board image (same SVG the human sees) | A-json (default benchmark) |

- Identical instance set across the four arms, drawn from calibrated strata;
  identical witness grading (single grader); identical attempt budget.
- Primary contrast: (H-board − A-json) decomposed via the off-diagonal arms into
  a modality component and a residual reasoning component.
- Materials: `c3_materials.py` emits, for every level of the playable build, the
  agent observation JSON (machine + run + target + window + budgets, no key) and
  the board SVG, both derived from the same instance object and covered by the
  parity audit (c1) — so any arm difference is presentation, machine-checked to
  carry no information difference.
- Black-box arms are out of scope here (identification is bundled with reasoning
  there by design; see the admission-check results).
