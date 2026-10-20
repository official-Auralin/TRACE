import Std

/-!
# TRACE reverse-parity review: proved semantic core

The type `α` is the *effective admissible domain*, not the universe of all traces.
For the finite-change interpretation use the subtype Adm ∩ Fin. No theorem here
asserts correctness of an LTL translator, parity solver, or automata construction.
-/
namespace TraceReview

universe u v

def Minimal {α : Type u} (r : α → α → Prop) (S : α → Prop) (x : α) : Prop :=
  S x ∧ ∀ y, S y → r y x → r x y

def Up {α : Type u} (r : α → α → Prop) (S : α → Prop) (x : α) : Prop :=
  ∃ y, S y ∧ r y x

structure Partial {α : Type u} (r : α → α → Prop) : Prop where
  refl : ∀ x, r x x
  trans : ∀ {x y z}, r x y → r y z → r x z
  antisymm : ∀ {x y}, r x y → r y x → x = y

def Strict {α : Type u} (r : α → α → Prop) (x y : α) := r x y ∧ ¬ r y x

def HasMinBelow {α : Type u} (r : α → α → Prop) : Prop :=
  ∀ (S : α → Prop) x, S x → ∃ m, Minimal r S m ∧ r m x

/-- Well-foundedness means well-foundedness of the *strict* part. -/
theorem wellFounded_hasMinBelow {α : Type u} {r : α → α → Prop}
    (h : Partial r) (wf : WellFounded (Strict r)) : HasMinBelow r := by
  classical
  intro S x
  induction x using wf.induction with
  | h x ih =>
    intro hx
    by_cases hm : ∀ y, S y → r y x → r x y
    · exact ⟨x, ⟨hx, hm⟩, h.refl x⟩
    · have hn : ∃ y, S y ∧ r y x ∧ ¬ r x y := by
        apply Classical.byContradiction
        intro hn
        apply hm
        intro y hy hyx
        apply Classical.byContradiction
        intro hxy
        exact hn ⟨y, hy, hyx, hxy⟩
      obtain ⟨y, hy, hyx, hxy⟩ := hn
      obtain ⟨m, hm, hmy⟩ := ih y ⟨hyx, hxy⟩ hy
      exact ⟨m, hm, h.trans hmy hyx⟩

/-- Antisymmetry is essential: equal-cost distinct worlds refute this. -/
theorem minimal_up_iff {α : Type u} {r : α → α → Prop}
    (h : Partial r) (F : α → Prop) (x : α) :
    Minimal r (Up r F) x ↔ Minimal r F x := by
  constructor
  · rintro ⟨⟨f, hf, hfx⟩, hm⟩
    have hxf := hm f ⟨f, hf, h.refl f⟩ hfx
    have heq : f = x := h.antisymm hfx hxf
    subst f
    exact ⟨hf, fun y hy hyx => hm y ⟨y, hy, h.refl y⟩ hyx⟩
  · rintro ⟨hx, hm⟩
    refine ⟨⟨x, hx, h.refl x⟩, ?_⟩
    rintro y ⟨f, hf, hfy⟩ hyx
    exact h.trans (hm f hf (h.trans hfy hyx)) hfy

def ValidCause {α : Type u} (r : α → α → Prop) (actual : α)
    (effect cause : α → Prop) : Prop :=
  cause actual ∧ effect actual ∧
  (∃ x, Minimal r (fun y => ¬ cause y) x) ∧
  ∀ x, Minimal r (fun y => ¬ cause y) x → ¬ effect x

def Canonical {α : Type u} (r : α → α → Prop) (effect : α → Prop) : α → Prop :=
  fun x => ¬ Up r (fun y => ¬ effect y) x

/-- Four semantic clauses only; candidate-language admission is separate. -/
theorem canonical_valid {α : Type u} {r : α → α → Prop}
    (h : Partial r) (hm : HasMinBelow r) (actual : α)
    (least : ∀ x, r actual x) (E : α → Prop) (hE : E actual)
    (failure : ∃ x, ¬ E x) : ValidCause r actual E (Canonical r E) := by
  classical
  have hcan : Canonical r E actual := by
    rintro ⟨f, hf, hfa⟩
    have hf_eq : f = actual := h.antisymm hfa (least f)
    exact hf (hf_eq ▸ hE)
  have remove_eq : (fun x => ¬ Canonical r E x) = Up r (fun x => ¬ E x) := by
    funext x
    simp [Canonical]
  refine ⟨hcan, hE, ?_, ?_⟩
  · obtain ⟨f, hf⟩ := failure
    obtain ⟨m, hmin, _⟩ := hm (fun x => ¬ E x) f hf
    exact ⟨m, remove_eq ▸ ((minimal_up_iff h _ m).mpr hmin)⟩
  · intro x hx
    have hx' : Minimal r (Up r (fun x => ¬ E x)) x := remove_eq ▸ hx
    exact ((minimal_up_iff h _ x).mp hx').1

/-- Language minimality among candidates with exactly the nearest-failure removals. -/
theorem canonical_smallest_anchored {α : Type u} {r : α → α → Prop}
    (hm : HasMinBelow r) (E C : α → Prop)
    (anchored : ∀ x, Minimal r (fun y => ¬ C y) x ↔
      Minimal r (fun y => ¬ E y) x) :
    ∀ x, Canonical r E x → C x := by
  classical
  intro x hx
  apply Classical.byContradiction
  intro hc
  obtain ⟨m, hmin, hmx⟩ := hm (fun y => ¬ C y) x hc
  exact hx ⟨m, ((anchored m).mp hmin).1, hmx⟩


/-- A preorder needs failure saturation of every equivalence class touching a
    minimal failure; totality alone is insufficient. -/
theorem minimal_up_iff_of_tie_saturation {α : Type u} {r : α → α → Prop}
    (refl : ∀ x, r x x) (trans : ∀ {x y z}, r x y → r y z → r x z)
    (F : α → Prop)
    (saturated : ∀ f x, Minimal r F f → r f x → r x f → F x) (x : α) :
    Minimal r (Up r F) x ↔ Minimal r F x := by
  constructor
  · rintro ⟨⟨f, hf, hfx⟩, hm⟩
    have hxf := hm f ⟨f, hf, refl f⟩ hfx
    have fmin : Minimal r F f := by
      refine ⟨hf, ?_⟩
      intro y hy hyf
      exact trans hfx (hm y ⟨y, hy, refl y⟩ (trans hyf hfx))
    exact ⟨saturated f x fmin hfx hxf,
      fun y hy hyx => hm y ⟨y, hy, refl y⟩ hyx⟩
  · rintro ⟨hx, hm⟩
    refine ⟨⟨x, hx, refl x⟩, ?_⟩
    rintro y ⟨f, hf, hfy⟩ hyx
    exact trans (hm f hf (trans hfy hyx)) hfy

theorem canonical_valid_of_tie_saturation {α : Type u} {r : α → α → Prop}
    (refl : ∀ x, r x x) (trans : ∀ {x y z}, r x y → r y z → r x z)
    (hm : HasMinBelow r) (actual : α) (E : α → Prop) (hE : E actual)
    (centered : ∀ f, ¬ E f → ¬ r f actual) (failure : ∃ x, ¬ E x)
    (saturated : ∀ f x, Minimal r (fun y => ¬ E y) f → r f x → r x f → ¬ E x) :
    ValidCause r actual E (Canonical r E) := by
  classical
  have remove_eq : (fun x => ¬ Canonical r E x) = Up r (fun x => ¬ E x) := by
    funext x
    simp [Canonical]
  refine ⟨?_, hE, ?_, ?_⟩
  · rintro ⟨f, hf, hfa⟩
    exact centered f hf hfa
  · obtain ⟨f, hf⟩ := failure
    obtain ⟨m, hmin, _⟩ := hm (fun x => ¬ E x) f hf
    exact ⟨m, remove_eq ▸ ((minimal_up_iff_of_tie_saturation refl trans _ saturated m).mpr hmin)⟩
  · intro x hx
    have hx' : Minimal r (Up r (fun x => ¬ E x)) x := remove_eq ▸ hx
    exact ((minimal_up_iff_of_tie_saturation refl trans _ saturated x).mp hx').1


/-- The correct partial-order reading is downward closure, not total proximity. -/
theorem canonical_downward {α : Type u} {r : α → α → Prop}
    (h : Partial r) (E : α → Prop) :
    ∀ x y, r y x → Canonical r E x → Canonical r E y := by
  rintro x y hyx hx ⟨f, hf, hfy⟩
  exact hx ⟨f, hf, h.trans hfy hyx⟩

theorem canonical_largest_failure_free_downset {α : Type u} {r : α → α → Prop}
    (E D : α → Prop) (down : ∀ x y, r y x → D x → D y)
    (free : ∀ x, D x → E x) : ∀ x, D x → Canonical r E x := by
  rintro x hx ⟨f, hf, hfx⟩
  exact hf (free f (down x f hfx hx))

theorem canonical_total_characterization {α : Type u} {r : α → α → Prop}
    (total : ∀ x y, r x y ∨ r y x) (E : α → Prop) (x : α) :
    Canonical r E x ↔ ∀ f, ¬ E f → Strict r x f := by
  constructor
  · intro hx f hf
    have hn : ¬ r f x := fun hfx => hx ⟨f, hf, hfx⟩
    exact ⟨(total x f).resolve_right hn, hn⟩
  · rintro hx ⟨f, hf, hfx⟩
    exact (hx f hf).2 hfx

/-- Any single failure produces an extensionally degenerate valid candidate. -/
theorem single_failure_complement_valid {α : Type u} {r : α → α → Prop}
    (actual f : α) (E : α → Prop) (ha : E actual) (hf : ¬ E f) :
    ValidCause r actual E (fun x => x ≠ f) := by
  classical
  have haf : actual ≠ f := fun heq => hf (heq ▸ ha)
  refine ⟨haf, ha, ⟨f, ?_⟩, ?_⟩
  · refine ⟨by simp, ?_⟩
    intro y hy hyf
    have heq : y = f := Classical.not_not.mp hy
    subst y
    exact hyf
  · intro x hx
    have heq : x = f := Classical.not_not.mp hx.1
    exact heq ▸ hf

/-- An invariant cannot have a nonvacuous removal within its own behavior set. -/
theorem invariant_has_no_removal {α : Type u} (A M C : α → Prop)
    (hAM : ∀ x, A x → M x) (hMC : ∀ x, M x → C x) :
    ¬ ∃ x, A x ∧ ¬ C x := by
  rintro ⟨x, hx, hn⟩
  exact hn (hMC x (hAM x hx))

theorem invariant_not_valid {α : Type u} (r : α → α → Prop)
    (actual : α) (E C : α → Prop) (invariant : ∀ x, C x) :
    ¬ ValidCause r actual E C := by
  rintro ⟨_, _, ⟨x, hx⟩, _⟩
  exact hx.1 (invariant x)

/- Counterexamples: Fin 3 names actual=0, failure=1, effect-preserving alternative=2. -/
def tiedCost (x : Fin 3) : Nat := if x = 0 then 0 else 1
def tiedOrder (x y : Fin 3) : Prop := tiedCost x ≤ tiedCost y
def forkOrder (x y : Fin 3) : Prop := x = 0 ∨ x = y
def sampleEffect (x : Fin 3) : Prop := x ≠ 1

/-- Totality of a preorder does not imply antisymmetry. -/
theorem total_preorder_not_antisymmetric :
    (∀ x y : Fin 3, tiedOrder x y ∨ tiedOrder y x) ∧
    tiedOrder 1 2 ∧ tiedOrder 2 1 ∧ (1 : Fin 3) ≠ 2 := by
  unfold tiedOrder tiedCost
  decide

theorem tied_failure_minima_differ :
    Minimal tiedOrder (Up tiedOrder (fun x => ¬ sampleEffect x)) 2 ∧
    ¬ Minimal tiedOrder (fun x => ¬ sampleEffect x) 2 := by
  unfold Minimal Up tiedOrder tiedCost sampleEffect
  decide

theorem tied_canonical_invalid :
    ¬ ValidCause tiedOrder 0 sampleEffect (Canonical tiedOrder sampleEffect) := by
  unfold ValidCause Canonical Minimal Up tiedOrder tiedCost sampleEffect
  decide

theorem incomparable_canonical_not_strictly_closer :
    Canonical forkOrder sampleEffect 2 ∧
    ¬ Strict forkOrder (2 : Fin 3) 1 := by
  unfold Canonical Up Strict forkOrder sampleEffect
  decide

theorem fork_is_partial : Partial forkOrder := by
  constructor <;> unfold forkOrder <;> decide

/-- The disjunct that actually holds masks the other disjunct's removal. -/
theorem or_background_does_not_repair :
    ∀ a : Bool, (a || true) = true := by

  decide

end TraceReview
