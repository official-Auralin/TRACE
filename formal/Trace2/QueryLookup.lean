import Trace2.Compiler

namespace Trace2.Runtime

def cellOrder (k m : Nat) : List (WindowCell k m) :=
  (List.finRange (k+1)).flatMap (fun t => (List.finRange m).map (fun r => (t,r)))

theorem cellOrder_complete (k m : Nat) (c : WindowCell k m) : c ∈ cellOrder k m := by
  apply List.mem_flatMap.mpr
  refine ⟨c.1, finRange_complete _ _, ?_⟩
  exact List.mem_map.mpr ⟨c.2, finRange_complete _ _, rfl⟩

def cellId {k m : Nat} (c : WindowCell k m) : Nat := c.1.val*m+c.2.val

def maskCells {k m : Nat} (C : Mask (WindowCell k m)) : List Nat :=
  ((cellOrder k m).filter C).map cellId

theorem cellId_injective {k m : Nat} (a b : WindowCell k m)
    (same : cellId a = cellId b) : a = b := by
  have h := Trace2.cellId_injective a.1.val b.1.val a.2 b.2 same
  exact Prod.ext (Fin.ext h.1) h.2

theorem mem_maskCells {k m : Nat} (C : Mask (WindowCell k m)) (c : WindowCell k m) :
    cellId c ∈ maskCells C ↔ C c = true := by
  constructor
  · intro h
    obtain ⟨d, hd, he⟩ := List.mem_map.mp h
    have hc := cellId_injective d c he
    subst d
    exact (List.mem_filter.mp hd).2
  · intro h
    exact List.mem_map.mpr ⟨c, List.mem_filter.mpr ⟨cellOrder_complete k m c, h⟩, rfl⟩

theorem maskCells_injective {k m : Nat} (C D : Mask (WindowCell k m))
    (same : maskCells C = maskCells D) : C = D := by
  funext c
  have h : C c = true ↔ D c = true := by
    rw [← mem_maskCells C c, ← mem_maskCells D c, same]
  cases hc : C c <;> cases hd : D c <;> simp_all

def rootsLookup {k m : Nat} (roots : List (List Nat × Bool))
    (C : Mask (WindowCell k m)) : Bool :=
  ((roots.find? (fun p => p.1 == maskCells C)).map Prod.snd).getD false

def rootsHas {k m : Nat} (roots : List (List Nat × Bool))
    (C : Mask (WindowCell k m)) : Bool :=
  roots.any (fun p => p.1 == maskCells C)

/-- Soundness of an accumulated checked root list. This permits sparse query
sets; no value for an absent query is ever used to certify an answer. -/
def RootsSound {k m : Nat} (roots : List (List Nat × Bool))
    (oracle : Mask (WindowCell k m) → Bool) : Prop :=
  ∀ pair, pair ∈ roots → ∀ C, pair.1 = maskCells C → pair.2 = oracle C

theorem rootsLookup_eq {k m : Nat} (roots : List (List Nat × Bool))
    (oracle : Mask (WindowCell k m) → Bool) (sound : RootsSound roots oracle)
    (C : Mask (WindowCell k m)) (present : rootsHas roots C = true) :
    rootsLookup roots C = oracle C := by
  induction roots with
  | nil => simp [rootsHas] at present
  | cons p rest ih =>
    by_cases hp : p.1 = maskCells C
    · simp only [rootsLookup, List.find?_cons, hp, beq_self_eq_true,
        Option.map_some, Option.getD_some]
      exact sound p (by simp) C hp
    · have hrest : RootsSound rest oracle := by
        intro pair hpair D hd
        exact sound pair (by simp [hpair]) D hd
      have hhas : rootsHas rest C = true := by
        simpa [rootsHas, hp] using present
      simpa [rootsLookup, hp] using ih hrest hhas

/-- Local-table correctness plus injective canonical cell keys binds an inserted
root to every future lookup with that key. -/
theorem checked_query_binding {ns k m : Nat}
    (M : Machine (Fin ns) (Valuation m)) (actual : Nat → Valuation m)
    (C D : Mask (WindowCell k m)) (table : Nat → Fin ns → Bool)
    (checked : checkTable M (allValuations m) (List.finRange ns)
      (allowedFix k m actual C) k table = true)
    (same : maskCells C = maskCells D) :
    table 0 M.initial = finiteBad k m M actual D := by
  have he := maskCells_injective C D same
  subst D
  have ht := checked_root_iff_bad k m M (List.finRange ns) (finRange_complete ns)
    actual C table checked
  have hb := finiteBad_iff k m M actual C
  cases hr : table 0 M.initial <;> cases hf : finiteBad k m M actual C <;> simp_all

theorem rootsSound_append_checked {ns k m : Nat}
    (M : Machine (Fin ns) (Valuation m)) (actual : Nat → Valuation m)
    (roots : List (List Nat × Bool)) (sound : RootsSound roots (finiteBad k m M actual))
    (C : Mask (WindowCell k m)) (table : Nat → Fin ns → Bool)
    (checked : checkTable M (allValuations m) (List.finRange ns)
      (allowedFix k m actual C) k table = true) :
    RootsSound (roots ++ [(maskCells C, table 0 M.initial)]) (finiteBad k m M actual) := by
  intro pair hpair D hd
  rcases List.mem_append.mp hpair with hold | hnew
  · exact sound pair hold D hd
  · have hp : pair = (maskCells C, table 0 M.initial) := by simpa using hnew
    subst pair
    exact checked_query_binding M actual C D table checked hd

def requiredKeys {k m : Nat} (C : Mask (WindowCell k m)) : List (List Nat) :=
  [maskCells (fun _ : WindowCell k m => false), maskCells C, maskCells (complement C)] ++
    ((cellOrder k m).filter C).flatMap (fun c =>
      [maskCells (erase C c), maskCells (complement (erase C c))])

def rootsCover {k m : Nat} (roots : List (List Nat × Bool))
    (C : Mask (WindowCell k m)) : Bool :=
  (requiredKeys C).all (fun key => roots.any (fun p => p.1 == key))

theorem covered_key_present {k m : Nat} (roots : List (List Nat × Bool))
    (C D : Mask (WindowCell k m)) (covered : rootsCover roots C = true)
    (required : maskCells D ∈ requiredKeys C) : rootsHas roots D = true := by
  exact List.all_eq_true.mp covered (maskCells D) required

theorem checked_lookup_minimal_iff {ns k m : Nat}
    (M : Machine (Fin ns) (Valuation m)) (actual : Nat → Valuation m)
    (roots : List (List Nat × Bool)) (sound : RootsSound roots (finiteBad k m M actual))
    (C : Mask (WindowCell k m)) (covered : rootsCover roots C = true) :
    minimalCheck (rootsLookup roots) (cellOrder k m) C = true ↔
      InclusionMinimal (Combined (windowValue k m) actual
        (fun input => replayOutput M M.initial input k = true)) C := by
  have bound : ∀ D, maskCells D ∈ requiredKeys C →
      (rootsLookup roots D = true ↔ Bad (windowValue k m) actual
        (fun input => replayOutput M M.initial input k = true) D) := by
    intro D hd
    rw [rootsLookup_eq roots _ sound D (covered_key_present roots C D covered hd)]
    exact finiteBad_iff k m M actual D
  apply minimalCheck_combined_iff _ _ _ _ _ (cellOrder_complete k m) C
  · exact bound C (by simp [requiredKeys])
  · exact bound (complement C) (by simp [requiredKeys])
  · intro c hc
    apply bound
    apply List.mem_append_right
    apply List.mem_flatMap.mpr
    exact ⟨c, List.mem_filter.mpr ⟨cellOrder_complete k m c, hc⟩, by simp⟩
  · intro c hc
    apply bound
    apply List.mem_append_right
    apply List.mem_flatMap.mpr
    exact ⟨c, List.mem_filter.mpr ⟨cellOrder_complete k m c, hc⟩, by simp⟩

theorem checked_lookup_no_explanation_iff {ns k m : Nat}
    (M : Machine (Fin ns) (Valuation m)) (actual : Nat → Valuation m)
    (positive : replayOutput M M.initial actual k = true)
    (roots : List (List Nat × Bool)) (sound : RootsSound roots (finiteBad k m M actual))
    (present : rootsHas roots (fun _ : WindowCell k m => false) = true) :
    rootsLookup roots (fun _ : WindowCell k m => false) = false ↔
      ¬ ∃ C, Combined (windowValue k m) actual
        (fun input => replayOutput M M.initial input k = true) C := by
  rw [rootsLookup_eq roots _ sound _ present]
  exact finiteNoExplanation_iff k m M actual positive

end Trace2.Runtime
