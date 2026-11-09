"""Version notifications must be monotonic and acknowledge each release once."""
import http.server,threading,os
from pathlib import Path
from playwright.sync_api import sync_playwright
os.chdir(Path(__file__).resolve().parents[1])
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Quiet)
threading.Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 page=b.new_page();page.route('https://**',lambda r:r.abort())
 page.goto(f'http://127.0.0.1:{server.server_port}',wait_until='domcontentloaded')
 page.wait_for_function('typeof smartUpdateCheck==="function"')
 results=page.evaluate('''async()=>{
  const meta=document.querySelector('meta[name="app-build"]');
  const setBuild=n=>meta.content='2026-11-09-'+n;
  const reset=()=>{document.getElementById('updDoneBar')?.remove();_updatedBannerHandled=false;};
  setBuild(1128);localStorage.setItem('hadaf-seen-build','2026-11-09-1127');
  sessionStorage.setItem('hadaf-upd-shown','1');reset();showUpdatedBanner();
  const first=!!document.getElementById('updDoneBar')&&localStorage.getItem('hadaf-seen-build')===curBuild();
  reset();showUpdatedBanner();const repeated=!document.getElementById('updDoneBar');
  setBuild(1127);reset();showUpdatedBanner();
  const older=!document.getElementById('updDoneBar')&&localStorage.getItem('hadaf-seen-build')==='2026-11-09-1128';
  setBuild(1128);reset();showUpdatedBanner();const recovered=!document.getElementById('updDoneBar');
  const original=fetch;let latest='2026-11-09-1127';
  window.fetch=async()=>({ok:true,text:async()=>'<meta name="app-build" content="'+latest+'">'});
  _lastVersionCheck=0;await checkVersion();const stale=!document.getElementById('updBar');
  latest='2026-11-09-1129';_lastVersionCheck=0;await smartUpdateCheck();
  const newer=document.querySelectorAll('#updBar').length===1;
  _lastVersionCheck=0;await smartUpdateCheck();const single=document.querySelectorAll('#updBar').length===1;
  setBuild(1129);_lastVersionCheck=0;await smartUpdateCheck();const cleared=!document.getElementById('updBar');
  window.fetch=original;return {first,repeated,older,recovered,stale,newer,single,cleared};
 }''')
 assert all(results.values()),results
 print('PASS',results)
 b.close()
server.shutdown()
