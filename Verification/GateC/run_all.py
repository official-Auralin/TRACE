import json, subprocess, sys, os, datetime
HERE = os.path.dirname(os.path.abspath(__file__))
def main():
    p = subprocess.run([sys.executable, os.path.join(HERE, "c1_parity.py")], capture_output=True, text=True)
    open(os.path.join(HERE, "results", "c1_parity.json"), "w").write(p.stdout)
    s1 = json.loads(p.stdout)["status"]
    p2 = subprocess.run([sys.executable, os.path.join(HERE, "c3_materials.py")], capture_output=True, text=True)
    lines = ["# Gate C — Results Report", "",
        f"Run: {datetime.datetime.now().isoformat()} · Python {sys.version.split()[0]}", "",
        "| Item | Status |", "|---|---|",
        f"| C1 four-consumer parity audit | {s1} |",
        "| C2 white-box budget | DECIDED (C2_whitebox_budget_decision.md) |",
        f"| C3 modality protocol + materials | {'EMITTED — ' + p2.stdout.strip() if p2.returncode==0 else 'ERROR'} |",
        "", "C1 checks, per instance (9 instances: 5 worked puzzles, the real TempoBench",
        "artifact, 3 generated): observation equivalence (board is a pure function of the",
        "agent observation AND behaviorally identical on every assignment); submission",
        "round-trip (every possible board submission ↔ agent JSON, identical verdicts —",
        "exhaustive, and checked PER DECLARED VARIANT POLICY: original, modified, and the",
        "legacy dual union, so the parity proven is the parity each shipped corpus grades",
        "under); probe parity (board walk == HOA simulation on random probes);",
        "candidate-space safety (every human-unreachable cell proven effect-irrelevant in",
        "every context, so no correct answer is human-inexpressible). Candidate-space",
        "safety (P_CAND) is release-blocking: future generator changes must keep it green."]
    open(os.path.join(HERE, "results", "REPORT.md"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines)); return 0 if s1 == "PASS" else 1
if __name__ == "__main__":
    sys.exit(main())
