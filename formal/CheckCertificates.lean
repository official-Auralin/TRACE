import Trace2.Runtime

/-- Read JSONL records, rejecting at the first invalid certificate. -/
def main (args : List String) : IO UInt32 := do
  let input ← match args with
    | ["-"] | [] => IO.getStdin
    | [path] => pure (IO.FS.Stream.ofHandle (← IO.FS.Handle.mk path .read))
    | _ => throw (IO.userError "usage: CheckCertificates.lean [JSONL_PATH|-]")
  let mut count := 0
  repeat
    let line ← input.getLine
    if line.isEmpty then break
    if !line.trim.isEmpty then
      match Trace2.Runtime.checkLine line with
      | .error reason =>
        IO.eprintln s!"FAIL record {count+1}: {reason}"
        return 1
      | .ok _ => count := count+1
  if count == 0 then
    IO.eprintln "FAIL: no certificate records"
    return 1
  IO.println s!"\{\"status\":\"PASS\",\"certificates_checked\":{count},\"checker\":\"Lean 4.24.0 Trace2.Runtime\"}"
  return 0
