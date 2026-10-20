"""Regrade immutable TRACE2 logs; equal-item estimates and exploratory form-cluster intervals.
Confirmatory inference requires a registered fixed-design plan and complete audited clusters.
"""
import argparse,csv,hashlib,json,math,platform,random,re,statistics,sys
from datetime import datetime,timezone
from urllib.parse import urlparse
from collections import Counter,defaultdict
from pathlib import Path
from .core import MODES,PROTOCOL_VERSION,digest,grade
from .paths import ROOT
from .runtime import load_package,StudyError

DIAGNOSTICS=('guarantee','prevention','minimality')
INFERENCE_GATE='EXPLORATORY: no validated registration supplied. Bootstrap intervals are exploratory; conservative Hoeffding bounds require their stated fixed-design assumptions.'
REGISTERED_STATUS='REGISTERED CONDITIONAL ANALYSIS: primary 95% cluster Hoeffding bound; validity remains conditional on operator-attested design and independence assumptions. Bootstrap intervals are exploratory.'
class AnalysisError(ValueError):pass

def records(paths):
    for path in paths:
        with Path(path).open() as stream:
            for number,line in enumerate(stream,1):
                if not line.strip():continue
                try:row=json.loads(line)
                except ValueError as error:raise AnalysisError(f'{path}:{number}: invalid JSON') from error
                if not isinstance(row,dict):raise AnalysisError('Every event must be an object')
                yield row

def configuration(meta):
    names=('provider','model_snapshot','generation','registration_id','adapter_files_sha256')
    if not isinstance(meta,dict) or any(name not in meta for name in names):raise AnalysisError('Agent provenance requires provider, snapshot, generation, registration and adapter hashes')
    if any(not isinstance(meta[name],str) or not meta[name].strip() for name in ('provider','model_snapshot','registration_id')):raise AnalysisError('Empty agent provenance')
    if not isinstance(meta['generation'],dict) or not isinstance(meta['adapter_files_sha256'],dict) or not meta['adapter_files_sha256']:raise AnalysisError('Invalid generation/adapter provenance')
    identity=digest({name:meta[name] for name in names})
    if meta.get('config_sha256',identity)!=identity:raise AnalysisError('Configuration hash mismatch')
    return identity

def load_trials(paths,items,manifest,forms):
    rows=[];seen=set();configs={};sources={};cohorts={};budgets={}
    for row in records(paths):
        if row.get('record_type')!='trial':continue
        r=dict(row)
        if r.get('schema_version')!='trace.trial.v2' or r.get('protocol_version')!=PROTOCOL_VERSION or r.get('dataset_sha256')!=manifest['dataset_sha256']:raise AnalysisError('Mixed or unrecognized dataset/protocol/schema version')
        if r.get('forms_sha256')!=manifest['forms_sha256']:raise AnalysisError('Form release mismatch')
        if not all(isinstance(r.get(k),str) and r[k] for k in ('session_id','participant_id','item_id','form_id')):raise AnalysisError('Missing identity')
        unique=(r['session_id'],r['item_id'])
        if unique in seen:raise AnalysisError('Duplicate session/item outcome')
        seen.add(unique)
        if r['item_id'] not in items or r['form_id'] not in forms:raise AnalysisError('Unknown item/form')
        item=items[r['item_id']];form=forms[r['form_id']]
        if set(r.get('form_item_ids',[]))!=set(form['item_ids']):raise AnalysisError('Form contents mismatch')
        if r.get('split')!=item['split'] or (item['split']!='tutorial' and r['item_id'] not in form['item_ids']):raise AnalysisError('Item/split/form mismatch')
        if r.get('mode') not in MODES or r.get('cohort') not in ('human','agent','baseline') or r.get('condition') not in ('reasoning','probe'):raise AnalysisError('Unknown study condition')
        for field in ('duration_ms','probes_used','attempts_used'):
            if type(r.get(field)) not in (int,float) or not math.isfinite(r[field]) or r[field]<0:raise AnalysisError('Invalid numeric budget field '+field)
        limits=r.get('limits')
        if not isinstance(limits,dict) or set(limits)!={'seconds','probes','attempts'} or type(limits['attempts']) is not int or limits['attempts']!=1 or type(limits['probes']) is not int or limits['probes']<0:
            raise AnalysisError('Missing or invalid declared session limits')
        seconds=limits['seconds']
        if seconds is None:
            if r['cohort']!='baseline':raise AnalysisError('Timed participants require a finite time budget')
        elif type(seconds) not in (int,float) or not math.isfinite(seconds) or seconds<=0:raise AnalysisError('Invalid declared time budget')
        if (seconds is not None and r['duration_ms']/1000>seconds+.0005) or type(r['probes_used']) is not int or r['probes_used']>limits['probes'] or (r['condition']=='reasoning' and limits['probes']!=0):raise AnalysisError('Budget contract violation')
        status=r.get('status');eligible=status in ('submitted','timeout')
        if status not in ('submitted','timeout','technical_error','withdrawn'):raise AnalysisError('Unrecognized outcome status')
        if r['attempts_used']!=(1 if status=='submitted' else 0):raise AnalysisError('Attempt contract violation')
        expected=grade(item,r.get('response'),r['mode']) if status=='submitted' else dict(correct=False,valid_format=False,**{field:False for field in DIAGNOSTICS})
        if eligible:
            for field in ('correct','valid_format',*DIAGNOSTICS):
                if type(r.get(field)) is not bool or r[field]!=expected[field]:raise AnalysisError('Recorded grade does not match regrading: '+field)
        elif any(r.get(field) is not None for field in ('correct',*DIAGNOSTICS)) or not r.get('reason'):raise AnalysisError('Excluded trial requires null scores and a reason')
        if status=='submitted' and r['cohort']!='baseline' and not isinstance(r.get('request_id'),str):raise AnalysisError('Missing first-submission request ID')
        if r.get('family')!=item.get('family','external') or r.get('cell_count')!=(item['target_step']+1)*len(item['machine']['inputs']):raise AnalysisError('Item descriptors mismatch')
        meta=r.get('agent_metadata',{})
        if r['cohort']!='human' and (not isinstance(meta,dict) or not isinstance(meta.get('system_id'),str)):raise AnalysisError('Missing system identity')
        system='human' if r['cohort']=='human' else r['cohort']+':'+meta['system_id']
        group=(system,r['condition'])
        if group in budgets and budgets[group]!=limits:raise AnalysisError('Mixed interaction budgets within one system/condition; analyze separately')
        budgets[group]=limits
        if r['cohort']=='agent':
            identity=configuration(meta)
            if group in configs and configs[group]!=identity:raise AnalysisError('Mixed model/configuration under one system ID; analyze separately')
            configs[group]=identity
            if not isinstance(meta.get('batch_id'),str) or not meta['batch_id']:raise AnalysisError('Agent run requires a globally unique batch_id')
            cohort=(group,r['form_id'],r['participant_id'])
            if cohort in cohorts and cohorts[cohort]!=meta['batch_id']:raise AnalysisError('Run-cohort identity collision across batches')
            cohorts[cohort]=meta['batch_id']
            r['config_sha256']=identity
        if r['cohort']!='baseline':
            provenance=r.get('source_provenance',{})
            if not provenance.get('files_sha256') or provenance.get('source_sha256')!=digest(provenance['files_sha256']):raise AnalysisError('Missing or inconsistent source provenance')
            identity=(provenance['source_sha256'],provenance.get('instructions_sha256'))
            if group in sources and sources[group]!=identity:raise AnalysisError('Mixed code/instruction releases within a study condition')
            sources[group]=identity
        no_answer=isinstance(r.get('response'),dict) and r['response'].get('verdict')=='no_explanation'
        rows.append({**r,'system':system,'included':eligible,'answer_kind':'no_explanation' if no_answer else 'cells'})
    human_sessions=defaultdict(set)
    for r in rows:
        if r['cohort']=='human':human_sessions[r['participant_id']].add(r['session_id'])
    if any(len(sessions)>1 for sessions in human_sessions.values()):raise AnalysisError('Human ID occurs in multiple sessions')
    return rows

def macro(rows,expected,field):
    by=defaultdict(list)
    for row in rows:
        if row['included'] and row['item_id'] in expected:by[row['item_id']].append(row[field])
    if set(expected)-by.keys():return None
    return statistics.mean(statistics.mean(by[item]) for item in sorted(expected))

def percentile(values,q):
    ordered=sorted(values);x=(len(ordered)-1)*q;lo=int(x);hi=min(lo+1,len(ordered)-1)
    return ordered[lo]+(ordered[hi]-ordered[lo])*(x-lo)

def bootstrap(rows,expected,count,rng):
    eligible=[r for r in rows if r['included'] and r['item_id'] in expected]
    if macro(eligible,expected,'correct') is None:return [],{'reason':'Missing planned item coverage','redraws':0}
    forms=defaultdict(lambda:defaultdict(list))
    for row in eligible:forms[row['form_id']][row['participant_id']].append(row)
    sizes={form:len(clusters) for form,clusters in forms.items()}
    if not sizes or min(sizes.values())<2:return [],{'reason':'Fewer than two independent clusters in at least one form','clusters_per_form':sizes,'redraws':0}
    for clusters in forms.values():
        assigned=set(next(iter(clusters.values()))[0]['form_item_ids'])&set(expected)
        if any({row['item_id'] for row in cluster}!=assigned for cluster in clusters.values()):
            return [],{'reason':'Incomplete within-form cluster; no conditional redraw or silent complete-case exclusion is permitted','clusters_per_form':sizes,'redraws':0}
    # One agent repetition is a cluster across every form, never independently redrawn per form.
    if all(row.get('cohort')=='agent' for row in eligible):
        runs=defaultdict(list)
        for row in eligible:runs[row['participant_id']].append(row)
        if len(runs)<2 or any({row['item_id'] for row in run}!=set(expected) for run in runs.values()):
            return [],{'reason':'Fewer than two complete whole-panel agent runs','redraws':0}
        clusters=list(runs.values());values=[]
        for _ in range(count):
            sample=[row for _ in clusters for row in clusters[rng.randrange(len(clusters))]]
            values.append(macro(sample,expected,'correct'))
        return values,{'reason':None,'whole_run_clusters':len(clusters),'redraws':0,'status':'Exploratory whole-run bootstrap'}
    values=[]
    for _ in range(count):
        sums=defaultdict(float);denom=Counter()
        for _,mapping in sorted(forms.items()):
            clusters=list(mapping.values())
            for _ in clusters:
                for row in clusters[rng.randrange(len(clusters))]:sums[row['item_id']]+=row['correct'];denom[row['item_id']]+=1
        values.append(sum(sums[item]/denom[item] for item in expected)/len(expected))
    return values,{'reason':None,'clusters_per_form':sizes,'redraws':0,'status':'Exploratory participant bootstrap within forms'}

def cluster_bound(rows,expected,alpha=.05):
    """Hoeffding for independent bounded participant/run contributions, fixed coverage.
    A run ID is one cluster across all forms. No iid assumption within a cluster.
    Eligibility/assignment must be fixed independently of outcomes; code cannot verify that.
    """
    selected=[row for row in rows if row['item_id'] in expected]
    estimate=macro(selected,expected,'correct')
    if estimate is None:return {'ci95':None,'reason':'Missing planned item coverage'}
    if any(not row['included'] for row in selected):return {'ci95':None,'reason':'Exclusions require a registered missingness analysis'}
    by_form=defaultdict(lambda:defaultdict(list))
    for row in selected:by_form[row['form_id']][row['participant_id']].append(row)
    for clusters in by_form.values():
        assigned=set(next(iter(clusters.values()))[0]['form_item_ids'])&set(expected)
        if any({row['item_id'] for row in cluster}!=assigned for cluster in clusters.values()):return {'ci95':None,'reason':'Incomplete assigned cluster'}
    coverage=Counter(row['item_id'] for row in selected);weights=defaultdict(float)
    for row in selected:weights[row['participant_id']]+=1/(len(expected)*coverage[row['item_id']])
    squared=sum(weight*weight for weight in weights.values());radius=math.sqrt(math.log(2/alpha)*squared/2)
    return {'ci95':[max(0.,estimate-radius),min(1.,estimate+radius)],'radius':radius,'sum_squared_cluster_ranges':squared,
        'independent_clusters':len(weights),'weight_sum':sum(weights.values()),'alpha':alpha,'reason':None,
        'method':'Distribution-free Hoeffding bound over independent participant/run clusters across all forms.',
        'assumptions':'Fixed outcome-independent assignment and eligibility; independent participant/run clusters; all assigned responses present. These assumptions require study review.'}

def event_dispositions(paths,split,forms,scope,manifest):
    all_events=list(records(paths));sessions={};result=defaultdict(Counter);started=defaultdict(set);finished=set();configs={}
    for event in all_events:
        if event.get('record_type')!='session':continue
        if event.get('schema_version')!='trace.session.v2' or event.get('protocol_version')!=PROTOCOL_VERSION or event.get('dataset_sha256')!=manifest['dataset_sha256'] or event.get('forms_sha256')!=manifest['forms_sha256']:raise AnalysisError('Mixed session release/protocol version')
        if event.get('split')!=split:continue
        form=forms.get(event.get('form_id'))
        if form is None:raise AnalysisError('Unknown session form')
        if scope=='panel' and split=='test' and not form.get('human_panel'):continue
        system='human' if event['cohort']=='human' else event['cohort']+':'+event.get('agent_metadata',{}).get('system_id','unknown')
        group=system+' / '+event['condition']
        if event['session_id'] in sessions:raise AnalysisError('Duplicate session event')
        if event['cohort']=='agent':
            config=configuration(event.get('agent_metadata',{}))
            if group in configs and configs[group]!=config:raise AnalysisError('Mixed model/configuration in session records')
            configs[group]=config
        sessions[event['session_id']]=(group,set(form['item_ids']));result[group]['sessions_created']+=1
    for event in all_events:
        identity=sessions.get(event.get('session_id'))
        if identity is None:continue
        group,assigned=identity;kind=event.get('record_type');key=(event.get('session_id'),event.get('item_id'))
        if kind=='session_withdrawn':result[group]['sessions_withdrawn']+=1
        if kind=='request_rejected':result[group]['rejected_'+str(event.get('action'))]+=1
        if kind=='request_replayed':result[group]['replayed_'+str(event.get('action'))]+=1
        if kind=='navigation' and event.get('item_id') in assigned:
            result[group]['navigation_events']+=1
            result[group]['navigation_'+str(event.get('kind'))]+=1
        if kind=='item_started':
            result[group]['all_items_started_including_practice']+=1
            if event.get('item_id') in assigned:
                if key in started[group]:raise AnalysisError('Duplicate trial start')
                started[group].add(key)
        if kind=='trial' and event.get('item_id') in assigned:finished.add(key)
    for group,counts in result.items():
        counts['scored_items_started']=len(started[group]);counts['started_without_outcome']=len(started[group]-finished)
    return {group:dict(counts) for group,counts in result.items()}


REGISTRATION_ASSUMPTIONS=('independent_clusters','independent_populations',
    'fixed_assignment_sample_and_stopping','noninformative_missingness',
    'complete_raw_export','registration_record_verified')

def validate_registration(path,paths,rows,expected,forms,manifest,split,scope):
    """Validate an operator-attested fixed, complete design; never infer independence.
    External registration authenticity and substantive assumptions remain auditable
    operator attestations. The supported confirmatory procedure admits no exclusions.
    """
    try:plan=json.loads(Path(path).read_text())
    except (OSError,ValueError) as error:raise AnalysisError('Cannot read registration JSON') from error
    required={'schema_version','status','registration_id','registry_url','registered_at',
        'reviewed_by','dataset_sha256','forms_sha256','protocol_version','source_sha256',
        'analysis_source_sha256','split','scope','condition','agent_system','agent_config_sha256',
        'primary_measure','direction','method','alpha','human_clusters_per_form',
        'agent_run_clusters','assumptions'}
    if not isinstance(plan,dict):raise AnalysisError('Registration must be an object')
    if plan.get('schema_version')=='trace.analysis-registration.v2':required.add('limits')
    if set(plan)!=required:raise AnalysisError('Registration must use the exact supported plan schema')
    if plan['schema_version'] not in ('trace.analysis-registration.v1','trace.analysis-registration.v2') or plan['status']!='registered':raise AnalysisError('Draft or unrecognized registration cannot enable confirmation')
    for field in ('registration_id','reviewed_by'):
        value=plan[field]
        if not isinstance(value,str) or len(value.strip())<3 or re.search(r'(?i)draft|todo|tbd|pending|replace|placeholder|example|unregistered',value):raise AnalysisError('Nonplaceholder '+field+' is required')
    url=urlparse(plan['registry_url']) if isinstance(plan['registry_url'],str) else None
    if url is None or url.scheme!='https' or not url.netloc or re.search(r'(?i)example|localhost|placeholder|invalid',url.netloc):raise AnalysisError('An HTTPS registration record URL is required')
    try:
        registered=datetime.fromisoformat(plan['registered_at'].replace('Z','+00:00'))
        if registered.tzinfo is None or registered>datetime.now(timezone.utc):raise ValueError()
        registered_at=registered.timestamp()
    except (AttributeError,TypeError,ValueError):raise AnalysisError('registered_at must be a past ISO timestamp with timezone')
    for field in ('dataset_sha256','forms_sha256','source_sha256','analysis_source_sha256','agent_config_sha256'):
        if not isinstance(plan[field],str) or not re.fullmatch(r'[0-9a-f]{64}',plan[field]) or plan[field]=='0'*64:raise AnalysisError('Invalid registration hash: '+field)
    if any(plan[field]!=manifest[field] for field in ('dataset_sha256','forms_sha256')) or plan['protocol_version']!=PROTOCOL_VERSION:raise AnalysisError('Registration release mismatch')
    if plan['analysis_source_sha256']!=hashlib.sha256(Path(__file__).read_bytes()).hexdigest():raise AnalysisError('Analysis implementation differs from the registered hash')
    if split!='test' or scope!='panel' or plan['split']!=split or plan['scope']!=scope:raise AnalysisError('Supported confirmatory comparison requires the registered test panel')
    if plan['condition'] not in ('reasoning','probe') or not isinstance(plan['agent_system'],str) or not plan['agent_system'].startswith('agent:') or len(plan['agent_system'])<=6:raise AnalysisError('Invalid registered condition or agent system')
    if (plan['primary_measure'],plan['direction'],plan['method'],plan['alpha'])!=('equal_item_accuracy','agent minus human','cluster_hoeffding',.05):raise AnalysisError('Unsupported registered primary procedure')
    if any(type(plan[field]) is not int or plan[field]<1 for field in ('human_clusters_per_form','agent_run_clusters')):raise AnalysisError('Register positive fixed cluster counts')
    if not isinstance(plan['assumptions'],dict) or set(plan['assumptions'])!=set(REGISTRATION_ASSUMPTIONS) or any(value is not True for value in plan['assumptions'].values()):raise AnalysisError('Every supported design assumption requires explicit review and attestation')
    targets={('human',plan['condition']),(plan['agent_system'],plan['condition'])}
    if {(row['system'],row['condition']) for row in rows}!=targets:raise AnalysisError('Confirmatory input must contain exactly the registered human-agent condition and system')
    registered_limits=plan.get('limits',{'attempts':1,'seconds':480,'probes':0 if plan['condition']=='reasoning' else 8})
    if not isinstance(registered_limits,dict) or set(registered_limits)!={'attempts','seconds','probes'} or type(registered_limits['attempts']) is not int or registered_limits['attempts']!=1 or type(registered_limits['seconds']) not in (int,float) or not math.isfinite(registered_limits['seconds']) or registered_limits['seconds']<=0 or type(registered_limits['probes']) is not int or registered_limits['probes']<0 or (plan['condition']=='reasoning' and registered_limits['probes']!=0):raise AnalysisError('Invalid registered interaction limits')
    if any(row['limits']!=registered_limits for row in rows):raise AnalysisError('Collected interaction budgets differ from registration')
    if any(not row['included'] for row in rows):raise AnalysisError('This registered conservative procedure does not support excluded or withdrawn trials')
    if any(row['source_provenance']['source_sha256']!=plan['source_sha256'] for row in rows):raise AnalysisError('Collected source release differs from registration')
    agents=[row for row in rows if row['cohort']=='agent']
    if any(configuration(row['agent_metadata'])!=plan['agent_config_sha256'] or row['agent_metadata']['registration_id']!=plan['registration_id'] for row in agents):raise AnalysisError('Agent configuration or registration identity differs from plan')
    events=list(records(paths));sessions={};starts={};withdrawn=set()
    def system(event):return 'human' if event.get('cohort')=='human' else event.get('cohort','')+':'+event.get('agent_metadata',{}).get('system_id','')
    for event in events:
        if event.get('record_type')=='session' and event.get('split')==split and (system(event),event.get('condition')) in targets and set(event.get('form_item_ids',[]))<=expected:
            sid=event.get('session_id')
            if sid in sessions:raise AnalysisError('Duplicate registered session')
            sessions[sid]=event
        elif event.get('record_type')=='item_started' and event.get('item_id') in expected:
            key=(event.get('session_id'),event['item_id'])
            if key in starts:raise AnalysisError('Duplicate registered item start')
            starts[key]=event
        elif event.get('record_type')=='session_withdrawn':withdrawn.add(event.get('session_id'))
    trial_sessions={row['session_id'] for row in rows}
    if set(sessions)!=trial_sessions or withdrawn&set(sessions):raise AnalysisError('Complete session ledger required, with no unstarted, missing or withdrawn registered sessions')
    for sid,event in sessions.items():
        cluster=[row for row in rows if row['session_id']==sid]
        expected_form=set(forms[cluster[0]['form_id']]['item_ids'])
        if set(event.get('form_item_ids',[]))!=expected_form or {row['item_id'] for row in cluster}!=expected_form:raise AnalysisError('Incomplete registered form')
        if event.get('source_provenance')!=cluster[0]['source_provenance'] or event.get('participant_id')!=cluster[0]['participant_id'] or system(event)!=cluster[0]['system']:raise AnalysisError('Session and trial identity/provenance differ')
        if event.get('limits')!=registered_limits:raise AnalysisError('Registered session budget differs from the fixed protocol')
        created=event.get('created_at')
        if type(created) not in (int,float) or not math.isfinite(created) or not registered_at<=created<=datetime.now(timezone.utc).timestamp():raise AnalysisError('Registration must precede session creation, and collection cannot be future dated')
        if event['cohort']=='agent' and (configuration(event.get('agent_metadata',{}))!=plan['agent_config_sha256'] or event['agent_metadata']['registration_id']!=plan['registration_id']):raise AnalysisError('Session configuration differs from registration')
        for row in cluster:
            start=starts.get((sid,row['item_id']))
            if start is None:raise AnalysisError('Every registered trial needs its original start event')
            began=start.get('started_at')
            if type(began) not in (int,float) or not math.isfinite(began) or began<created or row.get('started_at')!=began or start.get('deadline')!=row.get('deadline') or row.get('deadline')!=began+registered_limits['seconds']:raise AnalysisError('Invalid registered trial timeline')
            finished=row.get('finished_at')
            if type(finished) not in (int,float) or not math.isfinite(finished) or not began<=finished<=min(began+registered_limits['seconds'],datetime.now(timezone.utc).timestamp()):raise AnalysisError('Invalid registered finish time')
    if {key for key in starts if key[0] in sessions}!={(row['session_id'],row['item_id']) for row in rows}:raise AnalysisError('Started registered trial lacks an outcome')
    panel_forms={name for name,form in forms.items() if form['split']==split and form.get('human_panel',False)}
    human_counts=Counter(event['form_id'] for event in sessions.values() if event['cohort']=='human')
    if dict(human_counts)!={name:plan['human_clusters_per_form'] for name in panel_forms}:raise AnalysisError('Human sample differs from fixed registered form allocation')
    runs=defaultdict(list)
    for row in agents:runs[row['participant_id']].append(row)
    if len(runs)!=plan['agent_run_clusters'] or any(len(run)!=len(expected) or {row['item_id'] for row in run}!=expected or len({row['agent_metadata']['batch_id'] for row in run})!=1 for run in runs.values()):raise AnalysisError('Agent sample differs from fixed complete-run allocation')
    for target in targets:
        group=[row for row in rows if (row['system'],row['condition'])==target]
        if cluster_bound(group,expected)['ci95'] is None:raise AnalysisError('Registered cluster interval is unavailable')
    return {'plan':plan,'input_sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest(),
        'status':REGISTERED_STATUS,'attestation_limit':'Authenticity of external registration, independence, stopping, eligibility and completeness of supplied exports are operator attestations, not facts proved by software.'}

def analyze(paths,output,split='test',scope='panel',count=10000,seed=1729,confirmatory=False,registration=None,dataset=None):
    if confirmatory and registration is None:raise AnalysisError('Confirmatory analysis requires --registration with a completed registered plan')
    if registration is not None and not confirmatory:raise AnalysisError('Use --confirmatory to apply a registration plan')
    output=Path(output)
    if output.exists():raise AnalysisError('Use a new analysis output directory')
    if count<0:raise AnalysisError('Bootstrap count cannot be negative')
    if scope not in ('panel','full'):raise AnalysisError('Unknown analysis scope')
    try:_,body,manifest,forms=load_package(dataset)
    except StudyError as error:raise AnalysisError(str(error)) from error
    items=body['items']
    expected={item for form in forms.values() if form['split']==split and (scope=='full' or split!='test' or form.get('human_panel',False)) for item in form['item_ids']}
    if not expected:raise AnalysisError('No planned items in the requested split/scope')
    rows=load_trials(paths,items,manifest,forms)
    disposition=event_dispositions(paths,split,forms,scope,manifest)
    selected=[r for r in rows if r['split']==split and r['mode']=='explanation' and r['item_id'] in expected]
    registered=validate_registration(registration,paths,selected,expected,forms,manifest,split,scope) if confirmatory else None
    inference=REGISTERED_STATUS if registered else INFERENCE_GATE
    groups=defaultdict(list)
    for row in selected:groups[(row['system'],row['condition'])].append(row)
    summaries={};draws={};rng=random.Random(seed)
    for (system,condition),group in sorted(groups.items()):
        key=system+' / '+condition;included=[r for r in group if r['included']];coverage=Counter(r['item_id'] for r in included)
        values,diagnostic=bootstrap(group,expected,count,rng) if count and not system.startswith('baseline:') else ([],{'reason':'Computational baseline or bootstrap disabled','redraws':0})
        draws[key]=values;durations=[r['duration_ms']/1000 for r in included];statuses=Counter(r['status'] for r in group)
        summaries[key]={'system':system,'condition':condition,'planned_items':len(expected),'observed_items':len(coverage),'missing_items':sorted(expected-coverage.keys()),
            'trial_outcomes':len(group),'trials_started':disposition.get(key,{}).get('scored_items_started',len(group)),'started_without_outcome':disposition.get(key,{}).get('started_without_outcome',0),'included_trials':len(included),'clusters':len({r['participant_id'] for r in included}),
            'disposition':dict(statuses),'invalid_answers':sum(r['status']=='submitted' and not r['valid_format'] for r in group),
            'accuracy':macro(group,expected,'correct'),'accuracy_ci95':[percentile(values,.025),percentile(values,.975)] if values else None,
            'conservative_cluster_bound':cluster_bound(group,expected) if not system.startswith('baseline:') else None,
            'agent_configuration':{name:group[0].get('agent_metadata',{}).get(name) for name in ('provider','model_snapshot','generation','registration_id','config_sha256')} if system.startswith('agent:') else None,
            'source_provenance':group[0].get('source_provenance'),
            'limits':group[0]['limits'],
            'inference_status':inference,'confirmatory_ready':bool(registered),'coverage':dict(sorted(coverage.items())),'bootstrap':diagnostic,
            'diagnostics':{field+'_pass_rate':macro(group,expected,field) for field in DIAGNOSTICS},
            'no_explanation_answers':sum(r['status']=='submitted' and r['answer_kind']=='no_explanation' for r in group),
            'nonminimal_valid_answers':sum(r['status']=='submitted' and r['guarantee'] and r['prevention'] and not r['minimality'] for r in group),
            'capped_time_median_s':statistics.median(durations) if durations else None,
            'capped_time_iqr_s':[percentile(durations,.25),percentile(durations,.75)] if durations else None,
            'timeout_rate':statuses['timeout']/len(included) if included else None,
            'probe_mean':statistics.mean(r['probes_used'] for r in group) if group else None,
            'navigation_events':disposition.get(key,{}).get('navigation_events',0),
            'exclusions':[{'session_id':r['session_id'],'item_id':r['item_id'],'status':r['status'],'reason':r['reason']} for r in group if not r['included']]}
    for key,summary in summaries.items():
        if summary['started_without_outcome']:
            summary['accuracy_ci95']=None;summary['conservative_cluster_bound']={'ci95':None,'reason':'Started trial has no outcome; resolve batch disposition first'};draws[key]=[]
    contrasts=[]
    for key,summary in summaries.items():
        human='human / '+summary['condition']
        if not summary['system'].startswith('agent:') or human not in summaries:continue
        human_rules={r['source_provenance'].get('instructions_sha256') for r in selected if r['system']=='human' and r['condition']==summary['condition']}
        agent_rules={r['source_provenance'].get('instructions_sha256') for r in selected if r['system']==summary['system'] and r['condition']==summary['condition']}
        if human_rules!=agent_rules:raise AnalysisError('Human and agent task instructions differ; do not combine this contrast')
        if summary['limits']!=summaries[human]['limits']:raise AnalysisError('Human and agent interaction budgets differ; do not combine this contrast')
        other=summaries[human];gap=None if summary['accuracy'] is None or other['accuracy'] is None else 100*(summary['accuracy']-other['accuracy'])
        differences=[100*(a-b) for a,b in zip(draws[key],draws[human])]
        ab=summary['conservative_cluster_bound'];hb=other['conservative_cluster_bound'];conservative=None
        if gap is not None and ab and hb and ab['ci95'] is not None and hb['ci95'] is not None:
            radius=100*math.sqrt(math.log(40)*(ab['sum_squared_cluster_ranges']+hb['sum_squared_cluster_ranges'])/2)
            conservative={'ci95_pp':[max(-100.,gap-radius),min(100.,gap+radius)],'radius_pp':radius,'method':'Hoeffding over combined independent human and agent cluster contributions'}
        contrasts.append({'agent':summary['system'],'condition':summary['condition'],'direction':'agent minus human','gap_pp':gap,
            'conservative_cluster_bound':conservative,'ci95_pp':[percentile(differences,.025),percentile(differences,.975)] if differences else None,'items':len(expected),'inference_status':inference,'primary':bool(registered)})
    report={'dataset_sha256':manifest['dataset_sha256'],'protocol_version':PROTOCOL_VERSION,'split':split,'scope':scope,
        'estimand':'Equal-item accepted minimal-explanation accuracy on the fixed item set; all eligible partial-session answers retained.',
        'inference_status':inference,'confirmatory_ready':bool(registered),'diagnostic_denominator':'Eligible item responses, item weighted; timeout/invalid/no-explanation diagnostic flags are false. Diagnostic flags are not cell-overlap scores.',
        'planned_items':len(expected),'trial_events_read':len(rows),'selected_trial_events':len(selected),'groups':summaries,'contrasts':contrasts,
        'navigation_measure':'Client-reported, debounced navigation event counts and server timestamps; descriptive interface activity, not reasoning time or causal accuracy. Absence of events does not establish absence of navigation.',
        'session_events':disposition,'bootstrap_repetitions':count,'seed':seed,'registration':registered,'primary_uncertainty':'cluster_hoeffding' if registered else None,'bootstrap_role':'exploratory only'}
    output.mkdir(parents=True);(output/'summary.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    columns=['session_id','participant_id','system','condition','form_id','item_id','family','split','status','included','correct','answer_kind',*DIAGNOSTICS,'duration_ms','probes_used','attempts_used','request_id','reason']
    with (output/'trial_rows.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=columns,extrasaction='ignore');writer.writeheader();writer.writerows(selected)
    def tex(value):return ''.join({'_':r'\_','%':r'\%','&':r'\&','#':r'\#','$':r'\$','{':r'\{','}':r'\}','\\':r'\textbackslash{}','~':r'\textasciitilde{}','^':r'\textasciicircum{}'}.get(c,c) for c in value)
    lines=['% '+inference,r'\begin{tabular}{lrr}\toprule System / condition & Items & Accepted explanation\\\midrule']
    for key,summary in summaries.items():
        exact='unavailable' if summary['accuracy'] is None else f"{100*summary['accuracy']:.1f}\\%"
        lines.append(f"{tex(key)} & {summary['observed_items']}/{summary['planned_items']} & {exact}"+r'\\')
    lines.append(r'\bottomrule\end{tabular}');(output/'results_tables.tex').write_text('\n'.join(lines)+'\n')
    provenance={'inputs_sha256':{str(Path(path).resolve()):hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in paths},'dataset_sha256':manifest['dataset_sha256'],
        'analysis_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'python':sys.version,'platform':platform.platform(),'arguments':sys.argv,
        'outputs_sha256':{path.name:hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(output.iterdir())}}
    (output/'analysis_manifest.json').write_text(json.dumps(provenance,indent=2)+'\n');return report

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--input',nargs='+',required=True);parser.add_argument('--output-dir',required=True)
    parser.add_argument('--split',default='test');parser.add_argument('--scope',choices=['panel','full'],default='panel')
    parser.add_argument('--dataset',help='Compiled package directory whose logs are being analyzed')
    parser.add_argument('--bootstrap',type=int,default=10000);parser.add_argument('--seed',type=int,default=1729);parser.add_argument('--confirmatory',action='store_true',help='Apply a completed registered fixed-design plan; unsupported/incomplete designs reject')
    parser.add_argument('--registration',help='Completed JSON plan; docs/analysis_registration.template.json is deliberately a nonoperational draft')
    args=parser.parse_args();report=analyze(args.input,args.output_dir,args.split,args.scope,args.bootstrap,args.seed,args.confirmatory,args.registration,dataset=args.dataset)
    print(json.dumps({'path':args.output_dir,'groups':len(report['groups']),'planned_items':report['planned_items'],'inference_status':report['inference_status']},indent=2))
if __name__=='__main__':main()
