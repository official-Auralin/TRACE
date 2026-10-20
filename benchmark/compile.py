"""Import machine/trace/target JSONL and build a deterministic certified package.

No dataset generation is called here. Detailed certificates are checked in
memory and saved only with --emit-certificates. Console verbosity has no effect
on validation. The Lean constructor, not a Python substitute, creates each tree.
"""
import argparse
from contextlib import AbstractContextManager
import hashlib
import json
import os
from pathlib import Path
import select
import shutil
import subprocess
import sys

from .core import DATA_VERSION,SEMANTICS,canonical,digest,simulate,validate_item,validate_machine
from .game import make_certificate,verify_certificate
from .level import DISPLAY_VERSION,decorate

ROOT=Path(__file__).resolve().parents[1]
COMPILER_VERSION='trace.mealy-compiler.v2'


def lean_executable():
    configured=os.environ.get('LEAN_BIN')
    path=Path(configured)/'lean' if configured else Path('/private/tmp/lean-4.24.0-darwin_aarch64/bin/lean')
    if not path.is_file():
        found=shutil.which('lean')
        if not found:raise RuntimeError('Install pinned Lean 4.24.0 or set LEAN_BIN; certification was not skipped')
        path=Path(found)
    return path


def file_sha256(path):
    result=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):result.update(block)
    return result.hexdigest()


def formal_identity():
    report_path=ROOT/'formal/proof_checks.json'
    if not report_path.is_file():raise RuntimeError('Run bash formal/verify.sh before compiling tasks')
    report=json.loads(report_path.read_text())
    if report.get('status')!='PASS':raise RuntimeError('Formal source has no passing build')
    for name,expected in report['source_sha256'].items():
        path=ROOT/'formal'/name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
            raise RuntimeError('Formal source changed; run bash formal/verify.sh before compiling tasks')
    if 'Trace2/Compiler.lean' not in report['source_sha256']:
        raise RuntimeError('The general compiler has not passed the formal build')
    for name,expected in report.get('executable_sha256',{}).items():
        path=ROOT/'formal/.build'/name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
            raise RuntimeError('Formal executable changed; run bash formal/verify.sh')
    return {'source_sha256':report['source_sha256'],'lean_version':report['lean_version']}


def normalize(record):
    if not isinstance(record,dict):raise ValueError('each dataset record must be an object')
    allowed={'id','split','family','machine','observed','target_step','observed_outputs','observed_states','provenance'}
    unknown=set(record)-allowed
    if unknown:raise ValueError('unsupported dataset fields (no target or constraint is silently dropped): '+', '.join(sorted(unknown)))
    if not {'machine','observed','target_step'} <= record.keys():raise ValueError('record requires machine, observed and target_step')
    machine=record['machine'];validate_machine(machine)
    if set(machine)!={'inputs','states','initial','transitions'}:
        raise ValueError('source machine supports only inputs, states, initial and transitions; translate other semantics explicitly')
    observed=record['observed'];k=record['target_step']
    if type(k) is not int or k<0 or not isinstance(observed,list) or k>=len(observed):
        raise ValueError('target must lie within the finite observed trace')
    actual=simulate(machine,observed)
    if 'observed_outputs' in record and record['observed_outputs']!=actual['outputs']:
        raise ValueError('supplied observed outputs disagree with source machine')
    if 'observed_states' in record and record['observed_states']!=actual['states']:
        raise ValueError('supplied observed states disagree with source machine')
    item={'machine':{key:machine[key] for key in ('inputs','states','initial','transitions')},
          'observed':observed[:k+1],'target_step':k,'semantics':dict(SEMANTICS)}
    validate_item(item)
    item['id']=record.get('id','mealy-'+digest(item)[:20])
    if not isinstance(item['id'],str) or not item['id']:raise ValueError('nonempty string item ID required')
    item['split']=record.get('split','test');item['family']=record.get('family','external')
    if not isinstance(item['split'],str) or not isinstance(item['family'],str) or not item['family']:
        raise ValueError('split and family must be nonempty strings')
    if item['split'] not in ('tutorial','pilot','development','test'):raise ValueError('unknown split')
    return item


class LeanProcess(AbstractContextManager):
    def __init__(self, cli, timeout=None):
        self.timeout=timeout
        env=dict(os.environ,LEAN_PATH=str(ROOT/'formal/.build'))
        native=ROOT/'formal/.build'/('trace-compile' if cli=='CompileLevel.lean' else 'trace-check')
        command=[str(native)] if native.is_file() else [str(lean_executable()),'--run',str(ROOT/'formal'/cli)]
        self.process=subprocess.Popen(command,
            cwd=ROOT,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
    def request(self, value):
        p=self.process
        p.stdin.write(canonical(value)+'\n');p.stdin.flush()
        if self.timeout is not None and not select.select([p.stdout],[],[],self.timeout)[0]:
            p.kill();raise TimeoutError('operator computation budget exhausted; result is uncertified')
        line=p.stdout.readline()
        if not line:
            error=p.stderr.read();p.wait()
            if p.returncode<0 or 'stack overflow' in error.lower() or 'out of memory' in error.lower():
                raise MemoryError('Lean process exhausted resources or was interrupted: '+error.strip())
            raise ValueError('Lean rejected input or failed: '+error.strip())
        result=json.loads(line)
        if isinstance(result,dict) and result.get('status')=='ERROR':raise ValueError(str(result))
        return result
    def __exit__(self,*args):
        p=self.process
        if p.poll() is None:
            p.stdin.close()
            try:p.wait(timeout=10)
            except subprocess.TimeoutExpired:p.kill();p.wait()
        p.stdout.close();p.stderr.close()


def compile_item(record, compiler):
    item=normalize(record)
    board=compiler.request(item)
    if not isinstance(board,dict) or not isinstance(board.get('display'),dict) or board['display'].get('version')!=DISPLAY_VERSION:
        raise ValueError('Lean constructor must emit the proved terminal display; rebuild the pinned compiler')
    item['board']=decorate(board,item['observed'],item['machine']['inputs'])
    replay=validate_item(item)
    item.update(observed_outputs=replay['outputs'],observed_states=replay['states'])
    return item


def default_forms(items):
    forms={}
    for split in ('tutorial','pilot','development','test'):
        chosen=[item['id'] for item in items if item['split']==split]
        for offset in range(0,len(chosen),4):
            forms[f'{split}-{offset//4+1:02d}']={'split':split,'item_ids':chosen[offset:offset+4],
                'human_panel':split=='test' and offset<64}
    return forms


def compile_dataset(source, output, emit_certificates=None, verbose=False, timeout=None, certify=True):
    if not certify:raise ValueError('uncertified package publication is not supported')
    formal=formal_identity();source=Path(source);output=Path(output)
    if output.exists() and any(output.iterdir()):raise ValueError('output directory must be absent or empty; frozen packages are never overwritten')
    items=[];identities=set();evidence=[]
    cert_path=Path(emit_certificates) if emit_certificates else None
    if cert_path:
        if cert_path.exists():raise ValueError('certificate output exists; choose a new artifact path')
        if output.resolve() in cert_path.resolve().parents:raise ValueError('store private certificates outside the playable package')
        cert_path.parent.mkdir(parents=True,exist_ok=True)
    # The certificate runner consumes JSONL until EOF and gives a single summary.
    # Stream to a temporary private file rather than retaining all proof tables.
    import tempfile
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.trace-build-',dir=output.parent) as temporary, LeanProcess('CompileLevel.lean',timeout) as compiler:
        cert_file=Path(temporary)/'certificates.jsonl'
        package=Path(temporary)/'package';package.mkdir()
        with source.open() as rows,cert_file.open('w') as certificates,(package/'items.jsonl').open('wb') as tasks:
            for number,line in enumerate(rows,1):
                if not line.strip():continue
                record=json.loads(line);item=compile_item(record,compiler)
                if item['id'] in identities:raise ValueError('duplicate item ID: '+item['id'])
                identities.add(item['id'])
                cert=make_certificate(item);verify_certificate(item,cert)
                from .core import public_item
                certificates.write(canonical({'item':public_item(item),'certificate':cert})+'\n')
                evidence.append({'id':item['id'],'source_sha256':digest(record),'task_sha256':digest(public_item(item))})
                data=(canonical(item)+'\n').encode('ascii');offset=tasks.tell();tasks.write(data)
                items.append({'id':item['id'],'path':'items.jsonl','offset':offset,'length':len(data),
                    'sha256':digest(item),'split':item['split'],'family':item['family']})
                if verbose:print(f'Compiled and locally checked {item["id"]}',file=sys.stderr)
        if not items:raise ValueError('empty dataset')
        env=dict(os.environ,LEAN_PATH=str(ROOT/'formal/.build'))
        native=ROOT/'formal/.build/trace-check'
        command=[str(native),str(cert_file)] if native.is_file() else [str(lean_executable()),'--run',str(ROOT/'formal/CheckCertificates.lean'),str(cert_file)]
        result=subprocess.run(command,
            cwd=ROOT,env=env,text=True,capture_output=True,timeout=timeout)
        if result.returncode<0:raise MemoryError('certificate checker was interrupted; package remains uncertified')
        if result.returncode:raise ValueError('Lean certificate check failed: '+result.stdout+result.stderr)
        verdict=json.loads(result.stdout.strip().splitlines()[-1])
        if verdict.get('status')!='PASS' or verdict.get('certificates_checked')!=len(items):
            raise ValueError('incomplete certificate check')
        if cert_path:shutil.copyfile(cert_file,cert_path)
        body={'schema_version':DATA_VERSION,'semantics':dict(SEMANTICS),'item_index':items}
        forms=default_forms(items)
        counts={split:sum(i['split']==split for i in items) for split in ('tutorial','pilot','development','test')}
        panel=[name for name,form in forms.items() if form['human_panel']]
        manifest={'schema_version':DATA_VERSION,'dataset_sha256':digest(body),'forms_sha256':digest(forms),
            'n_items':len(items),'counts_by_split':counts,'human_panel_form_ids':panel,
            'human_panel_items':sum(len(forms[f]['item_ids']) for f in panel),'form_size':4,
            'semantics':dict(SEMANTICS),'compiler_version':COMPILER_VERSION,
            'source_file_sha256':file_sha256(source),
            'compiler_formal':formal,'items':evidence,'certification':{'status':'PASS',
            'canonical_answers_checked':len(items),'all_answers_enumerated':False,
            'scope':'Proved general Lean construction; independent local transition binding; Python and Lean canonical G/P certificate checks. Parser, serialization, executable platform and UI remain trusted/tested.'}}
        for name,obj in (('dataset.json',body),('forms.json',forms),('manifest.json',manifest)):
            (package/name).write_text(canonical(obj)+'\n')
        if output.exists():output.rmdir() # only the empty directory admitted above
        package.rename(output)
    return manifest


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',help='JSONL machine/trace/target records')
    p.add_argument('--output',required=True,help='new package directory')
    p.add_argument('--emit-certificates',metavar='PATH')
    p.add_argument('--verbose',action='store_true')
    p.add_argument('--timeout',type=float,help='optional operator time budget in seconds; never a semantic bound')
    args=p.parse_args()
    try:result=compile_dataset(args.source,args.output,args.emit_certificates,args.verbose,args.timeout)
    except (ValueError,RuntimeError,TimeoutError,subprocess.TimeoutExpired,MemoryError) as error:
        print(json.dumps({'status':'INCOMPLETE' if isinstance(error,(TimeoutError,subprocess.TimeoutExpired,MemoryError)) else 'ERROR','error':str(error)}),file=sys.stderr);raise SystemExit(1)
    print(json.dumps({'status':'PASS','items':result['n_items'],'dataset_sha256':result['dataset_sha256'],'output':args.output}))

if __name__=='__main__':main()
