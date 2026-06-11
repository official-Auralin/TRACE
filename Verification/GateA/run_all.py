"""Gate A runner: executes A1-A4, writes results/*.json and results/REPORT.md."""
import json, subprocess, sys, os, datetime
HERE = os.path.dirname(os.path.abspath(__file__))
TESTS = [("A1", "a1_audit.py", "a1_audit.json"),
         ("A2i", "a2_oracle_check.py", "a2_oracle.json"),
         ("A2ii", "a2_corp_compare.py", "a2_corp.json"),
         ("A3", "a3_variants.py", "a3_variants.json"),
         ("A4", "a4_window.py", "a4_window.json")]

def main():
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    rows, allpass = [], True
    for gid, script, outf in TESTS:
        p = subprocess.run([sys.executable, os.path.join(HERE, script)],
                           capture_output=True, text=True)
        path = os.path.join(HERE, "results", outf)
        open(path, "w").write(p.stdout)
        try: status = json.loads(p.stdout).get("status", "ERROR")
        except Exception: status = "ERROR: " + p.stderr[:200]
        hard_fail = p.returncode != 0
        allpass &= not hard_fail
        rows.append((gid, script, status, p.returncode))
    lines = ["# Gate A — Results Report", "",
             f"Run: {datetime.datetime.now().isoformat()}  ·  Python {sys.version.split()[0]}", "",
             "| Gate | Test | Status | Exit |", "|---|---|---|---|"]
    for gid, script, status, rc in rows:
        lines.append(f"| {gid} | `{script}` | {status} | {rc} |")
    lines += ["", "## Pass/fail conditions (see README.md)",
              "- A1: PASS iff every labelled fixture (1 positive, 4 negative controls) is classified",
              "  correctly on all of F1-operational/F2/F3. External corpus rates reported when present.",
              "- A2i: PASS iff oracle output == mainTB's published answers, 5 puzzles x 4 causal objects.",
              "- A2ii: PASS only on real TempoBench keys; otherwise BLOCKED-EXTERNAL (recorded).",
              "- A3: PASS iff variants agree exactly on non-overdetermined puzzles, diverge to the",
              "  joint pair on overdetermined ones, and dual-acceptance = union with no supersets.",
              "- A4: PASS iff same-step relevance detector flags exactly P4; Mealy rendering covers",
              "  all cause cells; Moore coverage holds iff Moore-safe.",
              "", "Evidence documents: A2_definitional_note.md, A3_decision_record.md."]
    open(os.path.join(HERE, "results", "REPORT.md"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0 if allpass else 1

if __name__ == "__main__":
    sys.exit(main())
