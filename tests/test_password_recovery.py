"""Recovery UI with mocked Auth responses: validation, errors, reset, and PIN handoff."""
import http.server, threading, os
from pathlib import Path
from playwright.sync_api import sync_playwright
os.chdir(Path(__file__).resolve().parents[1])
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args): pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Quiet)
threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  page=b.new_page(viewport={'width':390,'height':844});errors=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  page.route('https://**',lambda r:r.abort())
  url=f'http://127.0.0.1:{server.server_port}/index.html'
  page.goto(url);page.wait_for_function('typeof hdShowRecovery==="function"');page.wait_for_timeout(1000)
  # Exercise the real SDK listener (not a hand-written replacement).
  page.evaluate("async()=>{cloudInit();await _supa.auth._notifyAllSubscribers('PASSWORD_RECOVERY',{user:{email:'owner@example.invalid'}})}")
  assert page.locator('#hd-reset-box').is_visible()
  assert page.evaluate('HD_AUTHED') is False
  page.evaluate('''()=>{
   window.calls=[];window.failRecovery=false;window.failReset=false;
   _supa={auth:{
    resetPasswordForEmail:async(email,options)=>{calls.push({email,options});return {error:failRecovery?{status:429}:null};},
    updateUser:async args=>{calls.push({update:true});return failReset?{error:{status:401}}:{data:{user:{email:'owner@example.invalid'}}};},
    signOut:async()=>{calls.push({logout:true});return {};}
   }};
  }''')
  page.evaluate('hdCancelRecovery()');assert page.locator('#hd-pin-box').is_visible()
  page.get_by_role('button',name='نسيت البريد أو كلمة المرور؟',exact=True).first.click()
  page.locator('#hd-recovery-email').fill('invalid');page.evaluate('hdSendRecovery()')
  assert 'صحيحًا' in page.locator('#hd-pin-err').inner_text()
  page.locator('#hd-recovery-email').fill('owner@example.invalid')
  page.evaluate('failRecovery=true');page.evaluate('hdSendRecovery()')
  assert 'طلبات كثيرة' in page.locator('#hd-pin-err').inner_text()
  assert page.locator('#hd-recovery-btn').is_enabled()
  page.evaluate('failRecovery=false');page.evaluate('hdSendRecovery()')
  assert 'ستصلك رسالة' in page.locator('#hd-recovery-status').inner_text()
  assert page.evaluate('calls.at(-1).options.redirectTo')==url
  # Calling reset without the verified recovery event never updates the password.
  page.evaluate('hdResetPassword()');assert 'رابط الاستعادة' in page.locator('#hd-pin-err').inner_text()
  assert not page.evaluate('calls.some(c=>c.update)')
  page.evaluate("HD_RECOVERY_SESSION={user:{email:'owner@example.invalid'}};_hdBox('hd-reset-box')")
  page.locator('#hd-reset-password').fill('new-password-long');page.locator('#hd-reset-confirm').fill('different')
  page.evaluate('hdResetPassword()');assert 'غير مطابق' in page.locator('#hd-pin-err').inner_text()
  assert not page.evaluate('calls.some(c=>c.update)')
  page.locator('#hd-reset-confirm').fill('new-password-long')
  page.evaluate('failReset=true');page.evaluate('hdResetPassword()')
  assert 'انتهت صلاحية' in page.locator('#hd-pin-err').inner_text()
  assert page.locator('#hd-reset-btn').is_enabled()
  page.evaluate('failReset=false');page.evaluate('hdResetPassword()')
  assert page.locator('#hd-account-box').is_visible()
  assert page.locator('#hd-email').input_value()=='owner@example.invalid'
  assert 'تم تغيير' in page.locator('#hd-recovery-status').inner_text()
  assert page.locator('#hd-reset-password').input_value()==''
  assert page.locator('#hd-reset-confirm').input_value()==''
  assert page.evaluate('HD_RECOVERY_SESSION') is None
  assert page.evaluate('HD_AUTHED') is False
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  assert not errors,errors
  b.close()
finally:server.shutdown()
print('PASS: recovery link request, rate limit, SDK recovery event, validation, expired session, password update, PIN activation handoff, mobile.')
