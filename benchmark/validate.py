"""Package validation; optional finite exhaustive audits, never a size validity cap."""
from collections import Counter
import argparse,hashlib,json,os,subprocess,tempfile
from pathlib import Path
from .core import assignment,cell_count,cells,digest,grade,public_item,validate_item
from .game import make_certificate,solve,verify_certificate
from .level import execute
from .paths import ROOT
from .reference import direct_item_table,direct_key,table_execute
from .runtime import load_package


def validate(dataset=None,exhaustive_max_cells=0,emit_certificates=None,verbose=False):
    directory,body,manifest,forms=load_package(dataset)
    words=candidates=answer_checks=exhaustive_items=terminal_cases=0;counts=Counter();identities=set();dimensions=Counter();duplicates=0
    if emit_certificates and Path(emit_certificates).exists():raise ValueError('certificate output exists; use a new path')
    with tempfile.TemporaryDirectory(prefix='trace-audit-') as temporary:
        path=Path(temporary)/'certificates.jsonl'
        with path.open('w') as output:
            for item in body['items'].values():
                validate_item(item);counts[item['split']]+=1
                terminal_cases+=item['machine']['states']*(1<<len(item['machine']['inputs']))
                identity=digest(item['machine'])
                if identity in identities:duplicates+=1
                identities.add(identity)
                n=cell_count(item);dimensions[(item['machine']['states'],len(item['machine']['inputs']),item['target_step']+1)]+=1
                selected=solve(item)
                answer={'verdict':'no_explanation'} if selected is None else {'cells':selected}
                if not grade(item,answer)['correct']:raise ValueError('Solver/grader disagreement')
                cert=make_certificate(item,selected);verify_certificate(item,cert);answer_checks+=1
                output.write(json.dumps({'item':public_item(item),'certificate':cert},sort_keys=True,separators=(',',':'))+'\n')
                # Word/candidate enumeration is an explicitly bounded audit,
                # not a requirement of validity, compilation, or grading.
                if n<=exhaustive_max_cells:
                    exhaustive_items+=1
                    m=len(item['machine']['inputs']);h=item['target_step']+1
                    for mask in range(1<<n):
                        word=assignment(mask,m,h);expected=table_execute(item['machine'],word)
                        actual=execute(item['board'],word)
                        if any(actual[k]!=expected[k] for k in ('outputs','states')):raise ValueError('Independent word disagreement')
                        words+=1
                    accepted=direct_key(direct_item_table(item))['explanation']
                    for mask in range(1<<n):
                        selected=cells(mask,n)
                        if grade(item,{'cells':selected})['correct']!=(selected in accepted):raise ValueError('Direct quantifier grading disagreement')
                        candidates+=1
                if verbose:print('Validated '+item['id'],flush=True)
        checked=subprocess.run([str(ROOT/'formal/.build/trace-check'),str(path)],cwd=ROOT,capture_output=True,text=True)
        if checked.returncode:raise ValueError('Lean concrete-data checking failed: '+checked.stdout+checked.stderr)
        result=json.loads(checked.stdout)
        if result.get('status')!='PASS' or result.get('certificates_checked')!=answer_checks:raise ValueError('Incomplete Lean certificate run')
        if emit_certificates:
            import shutil
            dest=Path(emit_certificates);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,dest)
    if dict(counts)!= {k:v for k,v in manifest['counts_by_split'].items() if v}:raise ValueError('Split counts disagree')
    assigned=[iid for form in forms.values() for iid in form['item_ids']]
    actual_panel={iid for form in forms.values() if form.get('human_panel') for iid in form['item_ids']}
    if manifest.get('n_items',len(body['items']))!=len(body['items']):raise ValueError('Item count disagrees with manifest')
    if manifest.get('human_panel_items',len(actual_panel))!=len(actual_panel):raise ValueError('Panel count disagrees with manifest')
    return {'status':'PASS','dataset_sha256':manifest['dataset_sha256'],'items':len(body['items']),
        'counts_by_split':dict(counts),'repeated_exact_source_machines':duplicates,
        'forms_partition_items':Counter(assigned)==Counter(iter(body['items'])),
        'source_machine_uniqueness':'reported for exact labeled transition tables only; multiple traces of one machine are permitted',
        'dimensions':[{'states':q,'inputs':m,'horizon':h,'items':count} for (q,m,h),count in sorted(dimensions.items())],
        'terminal_state_input_outputs_checked':terminal_cases,
        'terminal_display':'Canonical output-only projection checked for every state and input, including unobserved alternatives.',
        'complete_input_sequences_checked':words,'scored_subsets_checked':candidates,
        'exhaustive_max_cells':exhaustive_max_cells,'canonical_certificates_checked':answer_checks,
        'exhaustive_answer_families_checked':exhaustive_items,'human_panel_items':len(actual_panel),
        'scope':'All compiled transition trees locally bound to source tables; canonical answer certificates checked in Python and Lean. Exhaustive counts apply only to stated small windows. No human/model findings or empirical difficulty calibration.'}


def write_report(report,path):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--dataset');p.add_argument('--output')
    p.add_argument('--exhaustive-max-cells',type=int,default=0);p.add_argument('--emit-certificates');p.add_argument('--verbose',action='store_true')
    a=p.parse_args();report=validate(a.dataset,a.exhaustive_max_cells,a.emit_certificates,a.verbose)
    if a.output:write_report(report,a.output)
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
