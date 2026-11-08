"""اكتشاف تحديث جديد رغم وجود علامة جلسة قديمة، دون إعادة تحميل تلقائية."""
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
 page=b.new_page();page.context.route('https://**',lambda r:r.abort())
 page.goto(f'http://127.0.0.1:{server.server_port}',wait_until='domcontentloaded')
 page.wait_for_function('typeof smartUpdateCheck==="function"')
 result=page.evaluate('''async()=>{
  const fetchSaved=window.fetch;
  const current=document.querySelector('meta[name="app-build"]');
  current.content='2026-11-08-1116';
  sessionStorage.setItem('hadaf-upd-checked','1');
  let calls=0;window.fetch=async()=>{calls++;return {ok:true,text:async()=>'<meta name="app-build" content="2026-11-08-1118">'}};
  _lastVersionCheck=0;UPD_SHOWN=false;
  await smartUpdateCheck();
  const shown=!!document.getElementById('updBar');
  await smartUpdateCheck();const throttled=calls===1;
  _lastVersionCheck=0;window.dispatchEvent(new Event('focus'));
  await new Promise(r=>setTimeout(r,30));
  const focused=calls===2;
  window.fetch=fetchSaved;
  return {shown,throttled,focused,current:curBuild()};
 }''')
 assert result=={'shown':True,'throttled':True,'focused':True,'current':'2026-11-08-1116'},result
 b.close()
server.shutdown()
print('PASS stale session flag does not hide updates, throttled focus recheck, no automatic reload')
