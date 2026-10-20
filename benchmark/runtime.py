"""Durable matched human/agent sessions. SQLite commits state and event together."""
import hashlib,json,math,re,secrets,sqlite3,time,uuid
from collections import OrderedDict
from collections.abc import Mapping
from contextlib import contextmanager
from pathlib import Path
from .core import MODES,PROTOCOL_VERSION,DATA_VERSION,canonical,digest,grade,probe,public_item,validate_item
from .paths import ROOT,dataset_directory
from .instructions import MODE_RULES,TUTORIAL_EXPLANATION,INSTRUCTION_BRIEF,rules_for_limits
from .teaching import demonstrations,practice_feedback,practice_solution

class StudyError(ValueError):pass

NAVIGATION_KINDS=('pan','zoom','moment','route','jump','overview','start','replay','controls')

class PackageItems(Mapping):
    """Load and validate one hash-bound task at a time; keep a small reuse cache.

    The cache bound is a memory optimization, not an admissible dataset bound.
    The in-memory index contains only IDs, locations and provenance, never boards.
    """
    def __init__(self,directory,index,packed=None):
        self.directory=directory;self.index=index;self.packed=packed
        self.cache=OrderedDict()
    def __iter__(self):return iter(self.index)
    def __len__(self):return len(self.index)
    def __contains__(self,item_id):return item_id in self.index
    def __getitem__(self,item_id):
        entry=self.index[item_id]
        if item_id in self.cache:
            self.cache.move_to_end(item_id);return self.cache[item_id]
        try:
            if self.packed is not None:item=self.packed[item_id]
            elif 'offset' in entry:
                path=self.directory/entry['path']
                if entry['offset']+entry['length']>path.stat().st_size:raise StudyError('Item byte range exceeds its shard: '+item_id)
                with path.open('rb') as stream:
                    stream.seek(entry['offset']);raw=stream.read(entry['length'])
                if len(raw)!=entry['length']:raise StudyError('Incomplete item shard: '+item_id)
                item=json.loads(raw)
            else:item=json.loads((self.directory/entry['path']).read_text())
            if not isinstance(item,dict) or digest(item)!=entry['sha256']:raise StudyError('Item digest mismatch: '+item_id)
            if item.get('id')!=item_id or item.get('split')!=entry['split'] or item.get('family','external')!=entry['family']:
                raise StudyError('Item metadata differs from package index: '+item_id)
            if 'board' not in item:raise StudyError('Every playable item requires a compiled visible board')
            validate_item(item)
        except (OSError,KeyError,TypeError,ValueError) as error:
            if isinstance(error,StudyError):raise
            raise StudyError('Invalid packaged item '+item_id+': '+str(error)) from error
        self.cache[item_id]=item
        if len(self.cache)>8:self.cache.popitem(last=False)
        return item


def load_package(dataset=None):
    """Load a hash-bound compiled package, independent of how it was produced.

    Answer keys and persisted certificates are not runtime dependencies. Forms
    are explicit so dataset selection and practice exposure cannot change on
    reload. Dataset compilers supply an empty tutorial list when none exists.
    """
    directory=dataset_directory(dataset)
    try:
        sharded=(directory/'dataset.json').is_file()
        body=json.loads((directory/('dataset.json' if sharded else 'corpus.json')).read_text())
        manifest=json.loads((directory/'manifest.json').read_text())
        forms=json.loads((directory/'forms.json').read_text())
        if not isinstance(body,dict) or not isinstance(manifest,dict):raise StudyError('Corpus and manifest must be objects')
        if body.get('schema_version')!=DATA_VERSION or manifest.get('schema_version')!=DATA_VERSION:
            raise StudyError('Dataset release does not match this runtime')
        if digest(body)!=manifest['dataset_sha256']:raise StudyError('Dataset digest mismatch')
        if digest(forms)!=manifest['forms_sha256']:raise StudyError('Form manifest digest mismatch')
        if sharded:
            entries=body.get('item_index');packed=None
        else:
            if not isinstance(body.get('items'),list) or not body['items']:raise StudyError('Dataset requires items')
            entries=[];packed={}
            for item in body['items']:
                if not isinstance(item,dict):raise StudyError('Items must be objects')
                if not isinstance(item.get('id'),str) or item['id'] in packed:raise StudyError('Item IDs must be unique strings')
                packed[item['id']]=item
                entries.append({'id':item['id'],'sha256':digest(item),'split':item.get('split'),'family':item.get('family','external')})
        if not isinstance(entries,list) or not entries:raise StudyError('Dataset requires an item index')
        index={}
        for entry in entries:
            if not isinstance(entry,dict):raise StudyError('Item index entries must be objects')
            item_id=entry.get('id')
            if not isinstance(item_id,str) or not item_id or item_id in index:raise StudyError('Item IDs must be unique nonempty strings')
            if not isinstance(entry.get('split'),str) or not entry['split'] or not isinstance(entry.get('family'),str):raise StudyError('Invalid item-index descriptors')
            if not isinstance(entry.get('sha256'),str) or not re.fullmatch('[0-9a-f]{64}',entry['sha256']):raise StudyError('Invalid item hash')
            if sharded:
                path=entry.get('path')
                if not isinstance(path,str) or Path(path).is_absolute() or '..' in Path(path).parts or not (directory/path).resolve().is_relative_to(directory):raise StudyError('Item path must remain inside its package')
                if path!='items.jsonl' and (not Path(path).parts or Path(path).parts[0]!='items'):raise StudyError('Task records belong in items.jsonl or items/, not metadata, archives, or raw logs')
                if ('offset' in entry)!=('length' in entry):raise StudyError('Shard index requires offset and length together')
                if 'offset' in entry and (type(entry['offset']) is not int or entry['offset']<0 or type(entry['length']) is not int or entry['length']<1):raise StudyError('Shard byte offsets must be nonnegative integers and lengths positive integers')
            index[item_id]=entry
        items=PackageItems(directory,index,packed)
        if not isinstance(forms,dict) or not forms:raise StudyError('Dataset requires forms')
        for name,form in forms.items():
            if not isinstance(name,str) or not name or not isinstance(form,dict):raise StudyError('Invalid form record')
            ids=form.get('item_ids')
            if not isinstance(ids,list) or not ids or any(not isinstance(i,str) for i in ids) or len(set(ids))!=len(ids) or any(i not in items for i in ids):raise StudyError('Form requires distinct known items')
            if not isinstance(form.get('split'),str) or not form['split']:raise StudyError('Form requires a split')
            if any(index[i]['split']!=form['split'] for i in ids):raise StudyError('Form/item split mismatch')
            if 'human_panel' in form and type(form['human_panel']) is not bool:raise StudyError('human_panel must be Boolean')
            practice=form.get('tutorial_ids',manifest.get('tutorial_ids',[]))
            if not isinstance(practice,list) or any(not isinstance(i,str) for i in practice) or len(set(practice))!=len(practice) or any(i not in items or index[i]['split']!='tutorial' for i in practice):raise StudyError('Practice references require distinct tutorial items')
    except (OSError,KeyError,TypeError,ValueError) as error:
        if isinstance(error,StudyError):raise
        raise StudyError('Invalid compiled package: '+str(error)) from error
    return directory,{**body,'items':items},manifest,forms

class StudyStore:
    def __init__(self,db,clock=time.time,dataset=None):
        self.db=Path(db).resolve();self.clock=clock
        source_paths=sorted({str(path.relative_to(ROOT)) for pattern in ("benchmark/*.py","adapters/*.py","web/*.js","web/*.html","web/*.css") for path in ROOT.glob(pattern)} | {"docs/STUDY_PROTOCOL.md","docs/AGENT_PROTOCOL.md","docs/REPORTING_PROTOCOL.md"})
        source_hashes={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in source_paths if (ROOT/name).exists()}
        self.provenance={"files_sha256":source_hashes,"source_sha256":digest(source_hashes),"instructions_sha256":digest(MODE_RULES)}
        self.db.parent.mkdir(parents=True,exist_ok=True)
        self.dataset,body,self.manifest,self.forms=load_package(dataset)
        self.items=body['items']
        with self.connect() as conn:
            conn.execute('CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, token TEXT UNIQUE NOT NULL, state TEXT NOT NULL)')
            conn.execute('CREATE TABLE IF NOT EXISTS events (seq INTEGER PRIMARY KEY AUTOINCREMENT, payload TEXT NOT NULL)')
            for row in conn.execute('SELECT state FROM sessions'):
                self.require_current_release(json.loads(row[0]))
    @contextmanager
    def connect(self):
        c=sqlite3.connect(self.db,timeout=20);c.row_factory=sqlite3.Row
        try:
            with c:yield c
        finally:c.close()
    def emit(self,conn,event):
        conn.execute('INSERT INTO events(payload) VALUES (?)',(canonical(event),))
    def save(self,conn,state):
        conn.execute('UPDATE sessions SET state=? WHERE id=?',(canonical(state),state['session_id']))
    def require_current_release(self,state):
        if state.get('protocol_version')!=PROTOCOL_VERSION or state.get('source_provenance')!=self.provenance:raise StudyError('Session belongs to different code/instructions; preserve it and use the frozen release')
        if state.get('dataset_sha256')!=self.manifest['dataset_sha256'] or state.get('forms_sha256')!=self.manifest['forms_sha256']:raise StudyError('Session belongs to a different dataset version; use a separate database')
    def create(self,cohort,participant,split,form,condition='reasoning',mode='explanation',rotation=0,metadata=None,*,seconds=480,probes=8):
        if cohort not in ('human','agent','baseline') or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}',participant):raise StudyError('Use a cohort and anonymous alphanumeric participant ID')
        if condition not in ('reasoning','probe') or mode not in MODES or type(rotation) is not int or rotation<0:raise StudyError('Invalid condition/mode/rotation')
        if type(seconds) not in (int,float) or not math.isfinite(seconds) or seconds<=0:raise StudyError('seconds must be finite and positive')
        if type(probes) is not int or probes<0:raise StudyError('probes must be a nonnegative integer')
        if form not in self.forms or self.forms[form]['split']!=split:raise StudyError('Form/split mismatch')
        if cohort=='human' and split=='test' and not self.forms[form].get('human_panel',False):raise StudyError('Use a designated human-panel form for confirmatory comparisons')
        ids=self.forms[form]['item_ids']
        if rotation>=len(ids):raise StudyError('Rotation must be smaller than the form length')
        ids=ids[rotation:]+ids[:rotation]
        default_tutorial=self.forms.get('tutorial-01',{}).get('item_ids',[])[:2]
        tutorial=self.forms[form].get('tutorial_ids',self.manifest.get('tutorial_ids',default_tutorial)) if split!='tutorial' else []
        now=self.clock();token=secrets.token_urlsafe(32)
        s={'session_id':uuid.uuid4().hex,'participant_id':participant,'cohort':cohort,'split':split,'form_id':form,
           'condition':condition,'mode':mode,'rotation':rotation,'agent_metadata':metadata or {},
           'limits':{'attempts':1,'seconds':seconds,'probes':0 if condition=='reasoning' else probes},
           'source_provenance':self.provenance,'dataset_sha256':self.manifest['dataset_sha256'],'forms_sha256':self.manifest['forms_sha256'],'protocol_version':PROTOCOL_VERSION,
           'form_item_ids':ids,'item_ids':tutorial+ids,'tutorial_ids':tutorial,'index':-1,'active':False,
           'started_at':None,'deadline':None,'probes_used':0,'probe_history':[],'practice_feedback':{},'receipts':{},'created_at':now,'last_receipt':None,'withdrawn':False}
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            if cohort=='human':
                for row in c.execute('SELECT state FROM sessions'):
                    prior=json.loads(row[0])
                    if prior['cohort']=='human' and prior['participant_id']==participant:
                        raise StudyError('This human ID already has a study session; recover its existing token instead of creating another')
            c.execute('INSERT INTO sessions VALUES (?,?,?)',(s['session_id'],token,canonical(s)))
            self.emit(c,{'record_type':'session','schema_version':'trace.session.v2',**{k:s[k] for k in ('session_id','participant_id','cohort','condition','split','form_id','form_item_ids','mode','agent_metadata','dataset_sha256','forms_sha256','protocol_version','rotation','source_provenance','created_at','limits')}})
        return {'session_id':s['session_id'],'token':token,'form_id':form,'total_items':len(s['item_ids']),'practice_items':len(tutorial)}
    def load(self,c,token):
        row=c.execute('SELECT state FROM sessions WHERE token=?',(token,)).fetchone()
        if not row:raise StudyError('Unknown session token')
        s=json.loads(row[0])
        self.require_current_release(s)
        return s
    def finish(self,c,s,answer,status='submitted',reason=None,now=None,request_id=None):
        now=self.clock() if now is None else now
        item=self.items[s['item_ids'][s['index']]];tutorial=item['id'] in s['tutorial_ids'] or s['split']=='tutorial'
        mode='explanation' if tutorial else s['mode']
        scored=grade(item,answer,mode) if status=='submitted' else {'correct':False,'valid_format':False,'guarantee':False,'prevention':False,'minimality':False}
        excluded=status in ('technical_error','withdrawn')
        trial={k:s[k] for k in ('session_id','participant_id','cohort','condition','form_id','mode','dataset_sha256','forms_sha256','protocol_version','agent_metadata','form_item_ids','source_provenance','limits')}
        trial.update(record_type='trial',schema_version='trace.trial.v2',item_id=item['id'],family=item.get('family','external'),split='tutorial' if tutorial else s['split'],mode=mode,
                     cell_count=(item['target_step']+1)*len(item['machine']['inputs']),status=status,correct=None if excluded else scored['correct'],
                     guarantee=None if excluded else scored['guarantee'],prevention=None if excluded else scored['prevention'],minimality=None if excluded else scored['minimality'],request_id=request_id,
                     duration_ms=max(0,round((min(now,s['deadline'])-s['started_at'])*1000)),probes_used=s['probes_used'],attempts_used=1 if status=='submitted' else 0,
                     response=answer,valid_format=scored['valid_format'],started_at=s['started_at'],deadline=s['deadline'],finished_at=now,reason=reason or scored.get('reason'))
        self.emit(c,trial);s['active']=False
        receipt={'received':True,'status':status,'item_id':item['id'],'next_available':s['index']+1<len(s['item_ids'])}
        if tutorial:
            receipt['feedback']=practice_feedback(item,answer)
            if status!='submitted':
                receipt['feedback'].update(correct=False,tests=None,message='Practice ended: '+status+'.')
            s.setdefault('practice_feedback',{})[item['id']]=receipt['feedback']
        s['last_receipt']=receipt
        return receipt
    def expire(self,c,s):
        if s['active'] and self.clock()>=s['deadline']:
            self.finish(c,s,{'cells':[]},'timeout',now=s['deadline'])
    def observation(self,s):
        done=s['withdrawn'] or (not s['active'] and s['index']>=len(s['item_ids'])-1)
        out={'protocol_version':PROTOCOL_VERSION,'dataset_sha256':s['dataset_sha256'],'session_id':s['session_id'],
             'condition':s['condition'],'mode':s['mode'],'active':s['active'],'complete':done,'position':s['index']+1,
             'total_items':len(s['item_ids']),'last_receipt':s['last_receipt'],'server_time':self.clock(),
             'limits':dict(s['limits'])}
        if s['active']:
            item=self.items[s['item_ids'][s['index']]];tutorial=item['id'] in s['tutorial_ids'] or s['split']=='tutorial'
            out.update(item=public_item(item),practice=tutorial,mode='explanation' if tutorial else s['mode'],deadline=s['deadline'],probes_used=s['probes_used'],probe_history=s.get('probe_history',[]))
        out['instruction_brief']=INSTRUCTION_BRIEF
        out['instructions']=rules_for_limits(out['mode'],s['limits'])
        out['demonstrations']=demonstrations()
        if s['index']>=len(s['tutorial_ids']):
            out['training_examples']=[{'item':public_item(self.items[i]),**practice_solution(self.items[i]),'explanation':TUTORIAL_EXPLANATION,'feedback':s.get('practice_feedback',{}).get(i)} for i in s['tutorial_ids']]
        return out
    def act(self,token,action,payload=None):
        try:return self._act(token,action,payload)
        except (StudyError,ValueError) as error:
            # Persist rejected attempts in their own transaction after rollback.
            with self.connect() as c:
                c.execute('BEGIN IMMEDIATE')
                try:s=self.load(c,token)
                except StudyError:raise error
                self.expire(c,s)
                self.emit(c,{'record_type':'request_rejected','session_id':s['session_id'],
                    'action':action,'request_id':payload.get('request_id') if isinstance(payload,dict) else None,
                    'item_id':payload.get('item_id') if isinstance(payload,dict) else None,
                    'reason':str(error),'time':self.clock()})
                self.save(c,s)
            raise StudyError(str(error)) from error
    def _act(self,token,action,payload=None):
        payload=payload or {}
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE');s=self.load(c,token);self.expire(c,s)
            request_id=payload.get('request_id')
            if action in ('submit','probe'):
                if not isinstance(request_id,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,80}',request_id):raise StudyError('A unique request_id is required')
                if request_id in s['receipts']:
                    saved=s['receipts'][request_id]
                    if saved['request']!=digest({'action':action,'payload':payload}):raise StudyError('request_id already used for different content')
                    self.emit(c,{'record_type':'request_replayed','session_id':s['session_id'],'action':action,'request_id':request_id,'time':self.clock()})
                    self.save(c,s);return saved['response']
            if action=='state':result=self.observation(s)
            elif action=='next':
                if s['active']:raise StudyError('Current item is still active')
                if s['withdrawn'] or s['index']+1>=len(s['item_ids']):raise StudyError('Session is complete')
                s['index']+=1;s['active']=True;s['probes_used']=0;s['probe_history']=[];s['started_at']=self.clock();s['deadline']=s['started_at']+s['limits']['seconds'];s['last_receipt']=None
                self.emit(c,{'record_type':'item_started','session_id':s['session_id'],'item_id':s['item_ids'][s['index']],'started_at':s['started_at'],'deadline':s['deadline']})
                result=self.observation(s)
            elif action=='submit':
                if not s['active']:
                    if s['last_receipt'] and s['last_receipt']['status']=='timeout':
                        self.emit(c,{'record_type':'request_rejected','session_id':s['session_id'],'action':'late_submit','request_id':request_id,'item_id':payload.get('item_id'),'response':payload.get('answer'),'reason':'deadline expired','time':self.clock()})
                        result=s['last_receipt']
                    else:raise StudyError('No active item; only one scored submission is allowed')
                else:
                    if payload.get('item_id')!=s['item_ids'][s['index']]:raise StudyError('Stale item_id')
                    result=self.finish(c,s,payload.get('answer'),request_id=request_id)
            elif action=='probe':
                if not s['active']:raise StudyError('No active item')
                if payload.get('item_id')!=s['item_ids'][s['index']]:raise StudyError('Stale item_id')
                budget=s['limits']['probes']
                if s['probes_used']>=budget:raise StudyError('Probe budget exhausted')
                result=probe(self.items[s['item_ids'][s['index']]],payload.get('changes'))
                s['probes_used']+=1;result['probes_used']=s['probes_used'];result['probes_remaining']=budget-s['probes_used']
                s.setdefault('probe_history',[]).append({'changes':payload.get('changes'),'result':result})
                self.emit(c,{'record_type':'probe','request_id':request_id,'session_id':s['session_id'],'item_id':s['item_ids'][s['index']],'changes':payload.get('changes'),'result':result,'time':self.clock()})
            elif action=='navigate':
                if not s['active']:raise StudyError('No active item')
                if set(payload)-{'item_id','kind','view'}:raise StudyError('Unknown navigation fields')
                if payload.get('item_id')!=s['item_ids'][s['index']]:raise StudyError('Stale item_id')
                kind=payload.get('kind');view=payload.get('view',{})
                if not isinstance(kind,str) or kind not in NAVIGATION_KINDS:raise StudyError('Unknown navigation kind')
                if not isinstance(view,dict) or set(view)-{'moment','route','zoom','x','y'}:raise StudyError('Invalid navigation view')
                for name,value in view.items():
                    if type(value) not in (int,float) or not math.isfinite(value) or value<0 or (name=='zoom' and value==0):raise StudyError('Navigation view values must be finite and nonnegative; zoom must be positive')
                item=self.items[s['item_ids'][s['index']]]
                if 'moment' in view and (type(view['moment']) is not int or view['moment']>item['target_step']):raise StudyError('Navigation moment is outside the task')
                if 'route' in view and (type(view['route']) is not int or view['route']>=item['machine']['states']):raise StudyError('Navigation route is outside the machine')
                now=self.clock()
                self.emit(c,{'record_type':'navigation','schema_version':'trace.navigation.v1','session_id':s['session_id'],
                    'item_id':item['id'],'kind':kind,'view':view,'server_time':now,'elapsed_ms':max(0,round((now-s['started_at'])*1000))})
                result={'recorded':True}
            elif action=='withdraw':
                if not s['withdrawn']:self.emit(c,{'record_type':'session_withdrawn','session_id':s['session_id'],'time':self.clock(),'position':s['index']+1})
                if s['active']:self.finish(c,s,None,'withdrawn',reason='participant withdrawal')
                s['withdrawn']=True;result={'withdrawn':True}
            else:raise StudyError('Unknown action')
            if action in ('submit','probe'):
                s['receipts'][request_id]={'request':digest({'action':action,'payload':payload}),'response':result}
            self.save(c,s);return result
    def expire_all(self):
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            for row in c.execute('SELECT state FROM sessions').fetchall():
                s=json.loads(row[0])
                self.require_current_release(s)
                self.expire(c,s);self.save(c,s)
    def technical_error(self,token,reason):
        """Researcher-side infrastructure disposition; never exposed to participants."""
        if not isinstance(reason,str) or not reason.strip():raise StudyError('A documented reason is required')
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE');s=self.load(c,token);self.expire(c,s)
            if s['active']:self.finish(c,s,None,'technical_error',reason=reason)
            self.save(c,s)
    def export(self,path):
        target=Path(path).resolve()
        if target==self.db or target.exists():raise StudyError('Export must use a new path and cannot replace the database')
        self.expire_all()
        with self.connect() as c:
            rows=[r[0] for r in c.execute('SELECT payload FROM events ORDER BY seq')]
        target.parent.mkdir(parents=True,exist_ok=True);target.write_text('\n'.join(rows)+'\n')
        return {'events':len(rows),'path':str(target)}
