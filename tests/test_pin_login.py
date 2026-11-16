"""Four-digit server login on a clean device; legacy local PIN cannot unlock it."""
import http.server, threading, os, json
from pathlib import Path
from playwright.sync_api import sync_playwright
os.chdir(Path(__file__).resolve().parents[1])
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Quiet)
threading.Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 context=b.new_context();page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 mode={'value':'ok'};requests=[]
 def endpoint(route):
  body=json.loads(route.request.post_data or '{}');requests.append(body)
  if mode['value']=='invalid': status,data=401,{'error':'invalid_pin'}
  elif mode['value']=='limited':status,data=429,{'error':'rate_limited','retry_after':900}
  elif mode['value']=='collision':status,data=409,{'error':'pin_unavailable'}
  else:status,data=200,{'ok':True} if body['action']=='register' else {'access_token':'server-session','refresh_token':'server-refresh'}
  route.fulfill(status=status,content_type='application/json',body=json.dumps(data),headers={'access-control-allow-origin':'*'})
 page.route('https://**',lambda r:r.abort());page.route('**/functions/v1/pin-auth',endpoint)
 page.goto(f'http://127.0.0.1:{server.server_port}');page.wait_for_function('typeof hdPinLogin==="function"');page.wait_for_timeout(700)
 assert page.locator('#hd-pin-box').is_visible();assert not page.locator('#hd-account-box').is_visible()
 page.evaluate('''()=>{
  window.testAuth=[];window.testLogins=0;window.testSessions=0;
  _supa={auth:{setSession:async t=>{testSessions++;if(t.access_token!=='server-session')throw Error('unverified tokens');return {data:{session:{access_token:t.access_token,user:{id:'accountant-id',email:'test@example.invalid'}}}};},signInWithPassword:async()=>{testLogins++;return {data:{session:{access_token:'password-session',user:{id:'owner-id',email:'owner@example.invalid'}}}};},signOut:async()=>({})}};
  hdFetchRole=async uid=>uid==='accountant-id'?'accountant':'owner';cloudPullAll=async()=>{};cloudSubscribe=()=>{};
  logEvent=()=>{};localStorage.setItem('hd-local-pin-v1',JSON.stringify({uid:'old',hash:'fake'}));
 }''')
 # Invalid length never reaches server or restores cached sessions.
 page.locator('#hd-pin').fill('123');page.evaluate('hdPinLogin()');assert not requests
 mode['value']='invalid';page.locator('#hd-pin').fill('1234');page.evaluate('hdPinLogin()');assert 'غير صحيح' in page.locator('#hd-pin-err').inner_text();assert page.evaluate('testSessions')==0;assert page.locator('#hdGate').is_visible()
 mode['value']='limited';page.evaluate('hdPinLogin()');assert '15 دقيقة' in page.locator('#hd-pin-err').inner_text()
 mode['value']='ok';page.locator('#hd-pin').fill('١٢٣٤');assert page.locator('#hd-pin').input_value()=='1234';page.evaluate('hdPinLogin()');assert page.evaluate('HD_AUTHED') is True;assert page.evaluate('HD_ROLE')=='accountant';assert requests[-1]=={'action':'login','pin':'1234'};assert not page.locator('#hdGate').is_visible()
 page.evaluate('hdFullLogout()');assert page.locator('#hd-pin-box').is_visible();assert page.evaluate('HD_AUTHED') is False
 # Recovery: a confirmed new PIN, recent account credentials, then server registration.
 page.evaluate('hdShowAccountLogin()');page.locator('#hd-email').fill('owner@example.invalid');page.locator('#hd-pass').fill('test-password');page.locator('#hd-auth-pin').fill('5678');page.locator('#hd-auth-pin2').fill('5679');page.evaluate('hdAccountLogin()');assert page.evaluate('testLogins')==0
 page.locator('#hd-auth-pin2').fill('5678');mode['value']='collision';page.evaluate('hdAccountLogin()');assert 'رمزًا آخر' in page.locator('#hd-pin-err').inner_text();assert page.locator('#hdGate').is_visible();assert page.evaluate('HD_AUTHED') is False
 mode['value']='ok';page.evaluate('hdAccountLogin()');assert page.evaluate('HD_ROLE')=='owner';assert page.evaluate('HD_AUTHED') is True;assert page.locator('#hd-pass').input_value()=='';assert page.locator('#hd-auth-pin').input_value()=='';assert page.evaluate("localStorage.getItem('hd-local-pin-v1')") is None
 # Page reload and a genuinely fresh browser both show only four digits, never per-device setup.
 page.reload();page.wait_for_timeout(500);assert page.locator('#hd-pin-box').is_visible();assert not page.locator('#hd-account-box').is_visible()
 mobile=b.new_context(viewport={'width':390,'height':667});mp=mobile.new_page();mp.route('https://**',lambda r:r.abort());mp.goto(f'http://127.0.0.1:{server.server_port}');mp.wait_for_timeout(700);assert mp.locator('#hd-pin-box').is_visible();assert mp.evaluate('document.documentElement.scrollWidth<=innerWidth');mp.evaluate('hdShowAccountLogin()');mp.locator('#hd-login-btn').scroll_into_view_if_needed();assert mp.locator('#hd-login-btn').is_visible();assert mp.evaluate("document.getElementById('hd-login-btn').getBoundingClientRect().top>=0")
 assert not errors,errors
 b.close()
server.shutdown();print('PASS: fresh device, Arabic digits, wrong PIN, throttling, server tokens, preserved roles, recovery, no saved PIN/password, reload and mobile.')
