"""One release gate: formal build, focused tests, concrete package and browser interpreter.

--deep adds the exhaustive mathematical regression suite and small-window audit.
--verbose changes logs only. --output / --emit-certificates persist evidence.
No participant outcomes or empirical validity are fabricated by this command.
"""
import argparse,hashlib,json,subprocess,sys,time,unittest
from pathlib import Path
from .paths import ROOT
from .validate import validate,write_report
from .runtime import load_package

DEEP_TESTS={'test_all_32907_true_actual_boolean_functions_through_four_cells',
            'test_explicit_parity_game_all_candidates_through_three_cells'}


def flattened(suite):
    for entry in suite:
        if isinstance(entry,unittest.TestSuite):yield from flattened(entry)
        else:yield entry


def verify_browser_paths(dataset):
    _,body,_,_=load_package(dataset)
    # A process per bounded batch avoids retaining the complete corpus in memory.
    totals={'status':'PASS','items':0,'exhaustive_words':0,'sampled_words':0};batch=[]
    def run(items):
        result=subprocess.run(['node',str(ROOT/'tests/general_board_paths.mjs')],
            input=json.dumps(items),text=True,capture_output=True,cwd=ROOT)
        if result.returncode:raise ValueError(result.stdout+result.stderr)
        report=json.loads(result.stdout)
        if report['status']!='PASS':raise ValueError('Browser interpreter check failed')
        for key in ('items','exhaustive_words','sampled_words'):totals[key]+=report[key]
    for item in body['items'].values():
        batch.append(item)
        if len(batch)==16:run(batch);batch=[]
    if batch:run(batch)
    totals['scope']='Actual browser semantic interpreter and terminal display interpreter vs independent table execution: exhaustive through 12 cells; four stated probes above 12. Rendering tested separately.'
    return totals


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dataset');p.add_argument('--deep',action='store_true');p.add_argument('--verbose',action='store_true')
    p.add_argument('--output');p.add_argument('--emit-certificates')
    a=p.parse_args();started=time.time()
    if not __debug__:raise SystemExit('Do not disable Python assertions during verification')
    print('Building and auditing Lean proofs...',flush=True)
    formal_run=subprocess.run(['bash','formal/verify.sh'],cwd=ROOT,text=True,capture_output=not a.verbose)
    if formal_run.returncode:
        if not a.verbose:print(formal_run.stdout+formal_run.stderr,file=sys.stderr)
        raise SystemExit(formal_run.returncode)
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),top_level_dir=str(ROOT))
    selected=unittest.TestSuite(t for t in flattened(suite) if a.deep or t._testMethodName not in DEEP_TESTS)
    count=selected.countTestCases()
    result=unittest.TextTestRunner(verbosity=2 if a.verbose else 1).run(selected)
    if not result.wasSuccessful():raise SystemExit(1)
    print('Checking package and browser execution...',flush=True)
    report=validate(a.dataset,8 if a.deep else 0,a.emit_certificates,a.verbose)
    browser=verify_browser_paths(a.dataset)
    sources={str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest()
        for folder,pattern in (('benchmark','*.py'),('adapters','*.py'),('web','*'),('tests','*.py'),('tests','*.mjs'))
        for path in sorted((ROOT/folder).glob(pattern)) if path.is_file()}
    final={'status':'PASS','dataset_sha256':report['dataset_sha256'],'python_tests':count,
        'deep':a.deep,'package':report,'browser_interpreter':browser,
        'formal_report_sha256':hashlib.sha256((ROOT/'formal/proof_checks.json').read_bytes()).hexdigest(),
        'source_sha256':sources,'elapsed_seconds':time.time()-started,
        'scope':'Computational/formal/synthetic checks only; visual usability, human difficulty and live-model performance remain empirical gates.'}
    if a.output:write_report(final,a.output)
    print(json.dumps({k:v for k,v in final.items() if k!='source_sha256'},indent=2))
if __name__=='__main__':main()
