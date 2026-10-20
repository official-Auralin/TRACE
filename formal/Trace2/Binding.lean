import Trace2.Semantics
import Trace2.Layered

namespace Trace2

abbrev Valuation (m : Nat) := Fin m → Bool
abbrev WindowCell (target m : Nat) := Fin (target + 1) × Fin m

def windowValue (target m : Nat) (input : Nat → Valuation m)
    (cell : WindowCell target m) : Bool := input cell.1.val cell.2

/-- Complete canonical Boolean input alphabet, independent of any corpus. -/
def allValuations : (m : Nat) → List (Valuation m)
  | 0 => [fun i => Fin.elim0 i]
  | m + 1 => (allValuations m).flatMap
      (fun tail => [Fin.cases false tail, Fin.cases true tail])

theorem allValuations_complete (m : Nat) (v : Valuation m) :
    v ∈ allValuations m := by
  induction m with
  | zero =>
    have he : v = (fun i => Fin.elim0 i) := by
      funext i; exact Fin.elim0 i
    simp [allValuations,he]
  | succ m ih =>
    have ht := ih (fun i => v i.succ)
    have he : v = Fin.cases (v 0) (fun i => v i.succ) := by
      funext i
      exact Fin.cases rfl (fun _ => rfl) i
    rw [he]
    apply List.mem_flatMap.mpr
    refine ⟨fun i => v i.succ,ht,?_⟩
    cases v 0 <;> simp

theorem finRange_complete (n : Nat) (i : Fin n) : i ∈ List.finRange n := by
  exact List.mem_ofFn.mpr ⟨i,rfl⟩

theorem bool_guard (selected x y : Bool) :
    ((!selected) || (x == y)) = true ↔ selected = true → x = y := by
  cases selected <;> cases x <;> cases y <;> decide

def allowedFix (target m : Nat) (actual : Nat → Valuation m)
    (fixed : Mask (WindowCell target m)) (t : Nat) (input : Valuation m) : Bool :=
  if ht : t < target + 1 then
    (List.finRange m).all (fun r => !(fixed (⟨t,ht⟩,r)) || (input r == actual t r))
  else true

theorem allowedFix_iff (target m : Nat) (actual : Nat → Valuation m)
    (fixed : Mask (WindowCell target m)) (t : Nat) (ht : t < target + 1)
    (input : Valuation m) :
    allowedFix target m actual fixed t input = true ↔
      ∀ r, fixed (⟨t,ht⟩,r) = true → input r = actual t r := by
  unfold allowedFix
  rw [dif_pos ht]
  simp only [List.all_eq_true,bool_guard]
  constructor
  · intro h r; exact h r (finRange_complete m r)
  · intro h r _; exact h r

theorem permitted_iff_fixes (target m : Nat) (actual input : Nat → Valuation m)
    (fixed : Mask (WindowCell target m)) :
    Permitted (allowedFix target m actual fixed) 0 target input ↔
      Fixes (windowValue target m) actual input fixed := by
  constructor
  · intro hp cell hc
    rcases cell with ⟨t,r⟩
    have ha := hp t.val (by have := t.isLt; omega)
    simp only [Nat.zero_add] at ha
    exact ((allowedFix_iff target m actual fixed t.val t.isLt (input t.val)).mp ha) r hc
  · intro hf t ht
    simp only [Nat.zero_add]
    rw [allowedFix_iff target m actual fixed t (by omega)]
    intro r hr
    exact hf (⟨t,by omega⟩,r) hr

/-- Complete bridge from the checked Boolean table to the quantified Bad(F). -/
theorem checked_root_iff_bad {S : Type} (target m : Nat)
    (M : Machine S (Valuation m)) (states : List S) (statesComplete : ∀ q, q ∈ states)
    (actual : Nat → Valuation m) (fixed : Mask (WindowCell target m))
    (table : Nat → S → Bool)
    (checked : checkTable M (allValuations m) states
      (allowedFix target m actual fixed) target table = true) :
    table 0 M.initial = true ↔ Bad (windowValue target m) actual
      (fun input => replayOutput M M.initial input target = true) fixed := by
  rw [checked_table_replay_iff M (allValuations m) (allValuations_complete m)
    states statesComplete (allowedFix target m actual fixed) target table checked]
  constructor
  · rintro ⟨input,hp,ho⟩
    refine ⟨input,(permitted_iff_fixes target m actual input fixed).mp hp,?_⟩
    simp [ho]
  · rintro ⟨input,hp,ho⟩
    refine ⟨input,(permitted_iff_fixes target m actual input fixed).mpr hp,?_⟩
    cases h : replayOutput M M.initial input target <;> simp_all

theorem window_determines_effect {S : Type} (target m : Nat)
    (M : Machine S (Valuation m)) (actual input : Nat → Valuation m)
    (agree : ∀ c, windowValue target m input c = windowValue target m actual c) :
    replayOutput M M.initial input target = replayOutput M M.initial actual target := by
  rw [replayOutput_eq_mealy, replayOutput_eq_mealy]
  apply TraceReview.mealy_output_prefix
  intro t ht
  funext r
  exact agree (⟨t,by omega⟩,r)

end Trace2
