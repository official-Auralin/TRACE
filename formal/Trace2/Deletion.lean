import Trace2.Semantics

namespace Trace2
universe u

/-- One pass over a finite cell inventory. Decidability is supplied by the
executable Bad oracle; no choice of a minimum-cardinality answer is claimed. -/
def prune {Cell : Type u} [DecidableEq Cell] (H : Mask Cell → Prop)
    [DecidablePred H] : List Cell → Mask Cell → Mask Cell
  | [], C => C
  | c :: rest, C => prune H rest (if H (erase C c) then erase C c else C)

/-- Structural recursion on `order` is the termination measure. -/
theorem prune_nil {Cell : Type u} [DecidableEq Cell] (H : Mask Cell → Prop)
    [DecidablePred H] (C : Mask Cell) : prune H [] C = C := rfl

theorem prune_included {Cell : Type u} [DecidableEq Cell] (H : Mask Cell → Prop)
    [DecidablePred H] (order : List Cell) (C : Mask Cell) :
    Included (prune H order C) C := by
  induction order generalizing C with
  | nil => exact included_refl C
  | cons c rest ih =>
    simp only [prune]
    split
    · exact included_trans (ih (erase C c)) (erase_included C c)
    · exact ih C

theorem prune_valid {Cell : Type u} [DecidableEq Cell] (H : Mask Cell → Prop)
    [DecidablePred H] (order : List Cell) (C : Mask Cell) (hc : H C) :
    H (prune H order C) := by
  induction order generalizing C with
  | nil => exact hc
  | cons c rest ih =>
    simp only [prune]
    split
    · rename_i he; exact ih (erase C c) he
    · exact ih C hc

theorem prune_protects_visited {Cell : Type u} [DecidableEq Cell]
    (H : Mask Cell → Prop) [DecidablePred H] (up : Upward H)
    (order : List Cell) (C : Mask Cell) :
    ∀ c, c ∈ order → prune H order C c = true →
      ¬ H (erase (prune H order C) c) := by
  induction order generalizing C with
  | nil => simp
  | cons first rest ih =>
    intro c hmem
    simp only [prune]
    split
    · rename_i he
      intro hp
      rcases List.mem_cons.mp hmem with hfirst | hrest
      · subst c
        have hf := prune_included H rest (erase C first) first hp
        simp [erase] at hf
      · exact ih (erase C first) c hrest hp
    · rename_i he
      intro hp
      rcases List.mem_cons.mp hmem with hfirst | hrest
      · subst c
        intro hbad
        exact he (up _ _ (erase_monotone (prune_included H rest C) first) hbad)
      · exact ih C c hrest hp

theorem prune_minimal {Cell : Type u} [DecidableEq Cell]
    (H : Mask Cell → Prop) [DecidablePred H] (up : Upward H)
    (order : List Cell) (complete : ∀ c, c ∈ order)
    (C : Mask Cell) (hc : H C) :
    InclusionMinimal H (prune H order C) := by
  rw [minimal_iff_single_deletions H up]
  exact ⟨prune_valid H order C hc,
    fun c => prune_protects_visited H up order C c (complete c)⟩

/-- The loop performs one candidate-deletion decision per inventory entry. -/
def pruneChecks {Cell : Type u} (order : List Cell) : Nat :=
  match order with
  | [] => 0
  | _ :: rest => 1 + pruneChecks rest

theorem prune_checks_eq_length {Cell : Type u} (order : List Cell) :
    pruneChecks order = order.length := by
  induction order with
  | nil => rfl
  | cons c rest ih => simp [pruneChecks, ih, Nat.add_comm]

end Trace2
