import Lean
import Trace2.QueryLookup

namespace Trace2.Runtime
open Lean

structure Edge where
  next : Nat
  output : Nat
  deriving FromJson, Inhabited
structure RawMachine where
  inputs : Array String
  states : Nat
  initial : Nat
  transitions : Array (Array Edge)
  deriving FromJson
structure Item where
  id : String
  machine : RawMachine
  observed : Array (Array Nat)
  observed_outputs : Array Nat
  observed_states : Array Nat
  target_step : Nat
  semantics : Json
  deriving FromJson
structure Execution where
  outputs : Array Nat
  states : Array Nat
  deriving FromJson
structure Query where
  fixed_cells : Array Nat
  bad_layers : Array (Array Bool)
  failure_inputs : Option (Array (Array Nat))
  deriving FromJson
structure Certificate where
  schema_version : String
  instance_sha256 : String
  answer : Json
  actual_execution : Execution
  queries : Array Query
  deriving FromJson
structure Record where
  item : Item
  certificate : Certificate
  deriving FromJson

def expectedSemantics : Json := Json.mkObj [
  ("version", Json.str "trace.gp.v2"),
  ("answer", Json.str "one inclusion-minimal set satisfying guarantee and prevention"),
  ("cell_encoding", Json.str "cell = step * number_of_inputs + input_index; both zero-based"),
  ("selected_value", Json.str "the observed Boolean value, including zero"),
  ("output_timing", Json.str "output is emitted by the current-state/current-input transition before changing state"),
  ("effect", Json.str "the single output equals 1 at target_step"),
  ("guarantee", Json.str "every input assignment agreeing with selected cells preserves the effect"),
  ("prevention", Json.str "some input assignment agreeing with every unselected cell makes the effect false"),
  ("minimality", Json.str "no proper subset still satisfies both; not minimum cardinality"),
  ("counterfactuals", Json.str "all Boolean input assignments through target_step, replayed from the same initial state")
]

def ensure (condition : Bool) (message : String) : Except String Unit :=
  if condition then .ok () else .error message

def unique [BEq α] (xs : Array α) : Bool :=
  xs.toList == xs.toList.eraseDups

def bitRows (rows : Array (Array Nat)) (height width : Nat) : Bool :=
  rows.size == height && rows.all (fun row => row.size == width && row.all (· ≤ 1))

def inputWord (rows : Array (Array Nat)) (m : Nat) : Nat → Valuation m :=
  fun t r => (rows[t]?.getD #[])[r.val]?.getD 0 == 1

def valuationCode {m : Nat} (v : Valuation m) : Nat :=
  (List.finRange m).foldl (fun acc r => acc + if v r then 2^r.val else 0) 0

def selection (k m : Nat) (cells : Array Nat) : Mask (WindowCell k m) :=
  fun c => cells.contains (cellId c)

def rowsTable {ns : Nat} (rows : Array (Array Bool)) : Nat → Fin ns → Bool :=
  fun t q => (rows[t]?.getD #[])[q.val]?.getD false

/-- JSON decoding and bounds checks are a documented input boundary. Accepted
records are evaluated by the same Boolean definitions used in the theorems. -/
def checkRecord (record : Record) : Except String Unit := do
  let item := record.item
  let cert := record.certificate
  let raw := item.machine
  let ns := raw.states
  let m := raw.inputs.size
  let k := item.target_step
  let n := (k+1)*m
  ensure (ns > 0 && m > 0) "machine dimensions must be positive"
  ensure (unique raw.inputs) "duplicate input names"
  ensure (raw.inputs.all (fun name => !name.isEmpty)) "empty input name"
  ensure (raw.initial < ns && raw.transitions.size == ns) "invalid machine state bounds"
  ensure (raw.transitions.all (fun row => row.size == 2^m &&
    row.all (fun edge => edge.next < ns && edge.output ≤ 1))) "invalid total binary machine"
  ensure (bitRows item.observed (k+1) m) "invalid observed inputs"
  ensure (item.observed_outputs.size == k+1 && item.observed_states.size == k+2)
    "invalid observed execution dimensions"
  ensure (item.semantics == expectedSemantics) "wrong task semantics"
  ensure (cert.schema_version == "trace.gp-certificate.v2") "wrong certificate schema"
  ensure (cert.instance_sha256.length == 64 && cert.instance_sha256.toList.all
    (fun c => c.isDigit || ('a' ≤ c && c ≤ 'f'))) "malformed instance digest"
  if hn : 0 < ns then
    let initial : Fin ns := ⟨raw.initial % ns, Nat.mod_lt _ hn⟩
    let edge := fun (q : Fin ns) (v : Valuation m) =>
      ((raw.transitions[q.val]?.getD #[])[valuationCode v]?.getD default)
    let M : Machine (Fin ns) (Valuation m) := {
      initial := initial
      step := fun q v => ⟨(edge q v).next % ns, Nat.mod_lt _ hn⟩
      emit := fun q v => (edge q v).output == 1 }
    let alphabet := allValuations m
    ensure ((alphabet.map valuationCode).length == 2^m &&
      (alphabet.map valuationCode).all (· < 2^m) &&
      (alphabet.map valuationCode).eraseDups.length == 2^m)
      "input valuation encoding is not a complete bijection"
    let actual := inputWord item.observed m
    let mut state := initial
    let mut output : Array Nat := #[]
    let mut states : Array Nat := #[initial.val]
    for t in List.range (k+1) do
      output := output.push (if M.emit state (actual t) then 1 else 0)
      state := M.step state (actual t)
      states := states.push state.val
    ensure (output == item.observed_outputs && states == item.observed_states)
      "public actual execution does not replay"
    ensure (output == cert.actual_execution.outputs && states == cert.actual_execution.states)
      "certificate actual execution does not replay"
    ensure ((output[k]?.getD 0) == 1) "target is not actually positive"
    let mut roots : List (List Nat × Bool) := []
    for query in cert.queries do
      ensure (unique query.fixed_cells && query.fixed_cells.all (· < n))
        "invalid fixed cell set"
      ensure (query.bad_layers.size == k+1 && query.bad_layers.all (fun row => row.size == ns))
        "invalid recurrence table dimensions"
      let C := selection k m query.fixed_cells
      let key := maskCells C
      ensure (!(roots.any (fun p => p.1 == key))) "duplicate fixing query"
      let table := rowsTable (ns := ns) query.bad_layers
      ensure (checkTable M alphabet (List.finRange ns) (allowedFix k m actual C) k table)
        "local recurrence equation failed"
      let root := table 0 initial
      match query.failure_inputs with
      | none => ensure (!root) "true Bad root requires a failure witness"
      | some rows =>
        ensure root "false Bad root must have no failure witness"
        ensure (bitRows rows (k+1) m) "invalid failure witness dimensions"
        let input := inputWord rows m
        ensure ((List.range (k+1)).all (fun t => allowedFix k m actual C t (input t)))
          "failure witness changed a fixed cell"
        ensure (!(replayOutput M initial input k)) "failure witness does not defeat target"
      roots := roots ++ [(key,root)]
    let lookup := rootsLookup (k := k) (m := m) roots
    let has := rootsHas (k := k) (m := m) roots
    let empty : Mask (WindowCell k m) := fun _ => false
    ensure (has empty) "missing global defeat query"
    match cert.answer.getObjVal? "cells" with
    | .ok json =>
      ensure (cert.answer == Json.mkObj [("cells",json)]) "invalid cells answer schema"
      let selected : Array Nat ← fromJson? json
      ensure (unique selected && selected.all (· < n)) "invalid selected cells"
      let C := selection k m selected
      let order := cellOrder k m
      let required := requiredKeys C
      ensure (rootsCover roots C &&
        roots.all (fun p => required.contains p.1)) "missing or surplus answer queries"
      ensure (minimalCheck lookup order C) "certificate answer is not inclusion-minimal G and P"
    | .error _ =>
      let verdict ← cert.answer.getObjValAs? String "verdict"
      ensure (verdict == "no_explanation" && cert.answer ==
        Json.mkObj [("verdict",Json.str "no_explanation")]) "invalid no-explanation answer"
      ensure (roots.length == 1) "surplus no-explanation query"
      ensure (!(lookup empty)) "no-explanation claim has a counterexample"
  else
    throw "empty machine"

def checkLine (line : String) : Except String String := do
  let json ← Json.parse line
  let record : Record ← fromJson? json
  checkRecord record
  pure record.item.id

end Trace2.Runtime
