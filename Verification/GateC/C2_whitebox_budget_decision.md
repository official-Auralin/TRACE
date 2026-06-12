# White-Box Probe-Budget Decision Record

**Question.** mainTB budgets the probe/run affordance in both tracks; the playable
build simulates the white-box board live (β effectively unbounded), a deviation
recorded since the routing-ontology iteration. Which is right for each consumer?

**Decision.**
| Consumer | Budget | Rationale |
|---|---|---|
| Human white-box (play + pilot default) | **β = ∞ (live board)** | The device is fully shipped; with junction alignment visible, the route is deducible by eye, so a metered "run" button prices information the player already holds. The scored resources are attempts. |
| Human white-box (calibration arm) | **β finite, board static** | Retained as an experimental arm so the pilot can measure how much the live board helps — this preserves the paper's budgeted-white-box construct rather than amending it away. |
| Human black-box | **β finite (battery)** | Probes are the only information channel; the budget is what makes identification meaningful (and the admission check is computed against it). |
| Agents, both tracks | **β finite, declared per run** | Tool-less vs probe-budgeted vs code-equipped regimes are reported separately per mainTB's tool-regime caveat. |

**Parity note.** β=∞ live simulation for white-box humans does not break information
parity: a white-box agent holds the HOA text and can simulate it at will; the live
board is the same capability in spatial form. The C3 protocol controls for the
*modality* difference this leaves (spatial vs textual), which is presentation, not
information.

**Paper impact.** No mainTB edit until the pilot's two white-box arms are run; the
difficulty-knob table's β row applies to the black-box track and the static
calibration arm.
