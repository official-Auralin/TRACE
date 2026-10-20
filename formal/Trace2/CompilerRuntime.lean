import Trace2.Compiler
import Trace2.Runtime

namespace Trace2.CompilerRuntime
open Lean
open Trace2.Runtime

structure CompileInput where
  machine : RawMachine
  observed : Array (Array Nat)
  target_step : Nat
  deriving FromJson

def treeJson : SwitchTree Nat (Nat × Bool) → Json
  | .leaf (q, output) => Json.mkObj [
      ("kind", .str "output"), ("value", toJson (if output then (1 : Nat) else 0)),
      ("next", toJson q)]
  | .switch cell zero one => Json.mkObj [
      ("kind", .str "switch"), ("cell", toJson cell),
      ("zero", treeJson zero), ("one", treeJson one)]

def outcomeTreeJson : SwitchTree Nat Bool → Json
  | .leaf output => Json.mkObj [
      ("kind", .str "outcome"), ("value", toJson (if output then (1 : Nat) else 0))]
  | .switch cell zero one => Json.mkObj [
      ("kind", .str "switch"), ("cell", toJson cell),
      ("zero", outcomeTreeJson zero), ("one", outcomeTreeJson one)]

/-- Validation/serialization adapter; the tree builder called here is the same
definition whose arbitrary finite semantics are proved in Compiler.lean. -/
def compileInput (record : CompileInput) : Except String Json := do
  let raw := record.machine
  let m := raw.inputs.size
  let h := record.target_step+1
  ensure (raw.states > 0 && m > 0) "machine dimensions must be positive"
  ensure (unique raw.inputs) "duplicate input names"
  ensure (raw.inputs.all (fun name => !name.isEmpty)) "empty input name"
  ensure (raw.initial < raw.states && raw.transitions.size == raw.states)
    "invalid machine state bounds"
  ensure (raw.transitions.all (fun row => row.size == 2^m &&
    row.all (fun edge => edge.next < raw.states && edge.output ≤ 1)))
    "invalid total binary machine"
  ensure (h ≤ record.observed.size && bitRows record.observed record.observed.size m)
    "invalid observed inputs or target step"
  let edge := fun (q : Nat) (v : Valuation m) =>
    ((raw.transitions[q]?.getD #[])[valuationCode v]?.getD default)
  let M : Machine Nat (Valuation m) := {
    initial := raw.initial
    step := fun q v => (edge q v).next
    emit := fun q v => (edge q v).output == 1 }
  let actual := inputWord record.observed m
  let mut state := raw.initial
  let mut output := false
  for t in List.range h do
    output := M.emit state (actual t)
    state := M.step state (actual t)
  ensure output "target is not actually positive"
  let layers := (List.range h).map (fun t => toJson ((List.range raw.states).map
    (fun q => treeJson (compileRoundReduced M t q))))
  let terminal := (List.range raw.states).map
    (fun q => outcomeTreeJson (compileTerminal M record.target_step q))
  pure (Json.mkObj [
    ("version", .str "trace.board.v2"), ("initial", toJson raw.initial),
    ("states", toJson raw.states), ("inputs", toJson m), ("horizon", toJson h),
    ("layers", toJson layers),
    ("display", Json.mkObj [("version", .str "trace.display.v1"),
      ("terminal", toJson terminal)])])

def compileLine (line : String) : Except String Json := do
  let json ← Json.parse line
  let record : CompileInput ← fromJson? json
  compileInput record

end Trace2.CompilerRuntime
