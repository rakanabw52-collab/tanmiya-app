"""Explicit cloud snapshot replacement must not merge or upload stale device records."""
import http.server,threading,os,json
from pathlib import Path
from playwright.sync_api import sync_playwright
os.chdir(Path(__file__).resolve().parents[1])
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Quiet)
threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  page=b.new_page();page.route('https://**',lambda r:r.abort());page.on('dialog',lambda d:d.accept())
  page.goto(f'http://127.0.0.1:{server.server_port}');page.wait_for_timeout(1000)
  page.evaluate('''()=>{
   window.HD_AUTHED=true;window.HD_USER='test';_supa={};
   localStorage.setItem(SP,JSON.stringify([{id:'p',contractValue:80500},{id:'local-only'}]));
   window.failRead=true;window.uploads=0;
   _supa.from=()=>{uploads++;throw Error('unexpected upload')};
   cloudPull=async(table,id)=>{
    if(failRead&&table==='settings'){_cloudReadFailed=true;return null;}
    return {data:table==='projects'?[{id:'p',contractValue:100000}]:table==='settings'?{}:[]};
   };
  }''')
  assert page.evaluate('cloudUseServerSnapshot()') is False
  assert page.evaluate("JSON.parse(localStorage.getItem(SP))[0].contractValue")==80500
  assert page.evaluate('uploads')==0
  assert page.evaluate('_cloudReplacing') is False
  page.evaluate('failRead=false')
  # Reload is the final step: inspect persisted storage after it, never stale globals.
  with page.expect_navigation():page.evaluate('cloudUseServerSnapshot()')
  assert page.evaluate("JSON.parse(localStorage.getItem(SP))")==[{'id':'p','contractValue':100000}]
  backups=page.evaluate("Object.keys(localStorage).filter(k=>k.startsWith('hd-before-cloud-replace:')).map(k=>JSON.parse(localStorage.getItem(k)))")
  assert any(json.loads(v['storage']['hd-proj-v1'])[0]['contractValue']==80500 for v in backups)
  assert page.locator('#hd-pin-box').is_visible()
  b.close()
finally:server.shutdown()
print('PASS: failed read keeps local data; complete snapshot replaces rather than merges; local backup retained; no uploads; reload returns to PIN.')
