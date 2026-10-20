import TraceReview

namespace TraceReview

/- Finite state is needed for finite certificates, but not uniqueness/locality. -/
structure TotalMealy (S I O : Type) where
  initial : S
  step : S → I → S
  emit : S → I → O

def stateBefore (M : TotalMealy S I O) (input : Nat → I) : Nat → S
  | 0 => M.initial
  | n + 1 => M.step (stateBefore M input n) (input n)

def outputAt (M : TotalMealy S I O) (input : Nat → I) (n : Nat) : O :=
  M.emit (stateBefore M input n) (input n)

/-- A state sequence satisfying the recurrence is the generated one. -/
theorem mealy_state_unique (M : TotalMealy S I O) (input : Nat → I)
    (states : Nat → S) (hzero : states 0 = M.initial)
    (hstep : ∀ n, states (n + 1) = M.step (states n) (input n)) :
    ∀ n, states n = stateBefore M input n := by
  intro n
  induction n with
  | zero => exact hzero
  | succ n ih => simpa [stateBefore, ih] using hstep n

/-- Output n belongs to round n and uses the pre-round state. -/
theorem mealy_output_unique (M : TotalMealy S I O) (input : Nat → I)
    (states : Nat → S) (outputs : Nat → O)
    (hzero : states 0 = M.initial)
    (hstep : ∀ n, states (n + 1) = M.step (states n) (input n))
    (hemit : ∀ n, outputs n = M.emit (states n) (input n)) :
    ∀ n, outputs n = outputAt M input n := by
  intro n
  rw [hemit n, mealy_state_unique M input states hzero hstep n]
  rfl

/-- State before n depends only on input positions strictly before n. -/
theorem mealy_state_prefix (M : TotalMealy S I O) (a b : Nat → I) (n : Nat)
    (h : ∀ t, t < n → a t = b t) :
    stateBefore M a n = stateBefore M b n := by
  induction n with
  | zero => rfl
  | succ n ih =>
    have hp : ∀ t, t < n → a t = b t := by
      intro t ht
      exact h t (by omega)
    simp only [stateBefore, ih hp, h n (by omega)]

/-- A point output at k is invariant under changes strictly after k. -/
theorem mealy_output_prefix (M : TotalMealy S I O) (a b : Nat → I) (k : Nat)
    (h : ∀ t, t ≤ k → a t = b t) : outputAt M a k = outputAt M b k := by
  unfold outputAt
  rw [mealy_state_prefix M a b k (by intro t ht; exact h t (by omega)), h k (by omega)]

theorem point_effect_prefix (M : TotalMealy S I O) (a b : Nat → I) (k : Nat)
    (effect : O → Prop) (h : ∀ t, t ≤ k → a t = b t) :
    effect (outputAt M a k) ↔ effect (outputAt M b k) := by
  rw [mealy_output_prefix M a b k h]

def InfiniteOften (p : Nat → Prop) : Prop := ∀ n, ∃ t, n ≤ t ∧ p t

theorem infiniteOften_tail (p : Nat → Prop) (hp : InfiniteOften p) :
    InfiniteOften (fun t => p (t + 1)) := by
  intro n
  obtain ⟨t, ht, hpt⟩ := hp (n + 1)
  refine ⟨t - 1, by omega, ?_⟩
  have heq : t - 1 + 1 = t := by omega
  simpa only [heq] using hpt

/-- Worked plant: false = wait, true = serve; output is current state. -/
def waitServe : TotalMealy Bool Bool Bool where
  initial := false
  step s request := if s then false else request
  emit s _ := s

theorem request_has_service (input : Nat → Bool) (t : Nat) (hr : input t = true) :
    outputAt waitServe input t = true ∨ outputAt waitServe input (t + 1) = true := by
  cases hs : stateBefore waitServe input t with
  | false =>
    right
    change waitServe.step (stateBefore waitServe input t) (input t) = true
    rw [hs, hr]
    rfl
  | true =>
    left
    change stateBefore waitServe input t = true
    exact hs

/-- Fairness implies infinitely recurring grants for the frozen strategy. -/
theorem fair_requests_recurring_grants (input : Nat → Bool)
    (fair : InfiniteOften (fun t => input t = true)) :
    InfiniteOften (fun t => outputAt waitServe input t = true) := by
  intro n
  obtain ⟨t, ht, hr⟩ := fair n
  rcases request_has_service input t hr with hg | hg
  · exact ⟨t, ht, hg⟩
  · exact ⟨t + 1, by omega, hg⟩

/-- Skip initial round, then accept all requests; second bit is first-round memory. -/
def skipInitial : TotalMealy (Bool × Bool) Bool Bool where
  initial := (false, true)
  step s request := if s.2 then (false, false)
    else (if s.1 then false else request, false)
  emit s _ := s.1

theorem skip_initial_tail (input : Nat → Bool) :
    ∀ n, stateBefore skipInitial input (n + 1) =
      (stateBefore waitServe (fun t => input (t + 1)) n, false) := by
  intro n
  induction n with
  | zero => rfl
  | succ n ih =>
    change skipInitial.step (stateBefore skipInitial input (n + 1)) (input (n + 1)) =
      (waitServe.step (stateBefore waitServe (fun t => input (t + 1)) n)
        (input (n + 1)), false)
    rw [ih]
    rfl

theorem skip_initial_output_tail (input : Nat → Bool) (n : Nat) :
    outputAt skipInitial input (n + 1) =
      outputAt waitServe (fun t => input (t + 1)) n := by
  change (stateBefore skipInitial input (n + 1)).1 =
    stateBefore waitServe (fun t => input (t + 1)) n
  rw [skip_initial_tail]

/-- This alternative preserves the guarantee against EVERY fair input stream. -/
theorem skip_initial_preserves_recurrence (input : Nat → Bool)
    (fair : InfiniteOften (fun t => input t = true)) :
    InfiniteOften (fun t => outputAt skipInitial input t = true) := by
  have hf := infiniteOften_tail (fun t => input t = true) fair
  have hg := fair_requests_recurring_grants (fun t => input (t + 1)) hf
  intro n
  obtain ⟨t, ht, hgt⟩ := hg n
  refine ⟨t + 1, by omega, ?_⟩
  change outputAt skipInitial input (t + 1) = true
  rw [skip_initial_output_tail]
  exact hgt

/-- A first-round request is skipped, violating 'serve every request'. -/
theorem skip_initial_violates_immediate_service (input : Nat → Bool)
    (request : input 0 = true) :
    stateBefore skipInitial input 0 = (false, true) ∧
    input 0 = true ∧ outputAt skipInitial input 1 = false := by
  exact ⟨rfl, request, rfl⟩

theorem wait_serve_grant_proxy (input : Nat → Bool) (t : Nat) :
    outputAt waitServe input t = stateBefore waitServe input t := rfl

theorem skip_initial_grant_proxy (input : Nat → Bool) (t : Nat) :
    outputAt skipInitial input t = (stateBefore skipInitial input t).1 := rfl


/-- Exact plant legality; a requested service may be accepted or skipped. -/
def serviceMoveLegal (service request next : Bool) : Prop :=
  if service then next = false else if request then True else next = false

theorem frozen_move_legal (service request : Bool) :
    serviceMoveLegal service request (waitServe.step service request) := by
  cases service <;> cases request <;> simp [serviceMoveLegal, waitServe]

theorem skip_initial_move_legal (s : Bool × Bool) (request : Bool) :
    serviceMoveLegal s.1 request (skipInitial.step s request).1 := by
  rcases s with ⟨service, first⟩
  cases service <;> cases first <;> cases request <;> simp [serviceMoveLegal, skipInitial]

def alwaysSkip : TotalMealy Bool Bool Bool where
  initial := false
  step _ _ := false
  emit s _ := s

theorem always_skip_state (input : Nat → Bool) (t : Nat) :
    stateBefore alwaysSkip input t = false := by
  cases t <;> rfl

theorem always_skip_move_legal (s request : Bool) :
    serviceMoveLegal s request (alwaysSkip.step s request) := by
  cases s <;> cases request <;> simp [serviceMoveLegal, alwaysSkip]

/-- Removal feasibility has an explicit fair-input strategy witness. -/
theorem always_skip_removes_recurrence :
    ∃ input : Nat → Bool,
      InfiniteOften (fun t => input t = true) ∧
      ¬ InfiniteOften (fun t => outputAt alwaysSkip input t = true) := by
  refine ⟨fun _ => true, ?_, ?_⟩
  · intro n
    exact ⟨n, Nat.le_refl n, rfl⟩
  · intro h
    obtain ⟨t, _, ht⟩ := h 0
    change stateBefore alwaysSkip (fun _ => true) t = true at ht
    rw [always_skip_state] at ht
    cases ht

theorem no_requests_no_service (t : Nat) :
    stateBefore waitServe (fun _ => false) t = false := by
  induction t with
  | zero => rfl
  | succ n ih =>
    change waitServe.step (stateBefore waitServe (fun _ => false) n) false = false
    rw [ih]
    rfl


end TraceReview
