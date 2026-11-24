"""Invoice number is the owner's global identity, independent of supplier/type/date/amount."""
import http.server,threading,os
from pathlib import Path
from playwright.sync_api import sync_playwright
os.chdir(Path(__file__).resolve().parents[1])
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Quiet)
threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=b.new_page();page.route('https://**',lambda r:r.abort());page.goto(f'http://127.0.0.1:{server.server_port}');page.wait_for_function('typeof refreshInvoiceNumberStatus==="function"');page.wait_for_timeout(500)
  result=page.evaluate('''async()=>{
   document.getElementById('hdGate').style.display='none';_cloudOn=false;HD_ROLE='owner';
   invs=[{id:'old',number:' INV-١۲ ',vendor:'المورد الأول',date:'2026-01-01',total:100,subtotal:100,vat:0,type:'purchase'}];
   const candidate={id:'new',number:'inv-12',vendor:'المورد الثاني',date:'2026-02-01',total:999,subtotal:999,vat:0,type:'revenue'};
   const blocked=!await confirmInvoiceIdentity(candidate,null),sameIdAllowed=await confirmInvoiceIdentity(invs[0],'old');
   invs.push(candidate);const groups=findDupInvoices().length;invs.pop();
   return {blocked,sameIdAllowed,groups,arabic:normalizeInvoiceNumber(' INV-١۲ '),leadingZerosDistinct:normalizeInvoiceNumber('0012')!==normalizeInvoiceNumber('12'),punctuationDistinct:normalizeInvoiceNumber('INV-12')!==normalizeInvoiceNumber('INV12'),friendly:_cloudErrorLabel('invoices',{code:'23514',message:'hd_invoice_numbers_unique_check'})};
  }''')
  assert result['blocked'] and result['sameIdAllowed'] and result['groups']==1,result
  assert result['arabic']=='inv-12' and result['leadingZerosDistinct'] and result['punctuationDistinct']
  assert 'مسجل مسبقًا' in result['friendly']
  page.evaluate("goTab('add')");page.locator('#f-no').fill('inv-12');assert 'مسجلة مسبقًا' in page.locator('#invoice-number-status').inner_text()
  page.get_by_role('button',name='فتح الفاتورة الحالية',exact=True).click();assert page.evaluate('editId')=='old'
  assert page.locator('#invoice-number-status').inner_text()==''
  b.close()
finally:server.shutdown()
print('PASS invoice-number-only identity, Arabic digits, supplier/type/date/amount changes blocked, same-ID update allowed, direct duplicate notice and existing-record action, distinct number formatting preserved.')
