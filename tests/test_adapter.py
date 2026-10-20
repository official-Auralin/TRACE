import json,os,subprocess,sys,tempfile,threading,time,unittest
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from benchmark.evaluate import run_adapter
from benchmark.runtime import StudyStore
from benchmark.paths import ROOT
from benchmark.game import solve

class Provider(BaseHTTPRequestHandler):
    def log_message(self,*a):pass
    def do_POST(self):
        body=json.loads(self.rfile.read(int(self.headers['Content-Length'])));self.server.calls.append(body)
        if self.server.probe and len(self.server.calls)==1:action={'probe':{'changes':{}}}
        else:action=getattr(self.server,'action',{'answer':{'cells':[]}})
        response={'model':getattr(self.server,'returned_model','mock-snapshot'),'choices':[{'message':{'content':json.dumps(action)},'finish_reason':getattr(self.server,'finish_reason','stop')}],'usage':{'total_tokens':10}}
        raw=json.dumps(response).encode();self.send_response(200);self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)

class AdapterTests(unittest.TestCase):
    def test_local_mock_provider_through_real_runner(self):
        for condition in ('reasoning','probe'):
            with self.subTest(condition=condition),tempfile.TemporaryDirectory() as temp:
                store=StudyStore(Path(temp)/'study.sqlite3');token=store.create('agent','mock','pilot','pilot-01',condition,metadata={'system_id':'mock'})['token'];obs=store.act(token,'next')
                provider=ThreadingHTTPServer(('127.0.0.1',0),Provider);provider.calls=[];provider.probe=condition=='probe';thread=threading.Thread(target=provider.serve_forever,daemon=True);thread.start()
                try:
                    env={'TRACE_API_BASE':f'http://127.0.0.1:{provider.server_port}/v1','TRACE_API_KEY':'LOCAL-MOCK-ONLY','TRACE_MODEL':'mock-snapshot','TRACE_GENERATION_JSON':'{"max_completion_tokens":100}'}
                    transcript=[]
                    with patch.dict(os.environ,env):run_adapter(store,token,obs,[sys.executable,str(ROOT/'adapters/chat_completions.py')],transcript)
                    self.assertFalse(store.act(token,'state')['active']);self.assertEqual(len(provider.calls),2 if provider.probe else 1)
                    self.assertNotIn('tools',provider.calls[0]);self.assertFalse(provider.calls[0]['store']);self.assertNotIn('LOCAL-MOCK-ONLY',json.dumps(transcript))
                    message=json.loads(provider.calls[0]['messages'][1]['content']);self.assertNotIn('key',message['item']);self.assertEqual(message['item'],obs['item'])
                    if provider.probe:
                        with store.connect() as c:events=[json.loads(r[0]) for r in c.execute('SELECT payload FROM events')]
                        self.assertEqual([r for r in events if r['record_type']=='trial'][-1]['probes_used'],1)
                finally:provider.shutdown();provider.server_close();thread.join()
    def test_truncation_and_snapshot_mismatch(self):
        for case in ('length','snapshot'):
            with self.subTest(case=case),tempfile.TemporaryDirectory() as temp:
                store=StudyStore(Path(temp)/'db.sqlite3');token=store.create('agent','fixture','pilot','pilot-01',metadata={'system_id':'mock'})['token'];obs=store.act(token,'next')
                provider=ThreadingHTTPServer(('127.0.0.1',0),Provider);provider.calls=[];provider.probe=False
                provider.action={'answer':{'cells':solve(store.items[obs['item']['id']])}}
                provider.finish_reason='length' if case=='length' else 'stop';provider.returned_model='different' if case=='snapshot' else 'mock-snapshot'
                thread=threading.Thread(target=provider.serve_forever,daemon=True);thread.start()
                try:
                    env={'TRACE_API_BASE':f'http://127.0.0.1:{provider.server_port}/v1','TRACE_API_KEY':'LOCAL-MOCK-ONLY','TRACE_MODEL':'mock-snapshot','TRACE_GENERATION_JSON':'{"max_completion_tokens":100}'}
                    transcript=[]
                    with patch.dict(os.environ,env):run_adapter(store,token,obs,[sys.executable,'-B',str(ROOT/'adapters/chat_completions.py')],transcript)
                    with store.connect() as connection:trial=[json.loads(row[0]) for row in connection.execute('SELECT payload FROM events') if json.loads(row[0])['record_type']=='trial'][-1]
                    self.assertEqual(trial['status'],'submitted' if case=='length' else 'technical_error')
                    self.assertEqual(trial['correct'],False if case=='length' else None)
                    metadata=json.loads([event['raw'] for event in transcript if event['direction']=='from_adapter'][-1])['_metadata']
                    self.assertIn('request_started_at',metadata);self.assertIn('response_received_at',metadata);self.assertEqual(len(provider.calls),1)
                finally:provider.shutdown();provider.server_close();thread.join()
    def test_malformed_adapter_final_is_wrong(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'bad.py';path.write_text('print("not-json",flush=True)')
            store=StudyStore(Path(temp)/'db.sqlite3');token=store.create('agent','mock','pilot','pilot-01',metadata={'system_id':'mock'})['token'];obs=store.act(token,'next')
            run_adapter(store,token,obs,[sys.executable,str(path)],[])
            with store.connect() as c:trials=[json.loads(r[0]) for r in c.execute('SELECT payload FROM events') if json.loads(r[0])['record_type']=='trial']
            self.assertEqual(len(trials),1);self.assertFalse(trials[0]['correct']);self.assertEqual(trials[0]['status'],'submitted')
if __name__=='__main__':unittest.main()
