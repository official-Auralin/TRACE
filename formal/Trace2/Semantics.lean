import Std

namespace Trace2

universe u v
abbrev Mask (Cell : Type u) := Cell → Bool

def Included {Cell : Type u} (C D : Mask Cell) : Prop :=
  ∀ c, C c = true → D c = true

def complement {Cell : Type u} (C : Mask Cell) : Mask Cell := fun c => !(C c)

def Fixes {Cell : Type u} {World : Type v}
    (value : World → Cell → Bool) (actual x : World) (C : Mask Cell) : Prop :=
  ∀ c, C c = true → value x c = value actual c

def Bad {Cell : Type u} {World : Type v}
    (value : World → Cell → Bool) (actual : World) (E : World → Prop)
    (C : Mask Cell) : Prop := ∃ x, Fixes value actual x C ∧ ¬ E x

def Guarantee {Cell : Type u} {World : Type v}
    (value : World → Cell → Bool) (actual : World) (E : World → Prop)
    (C : Mask Cell) : Prop := ¬ Bad value actual E C

def Prevention {Cell : Type u} {World : Type v}
    (value : World → Cell → Bool) (actual : World) (E : World → Prop)
    (C : Mask Cell) : Prop := Bad value actual E (complement C)

def Combined {Cell : Type u} {World : Type v}
    (value : World → Cell → Bool) (actual : World) (E : World → Prop)
    (C : Mask Cell) : Prop := Guarantee value actual E C ∧ Prevention value actual E C

def Upward {Cell : Type u} (H : Mask Cell → Prop) : Prop :=
  ∀ C D, Included C D → H C → H D

def InclusionMinimal {Cell : Type u} (H : Mask Cell → Prop) (C : Mask Cell) : Prop :=
  H C ∧ ∀ D, Included D C → H D → Included C D

theorem included_refl {Cell : Type u} (C : Mask Cell) : Included C C := by
  intro c hc; exact hc

theorem included_trans {Cell : Type u} {A B C : Mask Cell}
    (hab : Included A B) (hbc : Included B C) : Included A C := by
  intro c hc; exact hbc c (hab c hc)

theorem complement_antitone {Cell : Type u} {C D : Mask Cell}
    (h : Included C D) : Included (complement D) (complement C) := by
  intro c hc
  cases hC : C c <;> cases hD : D c <;> simp_all [complement, Included]

theorem fixes_antitone {Cell : Type u} {World : Type v}
    (value : World → Cell → Bool) (actual x : World) {C D : Mask Cell}
    (h : Included C D) (hd : Fixes value actual x D) : Fixes value actual x C := by
  intro c hc; exact hd c (h c hc)

theorem bad_antitone {Cell : Type u} {World : Type v}
    (value : World → Cell → Bool) (actual : World) (E : World → Prop)
    {C D : Mask Cell} (h : Included C D) :
    Bad value actual E D → Bad value actual E C := by
  rintro ⟨x,hx,he⟩
  exact ⟨x, fixes_antitone value actual x h hx, he⟩

theorem guarantee_iff {Cell : Type u} {World : Type v}
    (value : World → Cell → Bool) (actual : World) (E : World → Prop)
    (C : Mask Cell) :
    Guarantee value actual E C ↔ ∀ x, Fixes value actual x C → E x := by
  classical
  constructor
  · intro hg x hx
    apply Classical.byContradiction
    intro hn
    exact hg ⟨x,hx,hn⟩
  · intro hg ⟨x,hx,hn⟩
    exact hn (hg x hx)

theorem guarantee_upward {Cell : Type u} {World : Type v}
    (value : World → Cell → Bool) (actual : World) (E : World → Prop) :
    Upward (Guarantee value actual E) := by
  intro C D h hg hb
  exact hg (bad_antitone value actual E h hb)

theorem prevention_upward {Cell : Type u} {World : Type v}
    (value : World → Cell → Bool) (actual : World) (E : World → Prop) :
    Upward (Prevention value actual E) := by
  intro C D h hp
  exact bad_antitone value actual E (complement_antitone h) hp

theorem combined_upward {Cell : Type u} {World : Type v}
    (value : World → Cell → Bool) (actual : World) (E : World → Prop) :
    Upward (Combined value actual E) := by
  intro C D h ⟨hg,hp⟩
  exact ⟨guarantee_upward value actual E C D h hg,
    prevention_upward value actual E C D h hp⟩

def erase {Cell : Type u} [DecidableEq Cell] (C : Mask Cell) (c : Cell) : Mask Cell :=
  fun i => if i = c then false else C i

theorem erase_self {Cell : Type u} [DecidableEq Cell] (C : Mask Cell) (c : Cell) :
    erase C c c = false := by simp [erase]

theorem erase_included {Cell : Type u} [DecidableEq Cell] (C : Mask Cell) (c : Cell) :
    Included (erase C c) C := by
  intro i hi
  by_cases hic : i = c
  · simp [erase,hic] at hi
  · simpa [erase,hic] using hi

theorem erase_monotone {Cell : Type u} [DecidableEq Cell]
    {C D : Mask Cell} (h : Included C D) (c : Cell) :
    Included (erase C c) (erase D c) := by
  intro i hi
  by_cases hic : i = c
  · simp [erase,hic] at hi
  · simp only [erase,if_neg hic] at hi ⊢
    exact h i hi

theorem included_erase_of_false {Cell : Type u} [DecidableEq Cell]
    {C D : Mask Cell} (h : Included D C) (c : Cell) (hd : D c = false) :
    Included D (erase C c) := by
  intro i hi
  by_cases hic : i = c
  · subst i; simp_all
  · simp only [erase,if_neg hic]; exact h i hi

theorem minimal_iff_single_deletions {Cell : Type u} [DecidableEq Cell]
    (H : Mask Cell → Prop) (up : Upward H) (C : Mask Cell) :
    InclusionMinimal H C ↔ H C ∧ ∀ c, C c = true → ¬ H (erase C c) := by
  constructor
  · rintro ⟨hc,hm⟩
    refine ⟨hc,?_⟩
    intro c hcc he
    have := hm (erase C c) (erase_included C c) he c hcc
    simp [erase] at this
  · rintro ⟨hc,hd⟩
    refine ⟨hc,?_⟩
    intro D hdc hD c hcc
    cases hdd : D c
    · have he := up D (erase C c) (included_erase_of_false hdc c hdd) hD
      exact False.elim (hd c hcc he)
    · rfl

/-- Full fixing guarantees an effect only if the observable cells determine it.
This explicit hypothesis prevents hidden-context assumptions. -/
theorem combined_exists_iff_failure {Cell : Type u} {World : Type v}
    (value : World → Cell → Bool) (actual : World) (E : World → Prop)
    (actualEffect : E actual)
    (determined : ∀ x, (∀ c, value x c = value actual c) → (E x ↔ E actual)) :
    (∃ C, Combined value actual E C) ↔ ∃ x, ¬ E x := by
  constructor
  · rintro ⟨C,_,x,_,hx⟩; exact ⟨x,hx⟩
  · rintro ⟨x,hx⟩
    refine ⟨fun _ => true,?_,x,?_,hx⟩
    · rw [guarantee_iff]
      intro y hy
      exact (determined y (fun c => hy c rfl)).mpr actualEffect
    · intro c hc
      simp [complement] at hc

end Trace2
