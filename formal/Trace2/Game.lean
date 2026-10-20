import Trace2.Semantics

namespace Trace2
universe u v

inductive Branch where
  | guarantee
  | prevention
  deriving DecidableEq

def branchLegal {Cell : Type u} {World : Type v}
    (value : World → Cell → Bool) (actual : World) (C : Mask Cell) : Branch → World → Prop
  | .guarantee, x => Fixes value actual x C
  | .prevention, x => Fixes value actual x (complement C)

def branchSuccess {World : Type v} (E : World → Prop) : Branch → World → Prop
  | .guarantee, x => E x
  | .prevention, x => ¬ E x

/-- A policy supplies the prevention input word. The challenger chooses the
branch, and every legal guarantee word. Machine evolution is forced. -/
def WinningWordPolicy {Cell : Type u} {World : Type v}
    (value : World → Cell → Bool) (actual : World) (E : World → Prop)
    (C : Mask Cell) (chosen : World) : Prop :=
  Fixes value actual chosen (complement C) ∧
  ∀ branch x, branchLegal value actual C branch x →
    (branch = .prevention → x = chosen) → branchSuccess E branch x

theorem winning_policy_iff_combined {Cell : Type u} {World : Type v}
    (value : World → Cell → Bool) (actual : World) (E : World → Prop)
    (C : Mask Cell) :
    (∃ chosen, WinningWordPolicy value actual E C chosen) ↔ Combined value actual E C := by
  constructor
  · rintro ⟨chosen,hlegal,hwin⟩
    refine ⟨(guarantee_iff value actual E C).mpr ?_,chosen,hlegal,?_⟩
    · intro x hx
      exact hwin .guarantee x hx (by intro h; cases h)
    · exact hwin .prevention chosen hlegal (by intro _; rfl)
  · rintro ⟨hg,chosen,hlegal,hfail⟩
    refine ⟨chosen,hlegal,?_⟩
    intro branch x hx hchosen
    cases branch with
    | guarantee => exact (guarantee_iff value actual E C).mp hg x hx
    | prevention => simpa [hchosen rfl] using hfail

/-- The two losing obligations are distinguished: a guarantee counterexample,
or the universal absence of a prevention witness. -/
theorem no_winning_policy_iff {Cell : Type u} {World : Type v}
    (value : World → Cell → Bool) (actual : World) (E : World → Prop)
    (C : Mask Cell) :
    (¬ ∃ chosen, WinningWordPolicy value actual E C chosen) ↔
      Bad value actual E C ∨ ¬ Bad value actual E (complement C) := by
  classical
  rw [winning_policy_iff_combined]
  simp only [Combined,Guarantee,Prevention]
  constructor
  · intro h
    by_cases hb : Bad value actual E C
    · exact Or.inl hb
    · exact Or.inr (fun hp => h ⟨hb,hp⟩)
  · intro h ⟨hg,hp⟩
    rcases h with hb | hn
    · exact hg hb
    · exact hn hp

/-- Bounded play is padded by one absorbing priority after its target. -/
def paddedPriority (success : Bool) (cutoff : Nat) (t : Nat) : Nat :=
  if t < cutoff then 2 else if success then 0 else 1

def InfinitelyOftenPriority (priority : Nat → Nat) (p : Nat) : Prop :=
  ∀ n, ∃ t, n ≤ t ∧ priority t = p

def MinEven (priority : Nat → Nat) : Prop :=
  ∃ p, InfinitelyOftenPriority priority p ∧ p % 2 = 0 ∧
    ∀ q, InfinitelyOftenPriority priority q → p ≤ q

theorem padded_infinitely_often (success : Bool) (cutoff p : Nat) :
    InfinitelyOftenPriority (paddedPriority success cutoff) p ↔
      p = (if success then 0 else 1) := by
  constructor
  · intro h
    obtain ⟨t,ht,hp⟩ := h cutoff
    have hn : ¬ t < cutoff := by omega
    simpa [paddedPriority,hn] using hp.symm
  · intro hp n
    refine ⟨max n cutoff,Nat.le_max_left _ _,?_⟩
    have hn : ¬ max n cutoff < cutoff := by have := Nat.le_max_right n cutoff; omega
    simp [paddedPriority,hn,hp]

theorem padded_min_even_iff (success : Bool) (cutoff : Nat) :
    MinEven (paddedPriority success cutoff) ↔ success = true := by
  constructor
  · rintro ⟨p,hp,he,_⟩
    have hv := (padded_infinitely_often success cutoff p).mp hp
    cases success <;> simp_all
  · intro hs
    subst success
    refine ⟨0,(padded_infinitely_often true cutoff 0).mpr rfl,by decide,?_⟩
    intro q _; exact Nat.zero_le q

/-- Parity acceptance is a faithful encoding of terminal success, not a claim
that the original controller's synthesis arena has been reconstructed. -/
def WinningParityPolicy {Cell : Type u} {World : Type v}
    (value : World → Cell → Bool) (actual : World) (E : World → Prop)
    [DecidablePred E] (C : Mask Cell) (chosen : World) (cutoff : Nat) : Prop :=
  Fixes value actual chosen (complement C) ∧
  ∀ branch x, branchLegal value actual C branch x →
    (branch = .prevention → x = chosen) →
      MinEven (paddedPriority
        (match branch with | .guarantee => decide (E x) | .prevention => decide (¬ E x)) cutoff)

theorem parity_policy_iff_word_policy {Cell : Type u} {World : Type v}
    (value : World → Cell → Bool) (actual : World) (E : World → Prop)
    [DecidablePred E] (C : Mask Cell) (chosen : World) (cutoff : Nat) :
    WinningParityPolicy value actual E C chosen cutoff ↔
      WinningWordPolicy value actual E C chosen := by
  constructor
  · rintro ⟨hl,hw⟩
    refine ⟨hl,?_⟩
    intro branch x hx hc
    have hp := (padded_min_even_iff _ cutoff).mp (hw branch x hx hc)
    cases branch <;> simpa [branchSuccess] using hp
  · rintro ⟨hl,hw⟩
    refine ⟨hl,?_⟩
    intro branch x hx hc
    apply (padded_min_even_iff _ cutoff).mpr
    have hp := hw branch x hx hc
    cases branch <;> simpa [branchSuccess] using hp

theorem parity_game_iff_combined {Cell : Type u} {World : Type v}
    (value : World → Cell → Bool) (actual : World) (E : World → Prop)
    [DecidablePred E] (C : Mask Cell) (cutoff : Nat) :
    (∃ chosen, WinningParityPolicy value actual E C chosen cutoff) ↔
      Combined value actual E C := by
  constructor
  · rintro ⟨chosen,hp⟩
    exact (winning_policy_iff_combined value actual E C).mp
      ⟨chosen,(parity_policy_iff_word_policy value actual E C chosen cutoff).mp hp⟩
  · intro hc
    obtain ⟨chosen,hw⟩ := (winning_policy_iff_combined value actual E C).mpr hc
    exact ⟨chosen,(parity_policy_iff_word_policy value actual E C chosen cutoff).mpr hw⟩

end Trace2
