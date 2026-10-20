# TRACE algorithm specification — general compiler v5, G/P semantics v2

## Supported problem

An instance contains a finite, total deterministic Mealy machine M=(Q,q0,Σ,δ,λ), Boolean input channels, an observed input word a of length h>0, and target step k=h−1. The effect is output 1 at step k, and must hold on a. The output at a step is emitted from the old state and current inputs, before the state update. A cell d=t*m+r names the observed value a[t][r], including zero. Every Boolean input word through k is admissible. The candidate language is every subset of these cells D. The admissibility domain is fixed independently of the candidate.

The task permits arbitrary positive finite state/channel counts and a finite target prefix. Import validates any supplied suffix before compiling only the target prefix. Runtime/resource budgets are separate from mathematical validity. The generic theorems have no fixed small dimension cap. All-answer enumeration is an explicit small-instance audit, never required for compilation or grading.

## Exact causal contract

G(C): every word agreeing with a on C produces the target.

P(C): some word agreeing with a outside C fails to produce the target.

H(C)=G(C) AND P(C). An answer is any inclusion-minimal H-valid C. It is not minimum-cardinality, a complete family, or a union.

P is existential over changes confined to C. It does not require changing every selected cell. XOR at actual (1,0) is a required regression: the minimal combined explanation is both cells, although flipping both preserves the output.

The normal answer is {"cells":[unique integer IDs]}. The separate answer {"verdict":"no_explanation"} is correct exactly when no H-valid candidate exists. An empty cell list is not a synonym for this verdict. Malformed instances and false actual effects are rejected before scoring.

## Counterexample query and backward recurrence

Bad(F) means there exists a target-defeating input word that fixes the recorded values on F. Therefore G(C)=not Bad(C), and P(C)=Bad(D\\C).

Let A_F(t) be the input valuations that agree with a at all fixed cells in round t. With pre-round state q:

- At t=k, R_F(k,q)=OR over u in A_F(k) of [λ(q,u)=0].
- At t<k, R_F(t,q)=OR over u in A_F(t) of R_F(t+1,δ(q,u)).
- Bad(F)=R_F(0,q0).

A proof proceeds by induction on remaining rounds: R_F(t,q) holds exactly when a permitted suffix produces a defeating target transition. Checking terminal output is essential; the final state alone need not determine the target output.

## Explicit verification game

C is fixed before the game. A challenger chooses an obligation:
1. Guarantee: challenger chooses outside C, selected values are fixed, and the explainer wins iff E.
2. Prevention: explainer chooses inside C, outside values are fixed, and the explainer wins iff not E.

Machine transitions are forced. The root is winning exactly when H(C). A successful terminal transition leads to an absorbing priority-0 sink and failure to an absorbing priority-1 sink, under minimum-even acceptance. Every play reaches a sink after a bounded number of rounds, so the parity verdict equals its terminal verdict.

This is a bounded quantifier game. After the branch choice, only one side has meaningful input choices in each branch. It is not the policy-replacement predicate N2 from the reverse-parity review. Temporal execution goes forward; the winning calculation proceeds backward.

## Minimality and search

Fixing more cells cannot create a defeating completion. Consequently G and P are both upward-closed in C, even for nonmonotone output functions.

For H(C), inclusion-minimality is equivalent to failure of H(C\\{c}) for every c in C. If a proper subset were valid, some single deletion containing that subset would be valid by upward closure.

Start with C=D. If H(D) fails, report no explanation. Otherwise consider every cell once, deleting it whenever H remains true. A failed deletion cannot become successful after later deletions, by upward closure. The procedure terminates after at most |D| deletion decisions and returns an inclusion-minimal explanation. Different orders may return different answers or sizes. Grading checks validity and deletion minimality, not equality with the particular answer produced by one order.

A query visits O(h|Q||Σ|) recurrence transitions once permitted valuations are available; one-answer search uses O(|D|h|Q||Σ|) such visits. Python input-fixing filters add O(hm|Σ|) work per query, and concrete adapters also encode and inspect input bits. These are recurrence bounds, not precise wall-clock bounds for every implementation. For m Boolean channels, |Σ|=2^m. These bounds do not describe enumeration of every answer or unrestricted parity games.

## Independent characterization

Let J be the inclusion-minimal supports of target-defeating changes. G(C) iff C intersects every J member; P(C) iff C contains some J member. If T is the family of inclusion-minimal hitting sets of J, then all accepted explanations are the inclusion-minimal members of {t union j : t in T, j in J}.

This provides an independent cross-check, not the definition used to justify the production recurrence. The direct reference oracle evaluates the quantified predicates over complete independently replayed words.

## Evidence contract

A certificate binds the exact public instance and semantic version to locally checkable recurrence labels and replay witnesses. Guarantee requires exclusion of all defeating completions; prevention requires one legal defeating completion. Each deletion must fail at least one obligation. No-answer requires a global exclusion certificate.

A witness alone cannot certify a universal guarantee. Agreement between two implementations cannot replace a correspondence proof. See formal/README.md for exactly which definitions and correspondences are machine checked, and which parser/runtime boundaries remain trusted.

## Required regression classes

Constant true (no answer), false actual effect (invalid instance), empty candidate, OR/AND redundancy, XOR rebound, dummy inputs, multiple explanations, different minimal answer sizes, arbitrary actual polarities, channel renaming, earlier targets, malformed IDs, changed transitions, incorrect certificate labels, nonminimal supersets, and alternative valid submissions.

The full strategy extension additionally requires a supplied arena, legal alternatives, a fixed editable set, baseline policy, candidate grammar, and certified acceptance monitors. It is a separately scoped extension, not a missing hidden dependency of this finite algorithm.

## General visual construction and its checked boundary

The optional source constructor creates machine/trace/target records independently of the game. External records enter exactly the same compiler. The shipped Lean constructor unfolds finite time/state pairs, reads each round's original Boolean input cells in switch trees, emits the source transition output and advances to its next state. Multiple switch decisions inside one round do not advance semantic time. A machine loop becomes a later occurrence of the same state. Outputs do not latch unless the source machine latches them.

`compileRoundReduced` removes equal subtrees using a proved reduction. Every original cell remains selectable even if a decision is irrelevant at some or all states. All appearances of one time/channel input share its identity and recorded value. The general output correspondence theorem covers every word and every finite round; target equality with unchanged intervention/candidate domains preserves every minimal explanation. See formal/PROOF_COVERAGE.md.

The semantic forest retains `(next state, output)` leaves at every round, including the target. A separate mandatory `board.display` (`trace.display.v1`) contains one reduced output-only terminal tree per source state. The Lean executable maps each final leaf `(q,b)` to `b`, then simplifies identical subtrees. For every final state/input valuation the resulting tree returns exactly the original output. Earlier rounds retain full successor-state distinctions. Combining those unchanged rounds with the terminal projection preserves the target under every word, and hence G, P and every inclusion-minimal explanation. It does not preserve the post-target state in the drawing; full semantic replay still does.

All final output-1 routes must visibly join one fixed target lamp and all output-0 routes one distinct dark exit. A gold recorded path identifies an execution, not the identity of the goal. Intermediate outputs are status indicators. Browser rendering, endpoints and animations require separate acceptance checks; this graphical claim is not established by the kernel theorem.

Python checks each compiled decision tree against every source transition, including unobserved alternatives, and independently checks the canonical terminal projection and all its outputs. This is a local transition check, not exponential complete-word enumeration. Small independent word and candidate audits supplement the theorem. The serialized forest, parser, native runtime, renderer, UI and Python grader remain explicit tested/trusted boundaries.

Default certification streams canonical answer evidence through both checkers. Detailed tables and witnesses are persisted only on request. This does not weaken universal guarantee checking. The Lean checker uses proved sparse query lookup and complete local recurrence equations; it no longer reruns an exponential recursive oracle. The Python decision path retains two state rows per query and caches Boolean roots, not all recurrence tables.

Practice supplies one valid example plus submitted-answer diagnostics and legal witnesses. It does not enumerate all explanations. Tiny fixed teaching boards can enumerate their few settings. A witness demonstrates an existential statement; universal statements still require the exact backward decision.

## Public demo execution boundary

`trace.demo.v1` uses the same compiled public machine/trace/target and terminal display. Its JavaScript grader implements the Bad(F) recurrence and deletion test directly; it does not use precomputed answer keys or exhaustive word/answer enumeration. The JavaScript implementation is checked against Python and independent bounded fixtures, but is not itself covered by a new kernel theorem. Normal submission returns obligation diagnostics; a canonical example is computed only on explicit solution disclosure. Browser-local scores and progress are editable and have no claim of research authenticity. None of these presentation/session changes changes G, P, the candidate domain, or minimality.
