"""Computational baselines or isolated, timed model adapters through the common StudyStore.
Adapter stdin/stdout: newline JSON. Receive {observation:...}; emit {answer:{cells:[]}}
or {probe:{changes:{"0":1}}}; receive {probe_result:...}. No answer repair/retries.
"""
import argparse,hashlib,json,os,random,selectors,shlex,statistics,subprocess,tempfile,time,uuid
from pathlib import Path
from .core import PROTOCOL_VERSION,canonical,digest,grade,public_item,simulate
from .game import solve
from .paths import ROOT
from .runtime import StudyStore,StudyError,load_package

STRATEGIES=('random','all','none','latest','pivots','solver')
def baseline_answer(item,strategy,rng):
    n=(item['target_step']+1)*len(item['machine']['inputs'])
    visible=sorted(switch['cell'] for switch in item['board']['switches']) if 'board' in item else list(range(n))
    if strategy=='random':selected=[c for c in visible if rng.random()<0.5]
    elif strategy=='all':selected=visible
    elif strategy=='none':selected=[]
    elif strategy=='latest':selected=[c for c in visible if c>=n-len(item['machine']['inputs'])]
    elif strategy=='pivots':
        selected=[];ni=len(item['machine']['inputs'])
        for c in range(n):
            changed=[row[:] for row in item['observed']];changed[c//ni][c%ni]^=1
            if simulate(item['machine'],changed)['outputs'][item['target_step']]==0:selected.append(c)
    elif strategy=='solver':
        selected=solve(public_item(item))
        if selected is None:return {'verdict':'no_explanation'}
    else:raise ValueError(strategy)
    return {'cells':selected}

def baselines(output,split='test',repetitions=5,seed=1729,strategies=STRATEGIES,dataset=None):
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    if output.exists():raise ValueError('Use a new raw output path')
    if repetitions<1:raise ValueError('Repetitions must be positive')
    _,body,manifest,forms=load_package(dataset)
    items=body['items']
    item_ids=[iid for iid,entry in items.index.items() if entry['split']==split]
    if not item_ids:raise ValueError('No items selected')
    membership={i:(name,f['item_ids']) for name,f in forms.items() for i in f['item_ids']}
    if any(iid not in membership for iid in item_ids):raise ValueError('Every evaluated item must be assigned to a form')
    systems={};raw_hash=hashlib.sha256()
    with output.open('xb') as stream:
        for strategy in strategies:
            rng=random.Random(seed);times=[];totals={key:0 for key in ('correct','guarantee','prevention','minimality')};count=0
            for rep in range(repetitions if strategy=='random' else 1):
                for iid in item_ids:
                    item=items[iid];form,ids=membership[iid]
                    before=time.perf_counter();answer=baseline_answer(item,strategy,rng);elapsed=(time.perf_counter()-before)*1000
                    score=grade(item,answer,'explanation')
                    row=dict(record_type='trial',schema_version='trace.trial.v2',protocol_version=PROTOCOL_VERSION,
                      dataset_sha256=manifest['dataset_sha256'],forms_sha256=manifest['forms_sha256'],session_id=f'baseline-{strategy}-{form}-{rep}',participant_id=f'{strategy}-{rep}',
                      cohort='baseline',condition='reasoning',form_id=form,form_item_ids=ids,mode='explanation',item_id=iid,family=item.get('family','external'),split=split,
                      agent_metadata={'system_id':strategy,'seed':seed,'repetition':rep,'regime':'computational baseline'},
                      limits={'attempts':1,'seconds':None,'probes':0},
                      cell_count=(item['target_step']+1)*len(item['machine']['inputs']),status='submitted',response=answer,
                      duration_ms=elapsed,probes_used=0,attempts_used=1,reason=None,**score)
                    raw=(canonical(row)+'\n').encode();stream.write(raw);raw_hash.update(raw)
                    count+=1;times.append(elapsed/1000)
                    for key in totals:totals[key]+=score[key]
            systems[strategy]={'accuracy':totals['correct']/count,
                **{key+'_rate':totals[key]/count for key in ('guarantee','prevention','minimality')},
                'trials':count,'items':len(item_ids),'median_seconds':statistics.median(times)}
    summary={'dataset_sha256':manifest['dataset_sha256'],'split':split,'systems':systems,'seed':seed,
             'random_expected_exact_accuracy':None,
             'analytic_chance_status':'Not computed by the production runner; exact answer-family counting is an optional exhaustive audit.',
             'selection_domain':'Uniform-subset and all-switch baselines select the public board.switches controls. Grading quantifies over the full input domain.',
             'raw_sha256':raw_hash.hexdigest(),'scope':'Measured non-learning finite G/P baselines; no human or language-model trials.',
             'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ('benchmark/core.py','benchmark/game.py','benchmark/boards.py','benchmark/evaluate.py')}}
    output.with_name(output.stem.replace('_trials','')+'_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    return summary

class AdapterTimeout(Exception):pass

def run_adapter(store,token,observation,command,transcript,max_message_bytes=None):
    """The trusted adapter sees public state only. The remote model has no repository tool."""
    with tempfile.TemporaryDirectory(prefix='trace-adapter-') as working:
        with tempfile.TemporaryFile() as errors:
            proc=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=errors,cwd=working,bufsize=0)
            selector=selectors.DefaultSelector();selector.register(proc.stdout,selectors.EVENT_READ);buffer=bytearray()
            def send(obj):
                transcript.append({'direction':'to_adapter','payload':obj});proc.stdin.write((canonical(obj)+'\n').encode());proc.stdin.flush()
            def receive():
                nonlocal buffer
                newline=buffer.find(b'\n')
                while newline<0:
                    remaining=observation['deadline']-store.clock()
                    if remaining<=0:raise AdapterTimeout()
                    if not selector.select(min(remaining,1)):continue
                    chunk=os.read(proc.stdout.fileno(),65536)
                    if not chunk:raise RuntimeError('Adapter exited without an answer')
                    search_from=len(buffer);buffer.extend(chunk)
                    if max_message_bytes is not None and len(buffer)>max_message_bytes:
                        raise RuntimeError('resource_exhausted: Adapter message exceeds the configured operator byte budget')
                    newline=buffer.find(b'\n',search_from)
                line=bytes(buffer[:newline]);del buffer[:newline+1]
                text=line.decode();transcript.append({'direction':'from_adapter','raw':text})
                return json.loads(text)
            try:
                send({'observation':observation})
                for _ in range(observation['limits']['probes']+1):
                    msg=receive()
                    if not isinstance(msg,dict):raise ValueError('Adapter response must be an object')
                    if 'technical_error' in msg:
                        store.technical_error(token,str(msg['technical_error']));return
                    if 'answer' in msg:
                        store.act(token,'submit',{'request_id':uuid.uuid4().hex,'item_id':observation['item']['id'],'answer':msg['answer']});return
                    if 'probe' in msg:
                        p=msg['probe']
                        if not isinstance(p,dict):raise ValueError('Probe must be an object')
                        try:result=store.act(token,'probe',{'request_id':uuid.uuid4().hex,'item_id':observation['item']['id'],'changes':p.get('changes')})
                        except StudyError as e:result={'error':str(e)}
                        send({'probe_result':result});continue
                    raise ValueError('Adapter must emit answer or probe')
                raise ValueError('Adapter action limit exceeded')
            except AdapterTimeout:
                store.act(token,'state') # Timer is authoritative; records a zero-score timeout.
            except (ValueError,UnicodeError) as e:
                store.act(token,'submit',{'request_id':uuid.uuid4().hex,'item_id':observation['item']['id'],'answer':{'invalid_adapter_output':str(e)}})
            except (OSError,RuntimeError) as e:
                store.technical_error(token,str(e))
            finally:
                selector.close()
                if proc.poll() is None:proc.kill()
                proc.wait();proc.stdin.close();proc.stdout.close()
                # Adapter stderr may contain credentials; never copy it into study records.

def evaluate_adapters(args):
    output=Path(args.output).resolve();audit=output.with_suffix('.transport.jsonl');db=output.with_suffix('.sqlite3')
    if any(p.exists() for p in (output,audit,db)):raise ValueError('Use a new run output prefix; preserve partial logs after a failure')
    metadata=json.loads(Path(args.metadata).read_text())
    for key in ('provider','model_snapshot','generation','registration_id'):
        if key not in metadata or (key!='generation' and (not isinstance(metadata[key],str) or not metadata[key].strip())):raise ValueError('Metadata requires nonempty '+key)
    if not isinstance(metadata['generation'],dict):raise ValueError('generation must be an object')
    command=shlex.split(args.adapter)
    if not command:raise ValueError('Adapter command is empty')
    # Resolve script arguments before using an empty temporary working directory.
    command=[str(Path(x).resolve()) if Path(x).is_file() else x for x in command]
    if any(x.endswith('adapters/chat_completions.py') for x in command):
        if os.environ.get('TRACE_MODEL')!=metadata['model_snapshot']:raise ValueError('TRACE_MODEL must equal the declared model_snapshot')
        if json.loads(os.environ.get('TRACE_GENERATION_JSON','{}'))!=metadata['generation']:raise ValueError('TRACE_GENERATION_JSON must match declared generation settings')
        if not os.environ.get('TRACE_API_KEY'):raise ValueError('Configure TRACE_API_KEY in the environment')
    metadata.update(system_id=args.system_id,adapter_command=command,adapter_files_sha256={x:hashlib.sha256(Path(x).read_bytes()).hexdigest() for x in command if Path(x).is_file()})
    batch_id=uuid.uuid4().hex
    metadata['batch_id']=batch_id
    metadata['config_sha256']=digest({k:metadata[k] for k in ('provider','model_snapshot','generation','registration_id','adapter_files_sha256')})
    metadata['evaluation_source_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'benchmark').glob('*.py'))}
    output.parent.mkdir(parents=True,exist_ok=True);store=StudyStore(db,dataset=getattr(args,'dataset',None))
    forms=[(name,f) for name,f in store.forms.items() if f['split']==args.split and (not args.panel or f.get('human_panel',False))]
    if not forms:raise ValueError('No forms selected')
    if args.max_forms:forms=forms[:args.max_forms]
    try:
        with audit.open('x') as log:
            for rep in range(args.repetitions):
                for name,form in forms:
                    session=store.create('agent',f'run-{batch_id}-{rep}',args.split,name,args.condition,metadata={**metadata,'repetition':rep},seconds=getattr(args,'seconds',480),probes=getattr(args,'probes',8))
                    token=session['token']
                    while not store.act(token,'state')['complete']:
                        obs=store.act(token,'next');transcript=[]
                        run_adapter(store,token,obs,command,transcript,max_message_bytes=getattr(args,'max_adapter_message_bytes',None))
                        log.write(canonical({'session_id':session['session_id'],'item_id':obs['item']['id'],'observation_sha256':digest(obs),'transport':transcript})+'\n');log.flush()
    finally:store.export(output)
    return {'path':str(output),'transport':str(audit),'forms':len(forms),'repetitions':args.repetitions,'dataset_sha256':store.manifest['dataset_sha256']}

def main():
    p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group(required=True);g.add_argument('--suite',choices=['baselines']);g.add_argument('--strategy',choices=STRATEGIES);g.add_argument('--adapter')
    p.add_argument('--split',default='test');p.add_argument('--repetitions',type=int,default=5);p.add_argument('--seed',type=int,default=1729);p.add_argument('--output',required=True)
    p.add_argument('--dataset',help='Compiled package directory; defaults to data/')
    p.add_argument('--seconds',type=float,default=480,help='Positive finite per-item budget for adapter sessions')
    p.add_argument('--probes',type=int,default=8,help='Nonnegative probe-arm query budget')
    p.add_argument('--max-adapter-message-bytes',type=int,help='Optional positive operator budget; no preset message cap')
    p.add_argument('--system-id');p.add_argument('--metadata');p.add_argument('--condition',choices=['reasoning','probe'],default='reasoning');p.add_argument('--panel',action='store_true');p.add_argument('--max-forms',type=int,help='Transport smoke runs only; partial coverage is reported')
    args=p.parse_args()
    if args.repetitions<1 or (args.max_forms is not None and args.max_forms<1):p.error('Counts must be positive')
    if args.max_adapter_message_bytes is not None and args.max_adapter_message_bytes<1:p.error('--max-adapter-message-bytes must be positive')
    if args.adapter:
        if not args.system_id or not args.metadata:p.error('--adapter requires --system-id and --metadata')
        result=evaluate_adapters(args)
    else:result=baselines(args.output,args.split,args.repetitions,args.seed,(args.strategy,) if args.strategy else STRATEGIES,dataset=args.dataset)
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
