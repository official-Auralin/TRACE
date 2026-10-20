"""Local researcher-operated study server. Only web assets and token-scoped actions are served."""
import argparse,hashlib,json,threading
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from .paths import ROOT
from .runtime import StudyStore,StudyError

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass  # Never put participant session tokens in access logs.
    def respond(self,status,obj,content_type='application/json'):
        data=json.dumps(obj).encode() if content_type=='application/json' else obj
        self.send_response(status);self.send_header('Content-Type',content_type);self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff');self.send_header('Content-Length',str(len(data)))
        self.end_headers();self.wfile.write(data)
    def do_GET(self):
        if self.path=='/api/state':
            try:self.respond(200,self.server.store.act(self.headers.get('X-Trace-Token',''),'state'))
            except StudyError as e:self.respond(400,{'error':str(e)})
            return
        assets={'/':('index.html','text/html; charset=utf-8'),'/app.js':('app.js','text/javascript; charset=utf-8'),'/board.js':('board.js','text/javascript; charset=utf-8'),'/style.css':('style.css','text/css; charset=utf-8')}
        if self.path not in assets:self.respond(404,{'error':'not found'});return
        name,mime=assets[self.path];data=(ROOT/'web'/name).read_bytes()
        expected=self.server.store.provenance['files_sha256'].get('web/'+name)
        if hashlib.sha256(data).hexdigest()!=expected:
            self.respond(409,{'error':'Participant assets changed after server startup; preserve the frozen session and restart with its release'});return
        self.respond(200,data,mime)
    def do_POST(self):
        if self.path not in ('/api/next','/api/submit','/api/probe','/api/withdraw','/api/navigate'):
            self.respond(404,{'error':'not found'});return
        # Same-origin browser requests only; non-browser agent clients may omit Origin.
        origin=self.headers.get('Origin')
        if origin and origin not in ('http://'+self.headers.get('Host',''),'https://'+self.headers.get('Host','')):
            self.respond(403,{'error':'cross-origin requests forbidden'});return
        try:
            length=int(self.headers.get('Content-Length',0))
            limit=getattr(self.server,'max_request_bytes',None)
            if length<=0:raise StudyError('A positive Content-Length is required')
            if limit is not None and length>limit:
                self.respond(413,{'error':'Request exceeds the configured operator byte budget','status':'resource_exhausted'})
                self.close_connection=True;return
            # Bounded reads avoid a giant up-front buffer allocation. JSON itself
            # is finite and still must fit operator memory; size limits are policy.
            remaining=length;chunks=[]
            while remaining:
                chunk=self.rfile.read(min(remaining,1024*1024))
                if not chunk:raise StudyError('Incomplete request body')
                chunks.append(chunk);remaining-=len(chunk)
            body=json.loads(b''.join(chunks))
            if not isinstance(body,dict):raise StudyError('request must be an object')
            self.respond(200,self.server.store.act(self.headers.get('X-Trace-Token',''),self.path[5:],body))
        except (ValueError,StudyError) as e:self.respond(400,{'error':str(e)})
        except MemoryError:
            self.respond(503,{'error':'Operator memory budget exhausted; no task verdict was inferred','status':'resource_exhausted'})
            self.close_connection=True

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--host',default='127.0.0.1');p.add_argument('--port',type=int,default=8765);p.add_argument('--db',default='runs/study.sqlite3')
    p.add_argument('--dataset',help='Compiled package directory; defaults to data/')
    p.add_argument('--max-request-bytes',type=int,default=None,help='Optional positive operator request budget; no preset size cap')
    a=p.parse_args()
    if a.max_request_bytes is not None and a.max_request_bytes<1:p.error('--max-request-bytes must be positive')
    server=ThreadingHTTPServer((a.host,a.port),Handler);server.store=StudyStore(a.db,dataset=a.dataset);server.max_request_bytes=a.max_request_bytes
    stop=threading.Event()
    def deadlines():
        while not stop.wait(1):server.store.expire_all()
    threading.Thread(target=deadlines,daemon=True).start()
    print(f'TRACE study server: http://{a.host}:{a.port} — create participant sessions with python3 -m benchmark.session create',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:stop.set();server.server_close()
if __name__=='__main__':main()
