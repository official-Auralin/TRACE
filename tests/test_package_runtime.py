"""Imported packages exercise the common runtime without construction or keys."""
import json
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

from benchmark.core import DATA_VERSION, SEMANTICS, canonical, digest, grade
from benchmark.evaluate import baselines, run_adapter
from benchmark.analyze import analyze
from benchmark.level import decorate
from benchmark.runtime import StudyError, StudyStore, load_package
from benchmark.server import Handler
from benchmark.teaching import practice_feedback


def imported_item():
    """An independent compact level fixture above the former Python limits."""
    states, channels, horizon = 17, 4, 20
    machine = {
        'inputs':[f'input{r}' for r in range(channels)],
        'states':states, 'initial':0,
        'transitions':[[{'next':(q+1)%states,'output':v&1}
                        for v in range(1 << channels)] for q in range(states)]}
    observed = [[t%2,0,0,0] for t in range(horizon)]
    layers = [[{'kind':'switch','cell':t*channels,
                'zero':{'kind':'output','value':0,'next':(q+1)%states},
                'one':{'kind':'output','value':1,'next':(q+1)%states}}
               for q in range(states)] for t in range(horizon)]
    board = decorate({'version':'trace.board.v2','initial':0,'states':states,
                      'inputs':channels,'horizon':horizon,'layers':layers},
                     observed,machine['inputs'])
    return {'id':'external-loop','split':'external','machine':machine,
            'observed':observed,'target_step':horizon-1,'board':board}


def write_package(directory, items=None, forms=None):
    directory.mkdir(parents=True,exist_ok=True)
    items = [imported_item()] if items is None else items
    forms = {'external':{'split':'external','item_ids':[i['id'] for i in items]}} if forms is None else forms
    body = {'schema_version':DATA_VERSION,'items':items}
    manifest = {'schema_version':DATA_VERSION,'dataset_sha256':digest(body),
                'forms_sha256':digest(forms),'tutorial_ids':[]}
    for name,value in [('corpus',body),('manifest',manifest),('forms',forms)]:
        (directory/(name+'.json')).write_text(json.dumps(value))
    return directory


def write_sharded_package(directory,items):
    write_package(directory,items)
    index=[]
    with (directory/'items.jsonl').open('wb') as stream:
        for item in items:
            raw=(canonical(item)+'\n').encode()
            index.append({'id':item['id'],'path':'items.jsonl','offset':stream.tell(),'length':len(raw),
                          'sha256':digest(item),'split':item['split'],'family':item.get('family','external')})
            stream.write(raw)
    descriptor={'schema_version':DATA_VERSION,'semantics':SEMANTICS,'item_index':index}
    manifest=json.loads((directory/'manifest.json').read_text());manifest['dataset_sha256']=digest(descriptor)
    (directory/'dataset.json').write_text(canonical(descriptor))
    (directory/'manifest.json').write_text(canonical(manifest))
    (directory/'corpus.json').unlink()
    return directory


class PackageRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.dataset=write_package(self.root/'package')
        self.now=1000.
        self.store=StudyStore(self.root/'sessions.sqlite3',clock=lambda:self.now,dataset=self.dataset)

    def tearDown(self):
        self.temp.cleanup()

    def test_keyless_external_human_agent_parity_and_configurable_limits(self):
        observations=[]
        for cohort in ('human','agent'):
            token=self.store.create(cohort,cohort,'external','external','probe',seconds=7,probes=12)['token']
            obs=self.store.act(token,'next');observations.append(obs)
            self.assertEqual(obs['limits'],{'attempts':1,'seconds':7,'probes':12})
            self.assertEqual(obs['deadline'],1007)
            self.assertEqual(obs['training_examples'],[])
            self.assertIn('7 seconds',obs['instructions'])
            self.assertIn('12 times',obs['instructions'])
            self.assertFalse({'key','certificate','recipe'} & obs['item'].keys())
            self.assertEqual(obs['item']['board']['display']['version'],'trace.display.v1')
            for index in range(12):
                reply=self.store.act(token,'probe',{'item_id':'external-loop','request_id':f'probe-{index}','changes':{}})
            self.assertEqual(reply['probes_remaining'],0)
            with self.assertRaises(StudyError):
                self.store.act(token,'probe',{'item_id':'external-loop','request_id':'extra','changes':{}})
            receipt=self.store.act(token,'submit',{'item_id':'external-loop','request_id':'answer','answer':{'cells':[76]}})
            self.assertNotIn('feedback',receipt)
        for field in ('item','instructions','limits','demonstrations'):
            self.assertEqual(observations[0][field],observations[1][field])
        with self.store.connect() as connection:
            trials=[json.loads(row[0]) for row in connection.execute('SELECT payload FROM events') if json.loads(row[0])['record_type']=='trial']
        self.assertTrue(all(trial['correct'] for trial in trials))
        self.assertTrue(all(trial['limits']['probes']==12 for trial in trials))

    def test_navigation_is_descriptive_and_does_not_consume_task_budgets(self):
        token=self.store.create('human','navigation','external','external',seconds=7)['token']
        request={'item_id':'external-loop','kind':'pan','view':{'moment':3,'route':2,'zoom':.5,'x':100,'y':20}}
        with self.assertRaisesRegex(StudyError,'No active'):self.store.act(token,'navigate',request)
        initial=self.store.act(token,'next');self.now+=2
        self.assertEqual(self.store.act(token,'navigate',request),{'recorded':True})
        state=self.store.act(token,'state')
        self.assertEqual(state['deadline'],initial['deadline'])
        self.assertEqual(state['probes_used'],0)
        self.assertEqual(state['limits']['attempts'],1)
        self.assertNotIn('navigation',state)
        for bad in ({'moment':20},{'route':17},{'zoom':0},{'x':float('nan')},{'y':-1},{'moment':True},{'answer':[76]}):
            with self.assertRaises(StudyError):self.store.act(token,'navigate',{**request,'view':bad})
        self.store.act(token,'submit',{'item_id':'external-loop','request_id':'answer','answer':{'cells':[76]}})
        with self.store.connect() as connection:
            events=[json.loads(row[0]) for row in connection.execute('SELECT payload FROM events')]
        navigation=[event for event in events if event['record_type']=='navigation']
        self.assertEqual(len(navigation),1)
        self.assertEqual(navigation[0]['elapsed_ms'],2000)
        trial=next(event for event in events if event['record_type']=='trial')
        self.assertTrue(trial['correct']);self.assertEqual(trial['attempts_used'],1)
        self.assertEqual(trial['duration_ms'],2000)
        raw=self.root/'navigation.jsonl';self.store.export(raw)
        report=analyze([raw],self.root/'navigation-analysis',split='external',count=0,dataset=self.dataset)
        self.assertEqual(report['groups']['human / reasoning']['navigation_events'],1)

    def test_no_answer_enumeration_or_key_lookup_in_practice(self):
        item=imported_item()
        item['key']={'explanation':[[0]]} # A deliberately incorrect legacy key.
        with patch('benchmark.game.minimal_answers',side_effect=AssertionError('enumeration forbidden')):
            feedback=practice_feedback(item,{'cells':[76]})
        self.assertTrue(feedback['correct'])
        self.assertEqual(feedback['accepted_explanations'],[[76]])
        self.assertEqual(feedback['answer_inventory'],'examples_not_exhaustive')
        self.assertTrue(grade(item,feedback['answer'])['correct'])

    def test_custom_form_length_rotation_and_budget_persist_on_reload(self):
        items=[]
        for index in range(6):
            item=imported_item();item['id']=f'external-{index}';items.append(item)
        write_package(self.dataset,items)
        store=StudyStore(self.root/'rotations.sqlite3',clock=lambda:self.now,dataset=self.dataset)
        token=store.create('agent','rotation','external','external',rotation=5,seconds=9)['token']
        obs=store.act(token,'next');self.assertEqual(obs['item']['id'],'external-5')
        reloaded=StudyStore(store.db,clock=lambda:self.now,dataset=self.dataset/'corpus.json')
        self.assertEqual(reloaded.act(token,'state')['deadline'],1009)
        self.now=1009
        self.assertEqual(reloaded.act(token,'state')['last_receipt']['status'],'timeout')

    def test_package_rejects_wrong_counterfactual_even_with_matching_hash(self):
        item=imported_item()
        item['board']['layers'][0][0]['one']['value']=0
        write_package(self.dataset,[item])
        with self.assertRaisesRegex(StudyError,'counterfactual'):
            load_package(self.dataset)[1]['items']['external-loop']

    def test_database_cannot_mix_dataset_identities(self):
        self.store.create('agent','original','external','external')
        item=imported_item();item['id']='other-release'
        other=write_package(self.root/'other',[item])
        with self.assertRaisesRegex(StudyError,'different dataset'):
            StudyStore(self.store.db,dataset=other)

    def test_sharded_package_is_lazy_and_checks_each_item_at_load(self):
        first=imported_item();second=imported_item();second['id']='second'
        path=write_sharded_package(self.root/'sharded',[first,second])
        with patch('benchmark.runtime.validate_item',side_effect=AssertionError('startup eagerly loaded an item')):
            store=StudyStore(self.root/'sharded.sqlite3',dataset=path/'dataset.json')
            self.assertEqual(set(store.items),{'external-loop','second'})
            self.assertEqual(len(store.items.cache),0)
        self.assertEqual(store.items['external-loop'],first)
        # Only the unused record is corrupted; accessing it must fail before play.
        shard=path/'items.jsonl'
        raw=shard.read_bytes();entry=store.items.index['second']
        replacement=raw[entry['offset']:].replace(b'"second"',b'"forged"',1)
        shard.write_bytes(raw[:entry['offset']]+replacement)
        with self.assertRaisesRegex(StudyError,'digest mismatch'):store.items['second']

    def test_custom_dataset_analysis_and_streamed_baselines(self):
        token=self.store.create('human','analysis','external','external',seconds=7)['token']
        self.store.act(token,'next')
        self.store.act(token,'submit',{'item_id':'external-loop','request_id':'analysis','answer':{'cells':[76]}})
        raw=self.root/'raw.jsonl';self.store.export(raw)
        report=analyze([raw],self.root/'report',split='external',count=0,dataset=self.dataset)
        self.assertEqual(report['planned_items'],1)
        self.assertEqual(report['groups']['human / reasoning']['accuracy'],1)
        self.assertEqual(report['groups']['human / reasoning']['limits']['seconds'],7)
        path=self.root/'baselines.jsonl'
        summary=baselines(path,split='external',repetitions=1,strategies=('solver',),dataset=self.dataset)
        self.assertEqual(summary['systems']['solver']['accuracy'],1)
        self.assertIsNone(summary['random_expected_exact_accuracy'])
        analysis=analyze([path],self.root/'baseline-report',split='external',count=0,dataset=self.dataset)
        self.assertEqual(analysis['groups']['baseline:solver / reasoning']['accuracy'],1)

    def test_adapter_can_use_more_than_eight_probes(self):
        # The real adapter runner shares exactly the same actions and budget.
        store=StudyStore(self.root/'agent.sqlite3',dataset=self.dataset)
        token=store.create('agent','many-probes','external','external','probe',seconds=60,probes=12)['token']
        obs=store.act(token,'next')
        adapter=self.root/'adapter.py'
        adapter.write_text('import json,sys\njson.loads(sys.stdin.readline())\n'
                           'for _ in range(12):\n'
                           ' print(json.dumps({"probe":{"changes":{}}}),flush=True)\n'
                           ' json.loads(sys.stdin.readline())\n'
                           'print(json.dumps({"answer":{"cells":[76]}}),flush=True)\n')
        transcript=[]
        run_adapter(store,token,obs,[sys.executable,str(adapter)],transcript)
        self.assertTrue(store.act(token,'state')['complete'])
        with store.connect() as connection:
            trial=next(json.loads(row[0]) for row in connection.execute('SELECT payload FROM events') if json.loads(row[0])['record_type']=='trial')
        self.assertEqual(trial['probes_used'],12)
        self.assertTrue(trial['correct'])

    def test_http_request_budget_is_operator_configurable(self):
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler);server.store=self.store
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            token=self.store.create('agent','large-request','external','external')['token']
            url=f'http://127.0.0.1:{server.server_port}/api/next'
            request=urllib.request.Request(url,data=json.dumps({'padding':'x'*70000}).encode(),headers={'X-Trace-Token':token})
            with urllib.request.urlopen(request) as response:self.assertEqual(response.status,200)
            server.max_request_bytes=1000
            with self.assertRaises(urllib.error.HTTPError) as caught:urllib.request.urlopen(request)
            self.assertEqual(caught.exception.code,413)
            self.assertEqual(json.load(caught.exception)['status'],'resource_exhausted')
            caught.exception.close()
        finally:
            server.shutdown();server.server_close();thread.join()


if __name__=='__main__':unittest.main()
