import Mealy

namespace Trace2
universe u v

abbrev Machine (S : Type) (I : Type) := TraceReview.TotalMealy S I Bool

/-- `depth` is the number of transitions strictly before the target transition. -/
def BadFrom {S : Type} {I : Type} (M : Machine S I)
    (allowed : Nat → I → Bool) (time : Nat) : Nat → S → Prop
  | 0, q => ∃ i, allowed time i = true ∧ M.emit q i = false
  | depth + 1, q => ∃ i, allowed time i = true ∧
      BadFrom M allowed (time + 1) depth (M.step q i)

/-- Executable finite existential reachability, with a complete input alphabet. -/
def badEval {S : Type} {I : Type} (M : Machine S I) (letters : List I)
    (allowed : Nat → I → Bool) (time : Nat) : Nat → S → Bool
  | 0, q => letters.any (fun i => allowed time i && !(M.emit q i))
  | depth + 1, q => letters.any (fun i => allowed time i &&
      badEval M letters allowed (time + 1) depth (M.step q i))

theorem badEval_iff {S : Type} {I : Type} (M : Machine S I) (letters : List I)
    (complete : ∀ i, i ∈ letters) (allowed : Nat → I → Bool)
    (time depth : Nat) (q : S) :
    badEval M letters allowed time depth q = true ↔ BadFrom M allowed time depth q := by
  induction depth generalizing time q with
  | zero =>
    simp only [badEval, BadFrom, List.any_eq_true, Bool.and_eq_true]
    constructor
    · rintro ⟨i,_,ha,hb⟩
      exact ⟨i,ha,by cases he : M.emit q i <;> simp_all⟩
    · rintro ⟨i,ha,hb⟩; exact ⟨i,complete i,ha,by simp [hb]⟩
  | succ depth ih =>
    simp only [badEval, BadFrom, List.any_eq_true, Bool.and_eq_true]
    constructor
    · rintro ⟨i,_,ha,hb⟩; exact ⟨i,ha,(ih _ _).mp hb⟩
    · rintro ⟨i,ha,hb⟩; exact ⟨i,complete i,ha,(ih _ _).mpr hb⟩

/-- Replay from an explicit state, using the output of the target transition. -/
def replayOutput {S : Type} {I : Type} (M : Machine S I)
    (q : S) (input : Nat → I) : Nat → Bool
  | 0 => M.emit q (input 0)
  | depth + 1 => replayOutput M (M.step q (input 0)) (fun t => input (t + 1)) depth

def Permitted {I : Type} (allowed : Nat → I → Bool)
    (time depth : Nat) (input : Nat → I) : Prop :=
  ∀ j, j ≤ depth → allowed (time + j) (input j) = true

def prepend {I : Type} (i : I) (input : Nat → I) : Nat → I
  | 0 => i
  | j + 1 => input j

theorem permitted_tail {I : Type} (allowed : Nat → I → Bool)
    (time depth : Nat) (input : Nat → I)
    (h : Permitted allowed time (depth + 1) input) :
    Permitted allowed (time + 1) depth (fun j => input (j + 1)) := by
  intro j hj
  have he := h (j + 1) (by omega)
  simpa [Nat.add_assoc, Nat.add_comm, Nat.add_left_comm] using he

theorem permitted_prepend {I : Type} (allowed : Nat → I → Bool)
    (time depth : Nat) (i : I) (input : Nat → I)
    (hi : allowed time i = true) (h : Permitted allowed (time + 1) depth input) :
    Permitted allowed time (depth + 1) (prepend i input) := by
  intro j hj
  cases j with
  | zero => simpa [prepend] using hi
  | succ j =>
    have he := h j (by omega)
    simpa [prepend, Nat.add_assoc, Nat.add_comm, Nat.add_left_comm] using he

theorem badFrom_iff_replay {S : Type} {I : Type} (M : Machine S I)
    (allowed : Nat → I → Bool) (time depth : Nat) (q : S) :
    BadFrom M allowed time depth q ↔
      ∃ input, Permitted allowed time depth input ∧ replayOutput M q input depth = false := by
  induction depth generalizing time q with
  | zero =>
    constructor
    · rintro ⟨i,ha,hb⟩
      refine ⟨fun _ => i,?_,hb⟩
      intro j hj
      have hz : j = 0 := by omega
      subst j
      simpa using ha
    · rintro ⟨input,ha,hb⟩
      exact ⟨input 0, by simpa using ha 0 (Nat.le_refl 0), hb⟩
  | succ depth ih =>
    constructor
    · rintro ⟨i,ha,hb⟩
      obtain ⟨input,hp,ho⟩ := (ih _ _).mp hb
      refine ⟨prepend i input,permitted_prepend allowed time depth i input ha hp,?_⟩
      simpa [replayOutput,prepend] using ho
    · rintro ⟨input,hp,ho⟩
      refine ⟨input 0,?_,(ih _ _).mpr ?_⟩
      · simpa using hp 0 (by omega)
      · exact ⟨fun j => input (j + 1),permitted_tail allowed time depth input hp,ho⟩

/-- Semantic certificate contract used by the Python checker: every state of
 every supplied row satisfies the full backward recurrence. -/
def LocalTable {S : Type} {I : Type} (M : Machine S I) (letters : List I)
    (allowed : Nat → I → Bool) (target : Nat) (table : Nat → S → Bool) : Prop :=
  (∀ q, table target q = letters.any (fun i => allowed target i && !(M.emit q i))) ∧
  (∀ t, t < target → ∀ q, table t q = letters.any
    (fun i => allowed t i && table (t + 1) (M.step q i)))

theorem localTable_exact {S : Type} {I : Type} (M : Machine S I)
    (letters : List I) (allowed : Nat → I → Bool) (target : Nat)
    (table : Nat → S → Bool) (consistent : LocalTable M letters allowed target table)
    (time depth : Nat) (sum : time + depth = target) (q : S) :
    table time q = badEval M letters allowed time depth q := by
  induction depth generalizing time q with
  | zero =>
    have ht : time = target := by omega
    subst time
    exact consistent.1 q
  | succ depth ih =>
    rw [consistent.2 time (by omega) q]
    simp only [badEval]
    apply congrArg (fun f => letters.any f)
    funext i
    rw [ih (time + 1) (by omega) (M.step q i)]

/-- Small executable checker: all states, all rows, including unreachable ones. -/
def checkTable {S : Type} {I : Type} (M : Machine S I)
    (letters : List I) (states : List S) (allowed : Nat → I → Bool)
    (target : Nat) (table : Nat → S → Bool) : Bool :=
  states.all (fun q => table target q == letters.any
    (fun i => allowed target i && !(M.emit q i))) &&
  (List.range target).all (fun t => states.all (fun q => table t q == letters.any
    (fun i => allowed t i && table (t + 1) (M.step q i))))

theorem checkTable_iff {S : Type} {I : Type} (M : Machine S I)
    (letters : List I) (states : List S) (statesComplete : ∀ q, q ∈ states)
    (allowed : Nat → I → Bool) (target : Nat) (table : Nat → S → Bool) :
    checkTable M letters states allowed target table = true ↔
      LocalTable M letters allowed target table := by
  simp only [checkTable, Bool.and_eq_true, List.all_eq_true, beq_iff_eq]
  constructor
  · rintro ⟨ht,hs⟩
    exact ⟨fun q => ht q (statesComplete q),
      fun t h q => hs t (List.mem_range.mpr h) q (statesComplete q)⟩
  · rintro ⟨ht,hs⟩
    exact ⟨fun q _ => ht q,
      fun t h q _ => hs t (List.mem_range.mp h) q⟩

theorem checked_table_replay_iff {S : Type} {I : Type} (M : Machine S I)
    (letters : List I) (lettersComplete : ∀ i, i ∈ letters)
    (states : List S) (statesComplete : ∀ q, q ∈ states)
    (allowed : Nat → I → Bool) (target : Nat) (table : Nat → S → Bool)
    (checked : checkTable M letters states allowed target table = true) :
    table 0 M.initial = true ↔
      ∃ input, Permitted allowed 0 target input ∧
        replayOutput M M.initial input target = false := by
  have consistent := (checkTable_iff M letters states statesComplete allowed target table).mp checked
  rw [localTable_exact M letters allowed target table consistent 0 target (by omega) M.initial]
  exact (badEval_iff M letters lettersComplete allowed 0 target M.initial).trans
    (badFrom_iff_replay M allowed 0 target M.initial)

/-- In particular a checked false root proves universal absence, not just failure
of a search to find a witness. -/
theorem checked_false_iff_no_replay {S : Type} {I : Type} (M : Machine S I)
    (letters : List I) (lettersComplete : ∀ i, i ∈ letters)
    (states : List S) (statesComplete : ∀ q, q ∈ states)
    (allowed : Nat → I → Bool) (target : Nat) (table : Nat → S → Bool)
    (checked : checkTable M letters states allowed target table = true) :
    table 0 M.initial = false ↔ ¬ ∃ input, Permitted allowed 0 target input ∧
        replayOutput M M.initial input target = false := by
  have h := checked_table_replay_iff M letters lettersComplete states statesComplete
    allowed target table checked
  cases hb : table 0 M.initial <;> simp_all

/-- Aligns the recursive replay with the vendored pre-transition Mealy semantics. -/
theorem mealy_tail_state {S : Type} {I : Type} (M : Machine S I)
    (input : Nat → I) (n : Nat) :
    TraceReview.stateBefore M input (n + 1) =
      TraceReview.stateBefore { M with initial := M.step M.initial (input 0) }
        (fun t => input (t + 1)) n := by
  induction n with
  | zero => rfl
  | succ n ih =>
    change M.step (TraceReview.stateBefore M input (n + 1)) (input (n + 1)) =
      M.step (TraceReview.stateBefore { M with initial := M.step M.initial (input 0) }
        (fun t => input (t + 1)) n) (input (n + 1))
    rw [ih]

theorem mealy_tail_output {S : Type} {I : Type} (M : Machine S I)
    (input : Nat → I) (n : Nat) :
    TraceReview.outputAt M input (n + 1) =
      TraceReview.outputAt { M with initial := M.step M.initial (input 0) }
        (fun t => input (t + 1)) n := by
  unfold TraceReview.outputAt
  rw [mealy_tail_state]

theorem replayOutput_eq_mealy {S : Type} {I : Type} (M : Machine S I)
    (q : S) (input : Nat → I) (n : Nat) :
    replayOutput M q input n = TraceReview.outputAt { M with initial := q } input n := by
  induction n generalizing q input with
  | zero => rfl
  | succ n ih =>
    rw [replayOutput, ih, mealy_tail_output]

/-- Every well-typed finite instance has a complete locally checkable table. -/
def canonicalTable {S : Type} {I : Type} (M : Machine S I) (letters : List I)
    (allowed : Nat → I → Bool) (target : Nat) : Nat → S → Bool :=
  fun t q => badEval M letters allowed t (target - t) q

theorem canonicalTable_local {S : Type} {I : Type} (M : Machine S I)
    (letters : List I) (allowed : Nat → I → Bool) (target : Nat) :
    LocalTable M letters allowed target (canonicalTable M letters allowed target) := by
  constructor
  · intro q; simp [canonicalTable,badEval]
  · intro t ht q
    have hdepth : target - t = (target - (t + 1)) + 1 := by omega
    simp only [canonicalTable]
    rw [hdepth]
    rfl

theorem canonicalTable_checked {S : Type} {I : Type} (M : Machine S I)
    (letters : List I) (states : List S) (complete : ∀ q, q ∈ states)
    (allowed : Nat → I → Bool) (target : Nat) :
    checkTable M letters states allowed target (canonicalTable M letters allowed target) = true := by
  exact (checkTable_iff M letters states complete allowed target _).mpr
    (canonicalTable_local M letters allowed target)

theorem localTable_unique {S : Type} {I : Type} (M : Machine S I)
    (letters : List I) (allowed : Nat → I → Bool) (target : Nat)
    (first second : Nat → S → Bool)
    (hf : LocalTable M letters allowed target first)
    (hs : LocalTable M letters allowed target second) (time : Nat) (ht : time ≤ target) (q : S) :
    first time q = second time q := by
  rw [localTable_exact M letters allowed target first hf time (target-time) (by omega) q,
    localTable_exact M letters allowed target second hs time (target-time) (by omega) q]

end Trace2
