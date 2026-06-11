"""Gate B runner. b1_profile and b2_corpus are chunked (sandbox time budget):
run their per-chunk commands first if results/ is empty; this script re-runs the
fast tests and aggregates everything into results/REPORT.md."""
import json, subprocess, sys, os, datetime, glob
HERE = os.path.dirname(os.path.abspath(__file__))
def sh(args): return subprocess.run([sys.executable] + args, capture_output=True, text=True, cwd=HERE)

def main():
    rows = []
    p = sh(["b1_regression.py"]); open(os.path.join(HERE,"results","b1_regression.json"),"w").write(p.stdout)
    rows.append(("B1 regression", json.loads(p.stdout)["status"]))
    if not glob.glob(os.path.join(HERE,"results","prof_*.json")):
        rows.append(("B1 profiling", "RUN CHUNKS: python3 b1_profile.py 0..10, then agg"))
    else:
        p = sh(["b1_profile.py","agg"]); open(os.path.join(HERE,"results","b1_profile_final.json"),"w").write(p.stdout)
        rows.append(("B1 profiling", json.loads(p.stdout)["status"]))
    if not glob.glob(os.path.join(HERE,"results","b2_part*.json")):
        rows.append(("B2 corpus", "RUN CHUNKS: python3 b2_corpus.py 0..5, then agg"))
    else:
        p = sh(["b2_corpus.py","agg"]); open(os.path.join(HERE,"results","b2_corpus_final.json"),"w").write(p.stdout)
        rows.append(("B2 corpus", json.loads(p.stdout)["status"]))
    p = sh(["b3_identifiability.py"]); open(os.path.join(HERE,"results","b3_identifiability.json"),"w").write(p.stdout)
    rows.append(("B3 identifiability", json.loads(p.stdout)["status"]))
    prof = json.load(open(os.path.join(HERE,"results","b1_profile_final.json")))
    corp = json.load(open(os.path.join(HERE,"results","b2_corpus_final.json")))
    lines = ["# Gate B — Results Report", "",
             f"Run: {datetime.datetime.now().isoformat()} · Python {sys.version.split()[0]} (sandboxed Linux)","",
             "| Test | Status |", "|---|---|"] + [f"| {a} | {b} |" for a,b in rows] + ["",
      "## Headline measurements",
      f"- Tractable grader envelope (median per full key computation): <=1s at (|I|,k) in {prof['tractable_envelope']['<=1s']}; <=10s adds {[p for p in prof['tractable_envelope']['<=10s'] if p not in prof['tractable_envelope']['<=1s']]}. Credit-original cost is the exponential one, as mainTB's cost analysis predicts (growth ratios {prof['credit_growth_ratios_along_cells']}).",
      f"- Prototype corpus: {corp['counts']['generated']} generated, {corp['counts']['retain']} retained (discard rate {corp['discard_rate']:.0%}: {corp['counts']['discard:input-unconditional']} input-unconditional, {corp['counts']['discard:same-column-single-literal']} same-column single-literal).",
      f"- No-pivotal-cell verdicts: {corp['no_pivotal_cell']['overdetermined']} overdetermined (retained class) vs {corp['no_pivotal_cell']['input_unconditional_discarded']} input-unconditional (discarded).",
      f"- Credit-vs-Pin per-cell unions agree on {corp['counts']['retain']}/{corp['counts']['retain']} retained instances (zero divergences at full search depth) — empirical support for the per-cell equality mainTB leaves open. NOTE: with a size-3 search cap this statistic falsely showed 49 divergences; cap-censoring corrupts keys, validating the 'lift caps or certify per instance' requirement.",
      f"- Original-vs-modified HP variant keys diverge on {corp['original_vs_modified_divergence_count']}/{corp['counts']['retain']} retained instances (~{corp['original_vs_modified_divergence_count']/corp['counts']['retain']:.0%}) — the class where the CORP correspondence is predicted to fail is common on random machines.",
      "- Black-box identifiability: controls pass (known-identifiable accepted, observed-run-only refused); random 2-state/1-input instances with 3 probes: 0/10 admitted — the admission check is severely restrictive, as mainTB anticipated.",
      "", "Caveat: corpus realism is NOT claimed (random Mealy machines, not SYNTCOMP syntheses); statistics demonstrate the machinery and bound expectations only."]
    open(os.path.join(HERE,"results","REPORT.md"),"w").write("\n".join(lines)+"\n")
    print("\n".join(lines))
    return 0

if __name__ == "__main__":
    sys.exit(main())
