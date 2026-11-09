"""Exercise actual delayed settings boot instead of replacing the build in a unit test."""
import http.server,threading,os,re
from pathlib import Path
from playwright.sync_api import sync_playwright
os.chdir(Path(__file__).resolve().parents[1])
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Quiet)
threading.Thread(target=server.serve_forever,daemon=True).start()
url=f'http://127.0.0.1:{server.server_port}/index.html'
expected=re.search(r'name="app-build" content="([^"]+)"',Path('index.html').read_text())[1]
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 context=b.new_context(service_workers='block');context.route('https://**',lambda r:r.abort())
 # Reproduce the exact production failure with the previous settings module.
 old=context.new_page();old.route('**/settings.js*',lambda r:r.fulfill(body="setTimeout(()=>{document.querySelector('meta[name=app-build]').content='2026-09-15-1078'},120)",content_type='text/javascript'))
 old.goto(url);old.wait_for_timeout(500)
 assert old.evaluate('curBuild()')=='2026-09-15-1078'
 old.evaluate('_lastVersionCheck=0;smartUpdateCheck()');old.wait_for_selector('#updBar',state='attached');old.close()
 page=context.new_page();page.goto(url);page.wait_for_timeout(1500)
 assert page.evaluate('curBuild()')==expected
 page.evaluate('_lastVersionCheck=0;smartUpdateCheck()');page.wait_for_timeout(300)
 assert page.locator('#updBar').count()==0
 for _ in range(2):
  page.reload();page.wait_for_timeout(1200)
  assert page.evaluate('curBuild()')==expected
  assert page.locator('#updDoneBar').count()==0
  page.evaluate('_lastVersionCheck=0;window.dispatchEvent(new Event("focus"))');page.wait_for_timeout(200)
  assert page.locator('#updBar').count()==0
 print('PASS reproduced old settings overwrite; loaded build stable after settings initialization, repeated reload and focus show no false updates')
 b.close()
server.shutdown()
