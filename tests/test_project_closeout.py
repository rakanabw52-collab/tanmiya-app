"""Synthetic closeout lifecycle: snapshot arithmetic, stale review, locks, printing, reopening and persistence."""
import http.server,threading,os
from pathlib import Path
from playwright.sync_api import sync_playwright
os.chdir(Path(__file__).resolve().parents[1])
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Quiet);threading.Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=b.new_page();page.route('https://**',lambda r:r.abort());page.goto(f'http://127.0.0.1:{server.server_port}');page.wait_for_function('typeof openProjectCloseout==="function" && typeof renderBuy1077==="function"');page.wait_for_timeout(400)
 page.evaluate('''()=>{document.getElementById('hdGate').style.setProperty('display','none','important');window.HD_ROLE='owner';window.HD_USER='مالك اختبار';_cloudOn=false;projs=[{id:'close-test',name:'مشروع اختبار إقفال',status:'done',quantity:1000,unit:'م.ط',contractValue:100000,paidAmount:115000}];invs=[{id:'exp',projectId:'close-test',type:'expense',number:'EXP1',date:'2026-11-01',subtotal:60000,vat:9000,total:69000,vatRecoverable:true}];window.opsData={suppliers:[],claims:[],purchaseOrders:[],changeOrders:[],subcontracts:[],budgets:[]};progress=[];showProj('close-test');}''')
 page.get_by_role('button',name='🔒 الإقفال النهائي للمشروع',exact=True).click()
 data=page.evaluate("projectCloseoutSnapshot('close-test')")
 assert {k:data[k] for k in ['costGross','recoverableVAT','costNet','profitBeforeTaxCredit','profit','margin','costPerUnit','pricePerUnit']}=={'costGross':69000,'recoverableVAT':9000,'costNet':60000,'profitBeforeTaxCredit':31000,'profit':40000,'margin':40,'costPerUnit':60,'pricePerUnit':100},data
 assert page.evaluate('approveProjectCloseout()') is False
 page.locator('[data-close-check]').check() if page.locator('[data-close-check]').count()==1 else None
 for checkbox in page.locator('[data-close-check]').all():checkbox.check()
 assert page.evaluate('approveProjectCloseout()') is True
 assert page.evaluate("projs[0].closeout.status")== 'closed'
 assert page.evaluate("projs[0].closeout.reports[0].profit")==40000
 guard=page.evaluate('''async()=>{projs[0].contractValue=110000;const a=await svPDetailed();invs[0].vatRecoverable=false;const b=await svDetailed();window.opsData.purchaseOrders.push({id:'bad',projectId:'close-test',total:500});const c=await svOps(false);return {a:a.ok,b:b.ok,c:c.ok,net:projs[0].contractValue,selected:invs[0].vatRecoverable,orders:window.opsData.purchaseOrders.length};}''')
 assert guard=={'a':False,'b':False,'c':False,'net':100000,'selected':True,'orders':0},guard
 assert page.evaluate("_archiveProjectDelete('close-test')") is False
 with page.expect_popup() as popup:page.locator('[data-pc-action="print"]').click()
 printed=popup.value;assert '40,000' in printed.locator('body').inner_text() and 'كشف معتمد محفوظ' in printed.locator('body').inner_text();printed.close()
 assert page.evaluate('reopenProjectCloseout()') is False
 page.locator('#project-closeout-reason').fill('تصحيح فاتورة بعد مراجعة المستند')
 assert page.evaluate('reopenProjectCloseout()') is True
 assert page.evaluate("projs[0].closeout.reports[0].profit")==40000
 page.evaluate('''async()=>{invs[0].total=70000;invs[0].subtotal=61000;await svDetailed();openProjectCloseout('close-test');}''')
 for checkbox in page.locator('[data-close-check]').all():checkbox.check()
 assert page.evaluate('approveProjectCloseout()') is True
 assert page.evaluate("projs[0].closeout.reports.map(x=>x.profit)")==[40000,39000]
 page.reload();page.wait_for_function("projs.some(p=>p.id==='close-test') && typeof openProjectCloseout==='function'")
 assert page.evaluate("projs[0].closeout.reports.length")==2
 assert page.evaluate("(async()=>{projs[0].paidAmount=0;const r=await svPDetailed();return [r.ok,projs[0].paidAmount]})()")==[False,115000]
 page.evaluate("document.getElementById('hdGate').style.setProperty('display','none','important');openProjectCloseout('close-test')")
 for width in [1280,390,320]:
  page.set_viewport_size({'width':width,'height':900});assert page.locator('.pc-sheet').evaluate('(e)=>e.scrollWidth<=e.clientWidth'),width
 page.screenshot(path='/tmp/project-closeout-1145-mobile.png',full_page=True)
 print('PASS lifecycle, exact tax/profit/unit values, checklist gate, immutable print snapshot, financial source locks, reasoned reopen, second report, reload persistence, mobile fit')
 b.close()
server.shutdown()
