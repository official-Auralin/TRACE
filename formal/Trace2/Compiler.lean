import Trace2.Certificates

namespace Trace2

/-- A switch is a read of an original input cell, never a fresh input. A leaf
emits a Boolean output and carries the next machine state for one round. -/
inductive SwitchTree (Cell A : Type) where
  | leaf : A → SwitchTree Cell A
  | switch : Cell → SwitchTree Cell A → SwitchTree Cell A → SwitchTree Cell A
  deriving DecidableEq

def treeRead {Cell A : Type} (input : Cell → Bool) : SwitchTree Cell A → A
  | .leaf result => result
  | .switch cell zero one => if input cell then treeRead input one else treeRead input zero

/-- Change only the meaning carried by leaves, keeping the input decisions. -/
def mapLeaves {Cell A B : Type} (f : A → B) : SwitchTree Cell A → SwitchTree Cell B
  | .leaf result => .leaf (f result)
  | .switch cell zero one => .switch cell (mapLeaves f zero) (mapLeaves f one)

theorem mapLeaves_correct {Cell A B : Type} (f : A → B)
    (tree : SwitchTree Cell A) (input : Cell → Bool) :
    treeRead input (mapLeaves f tree) = f (treeRead input tree) := by
  induction tree with
  | leaf result => rfl
  | switch cell zero one hz ho =>
    cases hc : input cell <;> simp [mapLeaves, treeRead, hc, hz, ho]

/-- Equality reduction changes only routing, never the available cell set. -/
def simplifyTree {Cell A : Type} [DecidableEq Cell] [DecidableEq A] :
    SwitchTree Cell A → SwitchTree Cell A
  | .leaf result => .leaf result
  | .switch cell zero one =>
    let z := simplifyTree zero
    let o := simplifyTree one
    if z = o then z else .switch cell z o

theorem simplifyTree_correct {Cell A : Type} [DecidableEq Cell] [DecidableEq A]
    (tree : SwitchTree Cell A) (input : Cell → Bool) :
    treeRead input (simplifyTree tree) = treeRead input tree := by
  induction tree with
  | leaf result => rfl
  | switch cell zero one hz ho =>
    simp only [simplifyTree]
    split
    · rename_i he
      cases hc : input cell <;> simp only [treeRead, hc, Bool.false_eq_true, ↓reduceIte]
      · exact hz
      · rw [he]
        exact ho
    · simp only [treeRead, hz, ho]

/-- At the terminal display only the output determines success. The successor
state is retained in the semantic tree, but deliberately absent here. -/
def terminalDisplay {Cell S : Type} [DecidableEq Cell]
    (tree : SwitchTree Cell (S × Bool)) : SwitchTree Cell Bool :=
  simplifyTree (mapLeaves Prod.snd tree)

theorem terminalDisplay_correct {Cell S : Type} [DecidableEq Cell]
    (tree : SwitchTree Cell (S × Bool)) (input : Cell → Bool) :
    treeRead input (terminalDisplay tree) = (treeRead input tree).2 := by
  rw [terminalDisplay, simplifyTree_correct, mapLeaves_correct]

/-- The executable, total constructor. Branching reads channels in ascending
order; the subtrees share the same original cell identifiers. -/
def compileBits {Cell A : Type} : (m : Nat) → (Fin m → Cell) →
    (Valuation m → A) → SwitchTree Cell A
  | 0, _, action => .leaf (action (fun i => Fin.elim0 i))
  | m+1, cells, action => .switch (cells 0)
      (compileBits m (fun r => cells r.succ) (fun tail => action (Fin.cases false tail)))
      (compileBits m (fun r => cells r.succ) (fun tail => action (Fin.cases true tail)))

theorem compileBits_correct {Cell A : Type} (m : Nat) (cells : Fin m → Cell)
    (action : Valuation m → A) (input : Cell → Bool) :
    treeRead input (compileBits m cells action) = action (fun r => input (cells r)) := by
  induction m with
  | zero =>
    simp only [compileBits, treeRead]
    congr 1
    funext r
    exact Fin.elim0 r
  | succ m ih =>
    simp only [compileBits, treeRead]
    cases hb : input (cells 0) <;> simp only [Bool.false_eq_true, ↓reduceIte, ih]
    all_goals
      congr 1
      funext r
      exact Fin.cases (by simp [hb]) (fun _ => rfl) r

/-- Public cell IDs are exactly time * number of inputs + channel. -/
def compileRound {S : Type} {m : Nat} (M : Machine S (Valuation m))
    (time : Nat) (q : S) : SwitchTree Nat (S × Bool) :=
  compileBits m (fun r => time*m+r.val) (fun v => (M.step q v, M.emit q v))

def flatInput {m : Nat} (input : Nat → Valuation m) (cell : Nat) : Bool :=
  if hm : 0 < m then input (cell / m) ⟨cell % m, Nat.mod_lt _ hm⟩ else false

theorem flatInput_cell {m : Nat} (input : Nat → Valuation m) (time : Nat) (r : Fin m) :
    flatInput input (time*m+r.val) = input time r := by
  have hm : 0 < m := by have := r.isLt; omega
  simp only [flatInput, dif_pos hm]
  have hd : (time*m+r.val) / m = time := by
    rw [Nat.mul_comm time m, Nat.mul_add_div hm]
    simp [Nat.div_eq_of_lt r.isLt]
  have hr : (time*m+r.val) % m = r.val := by
    simp [Nat.add_mod, Nat.mod_eq_of_lt r.isLt]
  simp only [hd]
  congr 1
  exact Fin.ext hr

theorem cellId_injective {m : Nat} (t u : Nat) (r s : Fin m)
    (same : t*m+r.val = u*m+s.val) : t = u ∧ r = s := by
  have hm : 0 < m := by have := r.isLt; omega
  have hr := r.isLt
  have hs := s.isLt
  have ht : t = u := by
    have hd := congrArg (fun x => x / m) same
    dsimp at hd
    rw [Nat.mul_comm t m, Nat.mul_comm u m, Nat.mul_add_div hm,
      Nat.mul_add_div hm, Nat.div_eq_of_lt hr, Nat.div_eq_of_lt hs] at hd
    simpa using hd
  refine ⟨ht, Fin.ext ?_⟩
  subst u
  exact Nat.add_left_cancel same

theorem compileRound_correct {S : Type} {m : Nat} (M : Machine S (Valuation m))
    (time : Nat) (q : S) (input : Nat → Valuation m) :
    treeRead (flatInput input) (compileRound M time q) =
      (M.step q (input time), M.emit q (input time)) := by
  rw [compileRound, compileBits_correct]
  have h : (fun r : Fin m => flatInput input (time*m+r.val)) = input time := by
    funext r
    exact flatInput_cell input time r
  rw [h]

def compileRoundReduced {S : Type} [DecidableEq S] {m : Nat}
    (M : Machine S (Valuation m)) (time : Nat) (q : S) : SwitchTree Nat (S × Bool) :=
  simplifyTree (compileRound M time q)

theorem compileRoundReduced_correct {S : Type} [DecidableEq S] {m : Nat}
    (M : Machine S (Valuation m)) (time : Nat) (q : S) (input : Nat → Valuation m) :
    treeRead (flatInput input) (compileRoundReduced M time q) =
      (M.step q (input time), M.emit q (input time)) := by
  rw [compileRoundReduced, simplifyTree_correct, compileRound_correct]

/-- This is emitted only for the designated final display; earlier trees keep
both transition components because next state controls later outputs. -/
def compileTerminal {S : Type} [DecidableEq S] {m : Nat}
    (M : Machine S (Valuation m)) (time : Nat) (q : S) : SwitchTree Nat Bool :=
  terminalDisplay (compileRoundReduced M time q)

theorem compileTerminal_correct {S : Type} [DecidableEq S] {m : Nat}
    (M : Machine S (Valuation m)) (time : Nat) (q : S) (input : Nat → Valuation m) :
    treeRead (flatInput input) (compileTerminal M time q) = M.emit q (input time) := by
  rw [compileTerminal, terminalDisplay_correct, compileRoundReduced_correct]

/-- Complete state replay belongs to the unchanged semantic trees, including
the state reached after the target output. It is not read from the display. -/
def levelState {S : Type} {m : Nat} (rounds : Nat → S → SwitchTree Nat (S × Bool))
    (initial : S) (input : Nat → Valuation m) : Nat → S
  | 0 => initial
  | n+1 => (treeRead (flatInput input) (rounds n (levelState rounds initial input n))).1

theorem compile_reduced_states {S : Type} [DecidableEq S] {m : Nat}
    (M : Machine S (Valuation m)) (input : Nat → Valuation m) (n : Nat) :
    levelState (compileRoundReduced M) M.initial input n =
      TraceReview.stateBefore M input n := by
  induction n with
  | zero => rfl
  | succ n ih => simp only [levelState, compileRoundReduced_correct, ih, TraceReview.stateBefore]

/-- A display follows the full semantic successor until the target round, where
it evaluates the output-only terminal tree. -/
def displayOutput {S : Type} {m : Nat}
    (rounds : Nat → S → SwitchTree Nat (S × Bool))
    (terminal : Nat → S → SwitchTree Nat Bool)
    (input : Nat → Valuation m) (time : Nat) : Nat → S → Bool
  | 0, q => treeRead (flatInput input) (terminal time q)
  | depth+1, q => displayOutput rounds terminal input (time+1) depth
      (treeRead (flatInput input) (rounds time q)).1

theorem displayOutput_before_target {S : Type} {m : Nat}
    (rounds : Nat → S → SwitchTree Nat (S × Bool))
    (terminal : Nat → S → SwitchTree Nat Bool) (input : Nat → Valuation m)
    (time depth : Nat) (q : S) :
    displayOutput rounds terminal input time (depth+1) q =
      displayOutput rounds terminal input (time+1) depth
        (treeRead (flatInput input) (rounds time q)).1 := by
  rfl

/-- Board evaluation advances one round per leaf, not one round per switch. -/
def levelOutput {S : Type} {m : Nat} (rounds : Nat → S → SwitchTree Nat (S × Bool))
    (input : Nat → Valuation m) (time : Nat) : Nat → S → Bool
  | 0, q => (treeRead (flatInput input) (rounds time q)).2
  | depth+1, q => levelOutput rounds input (time+1) depth
      (treeRead (flatInput input) (rounds time q)).1

theorem compile_outputs {S : Type} {m : Nat} (M : Machine S (Valuation m))
    (input : Nat → Valuation m) (time depth : Nat) (q : S) :
    levelOutput (compileRound M) input time depth q =
      replayOutput M q (fun t => input (time+t)) depth := by
  induction depth generalizing time q with
  | zero => simp [levelOutput, compileRound_correct, replayOutput]
  | succ depth ih =>
    simp only [levelOutput, compileRound_correct, ih, replayOutput, Nat.add_zero]
    congr 1
    funext t
    congr 1
    omega

theorem compile_target {S : Type} {m : Nat} (M : Machine S (Valuation m))
    (input : Nat → Valuation m) (target : Nat) :
    levelOutput (compileRound M) input 0 target M.initial =
      replayOutput M M.initial input target := by
  simpa using compile_outputs M input 0 target M.initial

theorem compile_reduced_outputs {S : Type} [DecidableEq S] {m : Nat}
    (M : Machine S (Valuation m)) (input : Nat → Valuation m)
    (time depth : Nat) (q : S) :
    levelOutput (compileRoundReduced M) input time depth q =
      replayOutput M q (fun t => input (time+t)) depth := by
  induction depth generalizing time q with
  | zero => simp [levelOutput, compileRoundReduced_correct, replayOutput]
  | succ depth ih =>
    simp only [levelOutput, compileRoundReduced_correct, ih, replayOutput, Nat.add_zero]
    congr 1
    funext t
    congr 1
    omega

theorem compile_reduced_target {S : Type} [DecidableEq S] {m : Nat}
    (M : Machine S (Valuation m)) (input : Nat → Valuation m) (target : Nat) :
    levelOutput (compileRoundReduced M) input 0 target M.initial =
      replayOutput M M.initial input target := by
  simpa using compile_reduced_outputs M input 0 target M.initial

theorem compile_display_outputs {S : Type} [DecidableEq S] {m : Nat}
    (M : Machine S (Valuation m)) (input : Nat → Valuation m)
    (time depth : Nat) (q : S) :
    displayOutput (compileRoundReduced M) (compileTerminal M) input time depth q =
      replayOutput M q (fun t => input (time+t)) depth := by
  induction depth generalizing time q with
  | zero => simp [displayOutput, compileTerminal_correct, replayOutput]
  | succ depth ih =>
    simp only [displayOutput, compileRoundReduced_correct, ih, replayOutput, Nat.add_zero]
    congr 1
    funext t
    congr 1
    omega

theorem compile_display_target {S : Type} [DecidableEq S] {m : Nat}
    (M : Machine S (Valuation m)) (input : Nat → Valuation m) (target : Nat) :
    displayOutput (compileRoundReduced M) (compileTerminal M) input 0 target M.initial =
      replayOutput M M.initial input target := by
  simpa using compile_display_outputs M input 0 target M.initial

theorem compile_display_combined {S : Type} [DecidableEq S] (target m : Nat)
    (M : Machine S (Valuation m)) (actual : Nat → Valuation m)
    (C : Mask (WindowCell target m)) :
    Combined (windowValue target m) actual
      (fun input => displayOutput (compileRoundReduced M) (compileTerminal M)
        input 0 target M.initial = true) C ↔
    Combined (windowValue target m) actual
      (fun input => replayOutput M M.initial input target = true) C := by
  simp only [compile_display_target]

theorem compile_display_minimal_explanations {S : Type} [DecidableEq S] (target m : Nat)
    (M : Machine S (Valuation m)) (actual : Nat → Valuation m)
    (C : Mask (WindowCell target m)) :
    InclusionMinimal (Combined (windowValue target m) actual
      (fun input => displayOutput (compileRoundReduced M) (compileTerminal M)
        input 0 target M.initial = true)) C ↔
    InclusionMinimal (Combined (windowValue target m) actual
      (fun input => replayOutput M M.initial input target = true)) C := by
  simp only [compile_display_target]

theorem compile_combined {S : Type} (target m : Nat) (M : Machine S (Valuation m))
    (actual : Nat → Valuation m) (C : Mask (WindowCell target m)) :
    Combined (windowValue target m) actual
      (fun input => levelOutput (compileRound M) input 0 target M.initial = true) C ↔
    Combined (windowValue target m) actual
      (fun input => replayOutput M M.initial input target = true) C := by
  simp only [compile_target]

theorem compile_minimal_explanations {S : Type} (target m : Nat)
    (M : Machine S (Valuation m)) (actual : Nat → Valuation m)
    (C : Mask (WindowCell target m)) :
    InclusionMinimal (Combined (windowValue target m) actual
      (fun input => levelOutput (compileRound M) input 0 target M.initial = true)) C ↔
    InclusionMinimal (Combined (windowValue target m) actual
      (fun input => replayOutput M M.initial input target = true)) C := by
  simp only [compile_target]

theorem compile_reduced_minimal_explanations {S : Type} [DecidableEq S] (target m : Nat)
    (M : Machine S (Valuation m)) (actual : Nat → Valuation m)
    (C : Mask (WindowCell target m)) :
    InclusionMinimal (Combined (windowValue target m) actual
      (fun input => levelOutput (compileRoundReduced M) input 0 target M.initial = true)) C ↔
    InclusionMinimal (Combined (windowValue target m) actual
      (fun input => replayOutput M M.initial input target = true)) C := by
  simp only [compile_reduced_target]

end Trace2
