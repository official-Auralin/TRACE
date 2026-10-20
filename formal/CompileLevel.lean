import Trace2.CompilerRuntime

/-- Stream independent JSONL machines; one board per line, no corpus buffering. -/
def main (args : List String) : IO UInt32 := do
  if args != [] then
    IO.eprintln "usage: trace-compile < machines.jsonl > boards.jsonl"
    return 1
  let stdin ← IO.getStdin
  let stdout ← IO.getStdout
  let mut count := 0
  repeat
    let line ← stdin.getLine
    if line.isEmpty then break
    if !line.trim.isEmpty then
      match Trace2.CompilerRuntime.compileLine line with
      | .error reason =>
        IO.eprintln s!"FAIL record {count+1}: {reason}"
        return 1
      | .ok board =>
        stdout.putStrLn board.compress
        stdout.flush
        count := count+1
  if count == 0 then
    IO.eprintln "FAIL: no machine records"
    return 1
  return 0
