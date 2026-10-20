# TRACE v5 target-display correction

V4 established the general imported Mealy machine/trace/target pipeline, but drew separate bulbs for individual transitions. Its exact terminal trees retained distinctions between next states after the scored event. A participant could therefore reasonably treat a particular glowing bulb as the goal, although the grader tested the shared Boolean output. The screenshot from tutorial item `m-330fb31a90ea48fede1e` exposed this mismatch.

V5 keeps the source machines, traces, targets, cell identities, forms, G/P predicate and all accepted explanations. The native proved constructor adds an output-only reduced terminal display. Earlier rounds retain their full transitions; complete semantic replay retains all outputs and states. Every successful terminal route visibly reaches one shared target lamp; failures reach a separate dark exit. Earlier output indicators are visually distinct from the goal. Both modalities receive the same display projection.

In the reported puzzle the target is `NOT A1 OR A2`. Holding recorded A1=0 guarantees it and changing A1 alone can prevent it; A2 is unnecessary in that explanation. A2 still matters on the alternative A1=1 route. The corrected drawing removes its redundant terminal copy on route 2 while keeping its relevant copy on route 1. Practice feedback illustrates a removable mark with two runs when both preserve the target, without claiming the pair proves universal irrelevance.

Dataset/protocol identifiers are `trace-mealy-v5` and `trace-study-v5`, compiler `trace.mealy-compiler.v2`, display `trace.display.v1`; explanation semantics stay `trace.gp.v2`. Fresh package and session identities prevent mixing old and corrected displays. The complete pre-correction snapshot, screenshot and consistent playtest database backups are in `archive/v4-multiple-targets`; original raw logs remain private and unchanged.

Current checks are recorded in `IMPLEMENTATION_STATUS.md` and source-bound `results/`. No old PASS is substituted for new verification. Human comprehension, enjoyment, live-model results and empirical difficulty remain unmeasured study gates.
