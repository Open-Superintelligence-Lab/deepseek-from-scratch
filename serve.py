"""Local course server with atomic, versioned text saves. Bind to loopback only."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import json, os, re, threading, tempfile
from datetime import datetime, timezone
from build_course import build
ROOT=Path(__file__).resolve().parent
STORE=ROOT/'content/text-edits.json'
LOCK=threading.Lock()
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT),**kwargs)
 def end_headers(self):
  self.send_header('Cache-Control','no-cache');super().end_headers()
 def reply(self,status,data):
  raw=json.dumps(data,ensure_ascii=False).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
 def do_GET(self):
  if self.path.split('?')[0] in ('/', '/index.html'):
   try:
    with LOCK:build(ROOT)
   except (ValueError, OSError) as e:return self.reply(500,{'error':'Course build failed: '+str(e)})
  if self.path=='/api/text-edits':
   with LOCK:data=json.loads(STORE.read_text()) if STORE.exists() else {'edits':{}}
   return self.reply(200,data)
  return super().do_GET()
 def do_POST(self):
  if self.path!='/api/text-edits':return self.reply(404,{'error':'Unknown endpoint'})
  if self.headers.get('Origin') not in ('http://127.0.0.1:8766','http://localhost:8766') or self.headers.get('Content-Type')!='application/json':return self.reply(403,{'error':'Local course requests only'})
  try:
   size=int(self.headers.get('Content-Length','0'))
   if not 0<size<100000:raise ValueError('Invalid size')
   data=json.loads(self.rfile.read(size));key=data['id'];text=data['text']
   allowed=set(re.findall(r'data-edit-id="([^"]+)"',(ROOT/'index.html').read_text()))
   if key not in allowed or not isinstance(text,str) or len(text)>30000:raise ValueError('Invalid field')
   with LOCK:
    state=json.loads(STORE.read_text()) if STORE.exists() else {'edits':{}}
    stamp=datetime.now(timezone.utc).isoformat()
    with (ROOT/'content/text-edit-history.jsonl').open('a') as f:f.write(json.dumps({'at':stamp,'id':key,'before':state['edits'].get(key),'after':text},ensure_ascii=False)+'\n')
    state['edits'][key]=text;state['saved_at']=stamp
    fd,name=tempfile.mkstemp(dir=STORE.parent,prefix='.text-edits-')
    with os.fdopen(fd,'w') as f:json.dump(state,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
    os.replace(name,STORE)
   self.reply(200,{'saved_at':stamp})
  except (ValueError,KeyError,json.JSONDecodeError) as e:self.reply(400,{'error':str(e)})
if __name__=='__main__':
 build(ROOT)
 print('Course + text autosave: http://127.0.0.1:8766/',flush=True)
 ThreadingHTTPServer(('127.0.0.1',8766),Handler).serve_forever()
