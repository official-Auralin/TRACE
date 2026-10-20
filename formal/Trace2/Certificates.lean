import Trace2.Deletion
import Trace2.Binding

namespace Trace2
universe u v

def combinedCheck {Cell : Type u} (oracle : Mask Cell → Bool) (C : Mask Cell) : Bool :=
  !(oracle C) && oracle (complement C)

def minimalCheck {Cell : Type u} [DecidableEq Cell]
    (oracle : Mask Cell → Bool) (order : List Cell) (C : Mask Cell) : Bool :=
  combinedCheck oracle C && order.all
    (fun c => !(C c) || !(combinedCheck oracle (erase C c)))

theorem combinedCheck_iff {Cell : Type u} {World : Type v}
    (value : World → Cell → Bool) (actual : World) (E : World → Prop)
    (oracle : Mask Cell → Bool) (C : Mask Cell)
    (first : oracle C = true ↔ Bad value actual E C)
    (second : oracle (complement C) = true ↔ Bad value actual E (complement C)) :
    combinedCheck oracle C = true ↔ Combined value actual E C := by
  cases hfirst : oracle C <;> cases hsecond : oracle (complement C) <;>
    simp_all [combinedCheck,Combined,Guarantee,Prevention]

/-- Only the submitted candidate and its one-cell deletions need certified query
answers. No unqueried oracle entry is trusted. -/
theorem minimalCheck_iff {Cell : Type u} [DecidableEq Cell]
    (H : Mask Cell → Prop) (up : Upward H) (oracle : Mask Cell → Bool)
    (order : List Cell) (complete : ∀ c, c ∈ order) (C : Mask Cell)
    (candidate : combinedCheck oracle C = true ↔ H C)
    (deletions : ∀ c, C c = true → (combinedCheck oracle (erase C c) = true ↔ H (erase C c))) :
    minimalCheck oracle order C = true ↔ InclusionMinimal H C := by
  rw [minimal_iff_single_deletions H up]
  constructor
  · intro checked
    simp only [minimalCheck, Bool.and_eq_true] at checked
    have both := checked
    refine ⟨candidate.mp both.1,?_⟩
    intro c hc hh
    have hrow := List.all_eq_true.mp both.2 c (complete c)
    have hx := (deletions c hc).mpr hh
    simp [hc,hx] at hrow
  · rintro ⟨hc,hminimal⟩
    simp only [minimalCheck, Bool.and_eq_true]
    refine ⟨candidate.mpr hc,List.all_eq_true.mpr ?_⟩
    intro c _
    cases hcc : C c
    · simp
    · have hn : combinedCheck oracle (erase C c) ≠ true := by
        intro ht; exact hminimal c hcc ((deletions c hcc).mp ht)
      cases hd : combinedCheck oracle (erase C c) <;> simp_all

/-- End-to-end semantic answer check, assuming exactly the roots of the locally
checked tables needed for this answer. -/
theorem minimalCheck_combined_iff {Cell : Type u} {World : Type v}
    [DecidableEq Cell] (value : World → Cell → Bool) (actual : World) (E : World → Prop)
    (oracle : Mask Cell → Bool) (order : List Cell) (complete : ∀ c, c ∈ order)
    (C : Mask Cell)
    (candidateG : oracle C = true ↔ Bad value actual E C)
    (candidateP : oracle (complement C) = true ↔ Bad value actual E (complement C))
    (deletionG : ∀ c, C c = true →
      (oracle (erase C c) = true ↔ Bad value actual E (erase C c)))
    (deletionP : ∀ c, C c = true →
      (oracle (complement (erase C c)) = true ↔ Bad value actual E (complement (erase C c)))) :
    minimalCheck oracle order C = true ↔ InclusionMinimal (Combined value actual E) C := by
  apply minimalCheck_iff _ (combined_upward value actual E) oracle order complete C
  · exact combinedCheck_iff value actual E oracle C candidateG candidateP
  · intro c hc
    exact combinedCheck_iff value actual E oracle (erase C c)
      (deletionG c hc) (deletionP c hc)

/-- The empty fixing query is the global defeat query. -/
theorem empty_bad_iff_failure {Cell : Type u} {World : Type v}
    (value : World → Cell → Bool) (actual : World) (E : World → Prop) :
    Bad value actual E (fun _ => false) ↔ ∃ x, ¬ E x := by
  constructor
  · rintro ⟨x,_,hx⟩; exact ⟨x,hx⟩
  · rintro ⟨x,hx⟩
    refine ⟨x,?_,hx⟩
    intro c hc
    cases hc

theorem no_explanation_check_iff {Cell : Type u} {World : Type v}
    (value : World → Cell → Bool) (actual : World) (E : World → Prop)
    (actualEffect : E actual)
    (determined : ∀ x, (∀ c, value x c = value actual c) → (E x ↔ E actual))
    (oracle : Mask Cell → Bool)
    (root : oracle (fun _ => false) = true ↔ Bad value actual E (fun _ => false)) :
    oracle (fun _ => false) = false ↔ ¬ ∃ C, Combined value actual E C := by
  rw [combined_exists_iff_failure value actual E actualEffect determined]
  have h := root.trans (empty_bad_iff_failure value actual E)
  cases ho : oracle (fun _ => false) <;> simp_all

/-- A proved executable reference oracle. The efficient runtime uses locally
checked tables and the proved sparse lookup binding instead of recomputing it. -/
def finiteBad {ns : Nat} (target m : Nat) (M : Machine (Fin ns) (Valuation m))
    (actual : Nat → Valuation m) (C : Mask (WindowCell target m)) : Bool :=
  canonicalTable M (allValuations m) (allowedFix target m actual C) target 0 M.initial

theorem finiteBad_iff {ns : Nat} (target m : Nat) (M : Machine (Fin ns) (Valuation m))
    (actual : Nat → Valuation m) (C : Mask (WindowCell target m)) :
    finiteBad target m M actual C = true ↔ Bad (windowValue target m) actual
      (fun input => replayOutput M M.initial input target = true) C := by
  exact checked_root_iff_bad target m M (List.finRange ns) (finRange_complete ns)
    actual C _ (canonicalTable_checked M (allValuations m) (List.finRange ns)
      (finRange_complete ns) (allowedFix target m actual C) target)

theorem finiteMinimalCheck_iff {ns : Nat} (target m : Nat)
    (M : Machine (Fin ns) (Valuation m)) (actual : Nat → Valuation m)
    (order : List (WindowCell target m)) (complete : ∀ c, c ∈ order)
    (C : Mask (WindowCell target m)) :
    minimalCheck (finiteBad target m M actual) order C = true ↔
      InclusionMinimal (Combined (windowValue target m) actual
        (fun input => replayOutput M M.initial input target = true)) C := by
  apply minimalCheck_combined_iff _ _ _ _ order complete C
  · exact finiteBad_iff target m M actual C
  · exact finiteBad_iff target m M actual (complement C)
  · intro c _; exact finiteBad_iff target m M actual (erase C c)
  · intro c _; exact finiteBad_iff target m M actual (complement (erase C c))

theorem finiteNoExplanation_iff {ns : Nat} (target m : Nat)
    (M : Machine (Fin ns) (Valuation m)) (actual : Nat → Valuation m)
    (positive : replayOutput M M.initial actual target = true) :
    finiteBad target m M actual (fun _ => false) = false ↔
      ¬ ∃ C, Combined (windowValue target m) actual
        (fun input => replayOutput M M.initial input target = true) C := by
  apply no_explanation_check_iff (windowValue target m) actual
    (fun input => replayOutput M M.initial input target = true) positive
    (oracle := finiteBad target m M actual)
  · intro input agree
    change (replayOutput M M.initial input target = true) ↔
      (replayOutput M M.initial actual target = true)
    rw [window_determines_effect target m M actual input agree]
  · exact finiteBad_iff target m M actual (fun _ => false)

end Trace2
