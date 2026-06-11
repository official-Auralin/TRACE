# A2 (definitional half) — Does CORP's contingency discipline match mainTB's Definition of actual cause?

**Question (mainTB's own TODO, roadmap V2):** "verify against Coenen et al. (ATVA 2022)
whether their contingencies permit non-actual values, and record the answer here."

**Answer: NO — and the mismatch is two-fold.** Primary sources read 2026-06-10:

1. **Coenen et al., "Temporal Causality in Reactive Systems" (ATVA 2022)** — the
   definition CORP implements. Their preliminaries adopt actual causality "originally
   proposed by Halpern and Pearl [16], **in the version modified by Halpern [15]**"
   (i.e., Halpern 2015, the *modified* definition). Their contingency mechanism
   (Def. 4, Contingency Set): the counterfactual trace's outputs are determined by the
   system "together with **'jumps' to the original trace π**" — i.e., outputs may be
   reset **to their values on the actual trace only**. Quote (Sec. 3): "Contingencies
   now allow us to **reset certain parts of the counterfactual trace back to the actual
   trace**."

2. **Finkbeiner, Frenkel, Metzger, Siber, "Synthesis of Temporal Causality" (CAV 2024)
   — the CORP tool paper** (arXiv:2405.10912). Remark 2: the counterfactual automaton
   "models contingencies, which allow to **partially reset outputs back to as they were
   on the actual trace π** ... This mechanism, **inspired by Halpern's modified version
   of actual causality [28]** ... Beutner et al.'s implementation therefore allows to
   **toggle the usage of contingencies**."

**Contrast with mainTB Def. (actual cause):** contingencies are assignments of possibly
**non-actual** values to **input cells** (the original/updated HP variant; mainTB says
so explicitly in "Why this is Halpern–Pearl, and which Halpern–Pearl").

| | mainTB Def. actual | Coenen et al. / CORP |
|---|---|---|
| HP variant | original/updated (HP 2005) | **modified (Halpern 2015)** |
| Contingency variables | **input cells** (exogenous) | **outputs/states** (endogenous) |
| Contingency values | possibly **non-actual** | **actual-trace values only** ("jumps to π") |
| Contingency use | always part of the definition | **toggleable** in implementations |
| Counterfactual inputs | closest by count-only cell flips | closest by similarity relation (≤^subset / ≤^full) with rejection-structure refinement |

**Consequences:**
- **Conjecture corp, as stated, is definitionally unsupported.** mainTB itself proves the
  variants diverge on overdetermined instances ("under the modified definition Puzzle 3's
  cause would be the joint pair"), and a3_variants.py reproduces this divergence
  mechanically (P3, P5). Whether TempoBench's *per-cell flattening* of CORP keys happens
  to equal Γ^ac on benign instances remains an empirical question (a2_corp_compare.py),
  but **symmetric-overdetermination instances are the predicted counterexample class**.
- **Recommended edit to mainTB:** resolve the TODO with the quotes above; either
  (a) re-state Def. actual in the modified variant for the TempoBench-alignment claim,
  or (b) keep original/updated and downgrade Conjecture corp to apply only to
  non-overdetermined strata, with the divergence class published as a feature
  (it is exactly the Credit-vs-modified distinction the game's dual-acceptance handles).
- **The game's dual-acceptance policy (implementation spec §4.2) is vindicated:** the
  modified reading the demo added in iteration 12 is the reading CORP actually uses.

Sources: Coenen et al. ATVA 2022 (https://finkbeiner.groups.cispa.de/publications/CFF+22.pdf);
Finkbeiner et al. CAV 2024 (https://arxiv.org/abs/2405.10912); mainTB.tex ll. 635–668.
Caveat: quotes transcribed from author-hosted/arXiv versions, not versions of record.
