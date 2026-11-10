"""Local attachment review, explicit tax basis, independent recovery, persistence and safe failure."""
import http.server,threading,os
from pathlib import Path
from playwright.sync_api import sync_playwright
os.chdir(Path(__file__).resolve().parents[1])
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Quiet);threading.Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=b.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.route('https://**',lambda r:r.abort());page.goto(f'http://127.0.0.1:{server.server_port}');page.wait_for_function('typeof openInvoiceVATReview==="function" && typeof renderBuy1077==="function"');page.wait_for_timeout(400)
 page.evaluate('''async()=>{window.confirm=()=>true;document.getElementById('hdGate').style.setProperty('display','none','important');window.HD_ROLE='owner';_cloudOn=false;projs=[{id:'p',name:'مشروع مراجعة محلية',status:'done',contractValue:1000,paidAmount:1150,quantity:1000,attachments:[{id:'a',fileName:'original.png',fileMime:'image/png',fileRef:'local-review-file'},{id:'missing',fileName:'missing.pdf',fileMime:'application/pdf',fileRef:'absent-review-file'}]}];invs=[{id:'one',number:'TEST1',vendor:'مورد أول',type:'expense',date:'2026-11-01',projectId:'p',subtotal:1150,total:1150,vat:0,vatRate:0},{id:'two',number:'TEST2',vendor:'مورد ثان',type:'purchase',date:'2026-11-01',projectId:'p',subtotal:100,total:100,vat:0,paid:100}];window.opsData={claims:[],purchaseOrders:[],changeOrders:[],periods:[]};await _filePut('local-review-file',_dataUrlToBlob('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aP1sAAAAASUVORK5CYII='));await svPDetailed();await svDetailed();openInvoiceVATReview('one');}''')
 assert page.locator('#ivr-attachment').input_value()=='' # A project file is not guessed to belong to this invoice.
 page.locator('#ivr-attachment').select_option('project-att:a');page.wait_for_selector('#ivr-document img');assert page.locator('#ivr-document img').get_attribute('src').startswith('blob:')
 page.locator('#ivr-amount').fill('١١٥٠');page.locator('#ivr-basis').select_option('incl');page.locator('#ivr-method').select_option('rate');page.locator('#ivr-rate').fill('15')
 assert '150 ر.س' in page.locator('#ivr-calculation').inner_text()
 assert page.evaluate('saveInvoiceVATReview()') is False
 page.locator('#ivr-confirm').check();assert page.evaluate('saveInvoiceVATReview()') is True
 first=page.evaluate("(()=>{const i=invs.find(i=>i.id==='one');return {net:i.subtotal,tax:i.vat,total:i.total,choice:i.vatRecoverable??null,old:i.vatReview.before.vat,linked:i.vatReview.attachmentKey,history:i.vatReviewHistory.length}})()")
 assert first=={'net':1000,'tax':150,'total':1150,'choice':None,'old':0,'linked':'project-att:a','history':1},first
 page.evaluate("openInvoiceVATReview('two')");page.locator('#ivr-attachment').select_option('project-att:missing');page.wait_for_function("document.getElementById('ivr-document').textContent.includes('غير متاح')")
 page.locator('#ivr-basis').select_option('excl');page.locator('#ivr-tax').fill('not a number');page.locator('#ivr-confirm').check();assert page.evaluate('saveInvoiceVATReview()') is False
 page.locator('#ivr-amount').fill('200');page.locator('#ivr-basis').select_option('excl');page.locator('#ivr-tax').fill('30');page.locator('#ivr-recover').select_option('yes');page.locator('#ivr-confirm').check();assert page.evaluate('saveInvoiceVATReview()') is True
 assert page.evaluate("(()=>{const i=invs.find(i=>i.id==='two');return [i.subtotal,i.vat,i.total,i.vatRecoverable]})()")==[200,30,230,True]
 # A save failure must not replace the persisted record or append a review.
 page.locator('#ivr-basis').select_option('incl');page.locator('#ivr-tax').fill('10');page.locator('#ivr-confirm').check()
 failure=page.evaluate("(async()=>{const write=_stSet;_stSet=async()=>({ok:false,err:'test quota'});const saved=await saveInvoiceVATReview();_stSet=write;const i=invs.find(i=>i.id==='two');return {saved,tax:i.vat,history:i.vatReviewHistory.length};})()")
 assert failure=={'saved':False,'tax':30,'history':1},failure
 # Concurrent record changes cannot be silently overwritten.
 page.evaluate("openInvoiceVATReview('one');invs.find(i=>i.id==='one').notes='newer edit'");page.locator('#ivr-basis').select_option('incl');page.locator('#ivr-tax').fill('100');page.locator('#ivr-confirm').check();assert page.evaluate('saveInvoiceVATReview()') is False
 assert page.evaluate("invs.find(i=>i.id==='one').vat")==150
 page.evaluate("window.HD_ROLE='accountant';window.ACC_ALLOW=[];openInvoiceVATReview('one')");assert page.locator('#ivr-amount').is_disabled();assert page.evaluate('saveInvoiceVATReview()') is False
 page.evaluate("window.HD_ROLE='owner'")
 page.evaluate("opsData.periods=[{month:'2026-11',status:'closed'}];openInvoiceVATReview('one')");assert page.locator('#ivr-amount').is_disabled();assert page.evaluate('saveInvoiceVATReview()') is False
 page.evaluate("opsData.periods=[];projs[0].closeout={status:'closed'};openInvoiceVATReview('one')");assert page.locator('#ivr-amount').is_disabled();assert page.evaluate('saveInvoiceVATReview()') is False
 page.evaluate("delete projs[0].closeout;openInvoiceVATReview('one')")
 for width in [1440,1024,390,320]:
  page.set_viewport_size({'width':width,'height':1000});assert page.locator('.ivr-sheet').evaluate('(e)=>e.scrollWidth<=e.clientWidth'),width
 page.set_viewport_size({'width':1440,'height':1000});page.screenshot(path='/tmp/invoice-vat-review-1146.png',full_page=True)
 page.evaluate("openInvoiceVATReview('two')");page.locator('#ivr-basis').select_option('incl');page.locator('#ivr-tax').fill('30');page.locator('#ivr-recover').select_option('');page.locator('#ivr-confirm').check();assert page.evaluate('saveInvoiceVATReview()') is True
 assert page.evaluate("invs.find(i=>i.id==='two').vatRecoverable??null") is None
 page.evaluate("openInvoiceVATReview('one')");page.locator('#ivr-basis').select_option('none');page.locator('#ivr-recover').select_option('no');page.locator('#ivr-confirm').check();assert page.evaluate('saveInvoiceVATReview()') is True
 assert page.evaluate("(()=>{const i=invs.find(i=>i.id==='one');return [i.subtotal,i.vat,i.total,i.vatRate]})()")==[1150,0,1150,0]
 page.reload();page.wait_for_function("typeof openInvoiceVATReview==='function' && invs.some(i=>i.id==='two')")
 assert page.evaluate("(()=>{const i=invs.find(i=>i.id==='two');return [i.total,i.vat,i.vatReviewHistory.length]})()")==[230,30,2]
 assert not errors,errors
 print('PASS local blob preview, no guessed attachment match, inclusive/rate and exclusive/manual correction, independent recovery, confirmation, history, failed-save rollback, stale edit and lock guards, persistence, mobile fit')
 b.close()
server.shutdown()
