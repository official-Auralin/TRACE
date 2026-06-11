"""Gate A fixtures.

PUZZLES: the five worked puzzles of mainTB sec. 'Five worked puzzles', encoded as
HOA transducer artifacts (machine-readable, replacing hand simulation). Each entry
carries the EXPECTED answers exactly as published in mainTB; a2_oracle_check.py
fails if the oracle diverges from the paper on any object.

VIOLATIONS: known-bad HOA files for a1_audit.py self-validation. The audit is only
trusted because it classifies every fixture below correctly (positive AND negative
controls)."""

# ---- the five worked puzzles (positive controls; all satisfy F1-operational/F2/F3) ----
P1 = dict(
    name="P1 one pivotal switch (tutorial)",
    hoa="""HOA: v1
States: 2
Start: 0
AP: 2 "btn" "lamp"
controllable-AP: 1
Acceptance: 0 t
--BODY--
State: 0
[!1 & 0] 1
[!1 & !0] 0
State: 1
[1 & 0] 1
[1 & !0] 0
--END--
""",
    inputs=["btn"], out="lamp", k=1, obs=[[1, 0]],
    expect={
        "pivots": [(0, 0)], "no_pivotal_cell": False,
        "credit_original_minimal_causes": [((0, 0),)],
        "credit_union": [(0, 0)],
        "credit_modified_minimal_causes": [((0, 0),)],
        "pin_determining_sets": [((0, 0),)],
    })

P2 = dict(
    name="P2 delayed cause with distractor",
    # done@t = a@(t-2); b read but irrelevant. States encode (a_prev, a_prevprev).
    hoa="""HOA: v1
States: 4
Start: 0
AP: 3 "a" "b" "done"
controllable-AP: 2
Acceptance: 0 t
--BODY--
State: 0
[!2 & 0] 2
[!2 & !0] 0
State: 1
[2 & 0] 2
[2 & !0] 0
State: 2
[!2 & 0] 3
[!2 & !0] 1
State: 3
[2 & 0] 3
[2 & !0] 1
--END--
""",
    # states: 0=(ap=0,app=0) done=0 ; 1=(0,1) done=1 ; 2=(1,0) done=0 ; 3=(1,1) done=1
    inputs=["a", "b"], out="done", k=2, obs=[[1, 0, 0], [0, 1, 0]],
    expect={
        "pivots": [(0, 0)], "no_pivotal_cell": False,
        "credit_original_minimal_causes": [((0, 0),)],
        "credit_union": [(0, 0)],
        "credit_modified_minimal_causes": [((0, 0),)],
        "pin_determining_sets": [((0, 0),)],
    })

P3 = dict(
    name="P3 overdetermination",
    # fire@t = a@(t-1) OR b@(t-1)
    hoa="""HOA: v1
States: 2
Start: 0
AP: 3 "a" "b" "fire"
controllable-AP: 2
Acceptance: 0 t
--BODY--
State: 0
[!2 & (0 | 1)] 1
[!2 & !0 & !1] 0
State: 1
[2 & (0 | 1)] 1
[2 & !0 & !1] 0
--END--
""",
    inputs=["a", "b"], out="fire", k=1, obs=[[1, 0], [1, 0]],
    expect={
        "pivots": [], "no_pivotal_cell": True,                       # paper: 'no pivotal cell'
        "credit_original_minimal_causes": [((0, 0),), ((1, 0),)],    # paper: both singletons
        "credit_union": [(0, 0), (1, 0)],
        "credit_modified_minimal_causes": [((0, 0), (1, 0))],        # paper: modified => joint pair
        "pin_determining_sets": [((0, 0),), ((1, 0),)],              # paper: two determining sets
    })

P4 = dict(
    name="P4 guard (request/cancel)",
    # grant@t = req@t AND NOT cancel@t  (same-step Mealy output; k=0)
    hoa="""HOA: v1
States: 1
Start: 0
AP: 3 "req" "cancel" "grant"
controllable-AP: 2
Acceptance: 0 t
--BODY--
State: 0
[2 & 0 & !1] 0
[!2 & (!0 | 1)] 0
--END--
""",
    inputs=["req", "cancel"], out="grant", k=0, obs=[[1], [0]],
    expect={
        "pivots": [(0, 0), (1, 0)], "no_pivotal_cell": False,        # paper: two pivots
        "credit_original_minimal_causes": [((0, 0),), ((1, 0),)],    # paper: both singletons
        "credit_union": [(0, 0), (1, 0)],
        "credit_modified_minimal_causes": [((0, 0),), ((1, 0),)],    # each flip alone kills
        "pin_determining_sets": [((0, 0), (1, 0))],                  # paper: lock BOTH
    })

P5 = dict(
    name="P5 delayed overdetermination",
    # fire@t = a@(t-2) OR b@(t-1); state=(a_prev, f_next) with f_next = a_pp(next step uses)...
    # encode state bits (x=a_prev, f=a_prevprev OR b_prev): output fire=f; next=(a, x OR b)
    hoa="""HOA: v1
States: 4
Start: 0
AP: 3 "a" "b" "fire"
controllable-AP: 2
Acceptance: 0 t
--BODY--
State: 0
[!2 & 0 & 1] 3
[!2 & 0 & !1] 2
[!2 & !0 & 1] 1
[!2 & !0 & !1] 0
State: 1
[2 & 0 & 1] 3
[2 & 0 & !1] 2
[2 & !0 & 1] 1
[2 & !0 & !1] 0
State: 2
[!2 & 0 & 1] 3
[!2 & 0 & !1] 3
[!2 & !0 & 1] 1
[!2 & !0 & !1] 1
State: 3
[2 & 0 & 1] 3
[2 & 0 & !1] 3
[2 & !0 & 1] 1
[2 & !0 & !1] 1
--END--
""",
    # states: bit0=f (fire now), bit1=x (a_prev): 0=(f0,x0) 1=(f1,x0) 2=(f0,x1) 3=(f1,x1)
    # next state: f' = x OR b ; x' = a
    inputs=["a", "b"], out="fire", k=2, obs=[[1, 0, 0], [0, 1, 0]],
    expect={
        "pivots": [], "no_pivotal_cell": True,                       # paper: no pivotal cell
        "credit_original_minimal_causes": [((0, 0),), ((1, 1),)],    # paper: {(0,a)},{(1,b)}
        "credit_union": [(0, 0), (1, 1)],
        "credit_modified_minimal_causes": [((0, 0), (1, 1))],
        "pin_determining_sets": [((0, 0),), ((1, 1),)],              # paper: two determining sets
    })

PUZZLES = [P1, P2, P3, P4, P5]

# ---- violation fixtures (negative controls for the F1-F3 audit) ----
BAD_F2_OUTPUT = dict(           # two output completions for (q0, btn=1): monitor-like
    name="bad_f2_output_nondet", inputs=["btn"],
    expect_f1=False, expect_f2=False, expect_f3=True,
    hoa="""HOA: v1
States: 1
Start: 0
AP: 2 "btn" "lamp"
controllable-AP: 1
Acceptance: 0 t
--BODY--
State: 0
[0] 0
[!0 & !1] 0
--END--
""")
BAD_F2_STATE = dict(            # same full valuation, two successor states
    name="bad_f2_state_nondet", inputs=["btn"],
    expect_f1=False, expect_f2=False, expect_f3=True,
    hoa="""HOA: v1
States: 2
Start: 0
AP: 2 "btn" "lamp"
controllable-AP: 1
Acceptance: 0 t
--BODY--
State: 0
[0 & !1] 0
[0 & !1] 1
[!0 & !1] 0
State: 1
[!1] 1
--END--
""")
BAD_F3_PARTIAL = dict(          # input btn=0 undefined at q0
    name="bad_f3_partial", inputs=["btn"],
    expect_f1=False, expect_f2=True, expect_f3=False,
    hoa="""HOA: v1
States: 1
Start: 0
AP: 2 "btn" "lamp"
controllable-AP: 1
Acceptance: 0 t
--BODY--
State: 0
[0 & 1] 0
--END--
""")
MONITOR_F1 = dict(              # specification monitor for 'eventually lamp': accepts ALL
    name="monitor_f1_spec_monitor", inputs=["btn"],
    expect_f1=False, expect_f2=False, expect_f3=True,
    hoa="""HOA: v1
States: 2
Start: 0
AP: 2 "btn" "lamp"
Acceptance: 1 Inf(0)
--BODY--
State: 0
[!1] 0
[1] 1
State: 1
[t] 1
--END--
""")
GOOD_CONTROL = dict(            # P1 reused as a known-good audit control
    name="good_control_p1", inputs=["btn"],
    expect_f1=True, expect_f2=True, expect_f3=True,
    hoa=P1["hoa"])

GOOD_NAMED_LABELS = dict(   # same machine as P1 but with NAME-based labels (TempoBench style)
    name="good_control_named_labels", inputs=["btn"],
    expect_f1=True, expect_f2=True, expect_f3=True,
    hoa="""HOA: v1
States: 2
Start: 0
AP: 2 "btn" "lamp"
controllable-AP: 1
Acceptance: 0 t
--BODY--
State: 0
[!lamp & btn] 1
[!lamp & !btn] 0
State: 1
[lamp & btn] 1
[lamp & !btn] 0
--END--
""")

AUDIT_FIXTURES = [GOOD_CONTROL, GOOD_NAMED_LABELS, BAD_F2_OUTPUT, BAD_F2_STATE, BAD_F3_PARTIAL, MONITOR_F1]
