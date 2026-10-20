import copy,json,tempfile,threading,unittest,urllib.request,urllib.error,uuid
from pathlib import Path
from http.server import ThreadingHTTPServer
from benchmark.core import *
from benchmark.reference import direct_key
from benchmark.paths import ROOT
from benchmark.runtime import StudyStore,StudyError
from benchmark.server import Handler
from benchmark.game import solve

class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.now=1000.;self.store=StudyStore(Path(self.temp.name)/'study.sqlite3',clock=lambda:self.now)
    def tearDown(self):self.temp.cleanup()
    def create(self,condition='reasoning',participant='h1',cohort='human'):
        return self.store.create(cohort,participant,'pilot','pilot-01',condition)['token']
    def submit(self,token,obs,answer=None,request='request'):
        if answer is None:answer={'cells':solve(self.store.items[obs['item']['id']])}
        return self.store.act(token,'submit',{'request_id':request,'item_id':obs['item']['id'],'answer':answer})
    def events(self):
        with self.store.connect() as c:return [json.loads(r[0]) for r in c.execute('SELECT payload FROM events')]
    def main_item(self,token):
        for i in range(2):obs=self.store.act(token,'next');self.submit(token,obs,request='practice'+str(i))
        return self.store.act(token,'next')
    def test_one_attempt_idempotence_and_no_key(self):
        token=self.create();obs=self.main_item(token)
        self.assertFalse({'key','family','recipe','certificate'}&obs['item'].keys())
        self.assertEqual(len(obs['training_examples']),2)
        example=obs['training_examples'][0]
        self.assertEqual(example['answer_inventory'],'one_example_not_exhaustive')
        self.assertTrue(grade(self.store.items[example['item']['id']],example['answer'])['correct'])
        self.assertIn('proper subset',example['explanation'])
        receipt=self.submit(token,obs);self.assertNotIn('feedback',receipt);self.assertNotIn('correct',receipt)
        self.assertEqual(receipt,self.submit(token,obs))
        with self.assertRaises(StudyError):self.submit(token,obs,answer={'cells':[]})
        with self.assertRaises(StudyError):self.submit(token,obs,request='second')
        self.assertEqual(len([r for r in self.events() if r.get('item_id')==obs['item']['id'] and r['record_type']=='trial']),1)
    def test_malformed_is_scored_wrong(self):
        token=self.create();obs=self.main_item(token);self.submit(token,obs,{'cells':[True]})
        last=[r for r in self.events() if r['record_type']=='trial'][-1]
        self.assertFalse(last['correct']);self.assertFalse(last['valid_format']);self.assertEqual(last['attempts_used'],1)
    def test_deadline_persists_restart_reload(self):
        token=self.create();obs=self.main_item(token);deadline=obs['deadline'];self.now+=479
        reloaded=StudyStore(self.store.db,clock=lambda:self.now);self.assertEqual(reloaded.act(token,'state')['deadline'],deadline)
        self.now+=1;receipt=self.submit(token,obs);self.assertEqual(receipt['status'],'timeout')
        last=[r for r in self.events() if r['record_type']=='trial'][-1];self.assertFalse(last['correct']);self.assertEqual(last['duration_ms'],480000)
    def test_probe_zero_and_eight_budget(self):
        for condition in ('reasoning','probe'):
            token=self.create(condition,participant=condition);obs=self.main_item(token)
            p={'request_id':'p0','item_id':obs['item']['id'],'changes':{}}
            if condition=='reasoning':
                with self.assertRaises(StudyError):self.store.act(token,'probe',p)
            else:
                result=self.store.act(token,'probe',p);self.assertEqual(result,self.store.act(token,'probe',p));self.assertEqual(result['switches_changed'],0)
                for i in range(1,8):self.store.act(token,'probe',{**p,'request_id':'p'+str(i)})
                with self.assertRaises(StudyError):self.store.act(token,'probe',{**p,'request_id':'p9'})
                self.assertEqual(self.store.act(token,'state')['probes_used'],8)
                reloaded=StudyStore(self.store.db,clock=lambda:self.now)
                self.assertEqual(len(reloaded.act(token,'state')['probe_history']),8)
    def test_withdrawal_and_export(self):
        token=self.create();self.main_item(token);self.store.act(token,'withdraw');self.assertTrue(self.store.act(token,'state')['complete'])
        output=Path(self.temp.name)/'events.jsonl';self.store.export(output)
        self.assertNotIn(token,output.read_text())
        with self.assertRaises(StudyError):self.store.export(output)
        last=[r for r in self.events() if r['record_type']=='trial'][-1];self.assertIsNone(last['correct']);self.assertEqual(last['status'],'withdrawn')
    def test_repeat_human_and_panel_restrictions(self):
        self.create()
        with self.assertRaises(StudyError):self.create()
        with self.assertRaises(StudyError):self.store.create('human','h3','test','test-17')
    def test_technical_error_and_timeout_precedence(self):
        token=self.create();self.main_item(token);self.store.technical_error(token,'documented local outage')
        self.assertEqual([r for r in self.events() if r['record_type']=='trial'][-1]['status'],'technical_error')
        self.store.act(token,'next');self.now+=480;self.store.technical_error(token,'late claimed outage')
        self.assertEqual([r for r in self.events() if r['record_type']=='trial'][-1]['status'],'timeout')

class HTTPTests(unittest.TestCase):
    setUp=RuntimeTests.setUp
    tearDown=RuntimeTests.tearDown
    create=RuntimeTests.create
    def test_real_http_parity_and_private_routes(self):
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler);server.store=self.store
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();base='http://127.0.0.1:'+str(server.server_port)
        def call(token,path,body=None,origin=None):
            headers={'X-Trace-Token':token}
            if origin:headers['Origin']=origin
            req=urllib.request.Request(base+path,data=None if body is None else json.dumps(body).encode(),headers=headers)
            try:
                with urllib.request.urlopen(req) as r:return json.load(r)
            except urllib.error.HTTPError as e:
                e.close();raise
        try:
            for cohort in ('human','agent'):
                token=self.create(participant=cohort,cohort=cohort);obs=call(token,'/api/next',{})
                answer={'cells':solve(self.store.items[obs['item']['id']])}
                result=call(token,'/api/submit',{'request_id':'http','item_id':obs['item']['id'],'answer':answer});self.assertTrue(result['feedback']['correct'])
                with self.assertRaises(urllib.error.HTTPError):call(token,'/api/next',{},'https://foreign.example')
            for path in ('/data/corpus.json','/benchmark/core.py','/../data/corpus.json','/.git/config'):
                with self.assertRaises(urllib.error.HTTPError):call('',path)
            with self.assertRaises(urllib.error.HTTPError):call('invalid','/api/state')
        finally:server.shutdown();server.server_close();thread.join()
if __name__=='__main__':unittest.main()
