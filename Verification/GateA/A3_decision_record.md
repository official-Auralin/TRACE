# A3 — HP-Variant Decision Record (governs hp_variant_policy in the instance schema)

**Evidence base:** a3_variants.json (machine-verified on the five gold puzzles) and
A2_definitional_note.md (primary-source reading of Coenen et al. / CORP).

## Findings
1. The original/updated and modified variants **agree on every non-overdetermined
   instance** (P1, P2, P4) and **diverge exactly on overdetermined ones** (P3, P5):
   original/updated returns the singletons; modified returns the joint pair.
   (Verified mechanically; matches mainTB's own analysis.)
2. **CORP implements the modified discipline** (output-resets to actual values,
   toggleable) — see A2_definitional_note.md. mainTB's Def. actual implements
   original/updated over input cells.

## Decisions
| Consumer | Policy | Rationale |
|---|---|---|
| Human game — CREDIT IT (original/updated surface) | ~~`either`~~ **superseded 2026-06-12**: the mode-explicit construction (proposal, ADOPTED) poses CREDIT IT as a *demonstrated decider* — the original/updated object only; extinguishing sets are not a Credit answer *on this surface*, so no dual *acceptance* governs it (`either` is retired with the removed iteration-12 build; git history preserves it). | The original rationale (variant not communicable nonverbally) is dissolved rather than overruled: the demonstration gesture *shows* the variant instead of naming it. Reinforced 2026-06-14 by the **atomization theorem** (mainTB Prop. `atomize`, SMT-proven window ≤ 8): the original/updated object is *always* a single switch here, so the singleton surface loses no expressible answer. |
| Human game — CREDIT·JOINT (modified surface) | **added 2026-06-14**: `modified`, on its own explicitly-declared surface (`TRACE_credit_joint.html`, `build_joint.py`/`verify_joint.py`). The player names a minimal group whose joint flip darkens the bulb, no subgroup sufficing — the modified object, *shown not named*, exactly as CREDIT IT shows original/updated. | Realizes the proposal's anticipated "fourth, optional type." The modified reading returns **not** as dual acceptance (retired) but as a *separate* surface — the play surface for TempoBench-alignment corpora (row below) and, by Prop. `atomize`, the only surface where a genuine multi-cell cause can win. |
| Benchmark corpus targeting TempoBench alignment | `modified` (pending a2_corp_compare on real keys) | CORP's discipline is modified; alignment claims must grade in CORP's own variant. **This reverses mainTB's current default** and requires a paper edit (DONE 2026-06-14: mainTB "Variant policy" + Prop. `atomize` now state this; see A2 note, "Recommended edit"). |
| Benchmark corpus targeting mainTB's credit-assignment argument | `original` | mainTB's argued preference (per-cell credit under symmetric overdetermination); valid as an *independent* benchmark stance, not a TempoBench-equivalence stance. |

**Conflict rule:** any instance whose two variants disagree MUST carry the
`overdetermined` difficulty tag, and corpora MUST declare `hp_variant_policy`
per instance file; CI rejects instances without it. (Schema field exists —
implementation spec §3.)

**Open until A2(ii):** whether TempoBench's shipped per-cell keys equal the
modified-variant union, the original-variant union, or neither, on real artifacts.
