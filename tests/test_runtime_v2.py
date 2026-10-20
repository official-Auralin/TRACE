import json,tempfile,unittest
from pathlib import Path
from benchmark.runtime import StudyStore,StudyError
from benchmark.instructions import EXPLANATION_RULES

class RuntimeV2Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.store=StudyStore(Path(self.temp.name)/'study.sqlite3')
    def tearDown(self):self.temp.cleanup()
    def events(self):
        with self.store.connect() as connection:return [json.loads(row[0]) for row in connection.execute('SELECT payload FROM events')]
    def test_withdrawal_before_start_and_between_items_is_exported(self):
        for participant,started in [('before',False),('between',True)]:
            token=self.store.create('human',participant,'pilot','pilot-01')['token']
            if started:
                obs=self.store.act(token,'next');self.store.act(token,'submit',{'request_id':'first','item_id':obs['item']['id'],'answer':{'cells':[]}})
            self.store.act(token,'withdraw');self.store.act(token,'withdraw')
        self.assertEqual(len([event for event in self.events() if event['record_type']=='session_withdrawn']),2)
        self.assertFalse(any(event.get('status')=='withdrawn' for event in self.events()))
        output=Path(self.temp.name)/'events.jsonl';self.store.export(output);self.assertIn('session_withdrawn',output.read_text())
    def test_dispositions_include_unstarted_withdrawal_and_interrupted_trial(self):
        from benchmark.analyze import analyze
        withdrawn=self.store.create('human','withdrawn','pilot','pilot-01')['token'];self.store.act(withdrawn,'withdraw')
        active=self.store.create('human','interrupted','pilot','pilot-01')['token']
        for i in range(2):
            obs=self.store.act(active,'next');self.store.act(active,'submit',{'request_id':str(i),'item_id':obs['item']['id'],'answer':{'cells':[]}})
        self.store.act(active,'next');raw=Path(self.temp.name)/'raw.jsonl';self.store.export(raw)
        report=analyze([raw],Path(self.temp.name)/'report',split='pilot',count=0)
        counts=report['session_events']['human / reasoning']
        self.assertEqual(counts['sessions_created'],2);self.assertEqual(counts['sessions_withdrawn'],1)
        self.assertEqual(counts['scored_items_started'],1);self.assertEqual(counts['started_without_outcome'],1)
    def test_request_audit_provenance_and_frozen_restart(self):
        token=self.store.create('human','audit','pilot','pilot-01')['token'];obs=self.store.act(token,'next')
        request={'request_id':'first','item_id':obs['item']['id'],'answer':{'cells':[]}}
        receipt=self.store.act(token,'submit',request);self.assertEqual(receipt,self.store.act(token,'submit',request))
        with self.assertRaises(StudyError):self.store.act(token,'submit',{**request,'request_id':'second'})
        events=self.events();trial=next(event for event in events if event['record_type']=='trial')
        self.assertEqual(trial['request_id'],'first');self.assertEqual(trial['schema_version'],'trace.trial.v2');self.assertIn('source_provenance',trial)
        self.assertEqual(len([event for event in events if event['record_type']=='request_replayed']),1)
        self.assertEqual(len([event for event in events if event['record_type']=='request_rejected']),1)
        reloaded=StudyStore(self.store.db);reloaded.provenance={}
        with self.assertRaises(StudyError):reloaded.act(token,'state')
    def test_shared_rule_schema_and_no_private_main_feedback(self):
        token=self.store.create('human','rules','pilot','pilot-01')['token']
        for i in range(2):
            obs=self.store.act(token,'next');self.assertEqual(obs['instructions'],EXPLANATION_RULES)
            self.store.act(token,'submit',{'request_id':str(i),'item_id':obs['item']['id'],'answer':{'cells':[]}})
        obs=self.store.act(token,'next');self.assertIn('number_of_inputs',obs['instructions']);self.assertIn('transitions[state][v]',obs['instructions'])
        self.assertNotIn('key',obs['item']);self.assertEqual(len(obs['training_examples']),2)
        receipt=self.store.act(token,'submit',{'request_id':'scored','item_id':obs['item']['id'],'answer':{'verdict':'no_explanation'}})
        self.assertNotIn('feedback',receipt)
if __name__=='__main__':unittest.main()
