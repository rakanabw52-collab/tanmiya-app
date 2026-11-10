"""VAT recovery is an explicit per-expense choice, consistent across profit, unit cost and closeout."""
import http.server,threading,os
from pathlib import Path
from playwright.sync_api import sync_playwright
os.chdir(Path(__file__).resolve().parents[1])
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Quiet);threading.Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=b.new_page();page.route('https://**',lambda r:r.abort());page.goto(f'http://127.0.0.1:{server.server_port}');page.wait_for_function('typeof openProjectCloseout==="function" && typeof renderBuy1077==="function"');page.wait_for_timeout(400)
 page.evaluate('''()=>{document.getElementById('hdGate').style.setProperty('display','none','important');window.HD_ROLE='owner';_cloudOn=false;projs=[{id:'v',name:'اختبار اختيار الضريبة',status:'done',quantity:1000,unit:'م.ط',contractValue:100000,paidAmount:115000}];invs=[{id:'e',projectId:'v',number:'E',type:'expense',date:'2026-11-01',vendor:'مورد',vendorVAT:'300000000000003',subtotal:1000,vat:150,vatRate:15,total:1150}];window.opsData={suppliers:[],claims:[],purchaseOrders:[],changeOrders:[]};renderDB();showDet('e');}''')
 assert page.evaluate("projectRecoverableVAT('v')")==0
 assert page.evaluate("projPL('v').costNet")==1150
 selector=page.locator('#det-body select')
 selector.select_option('yes');page.wait_for_function('invs[0].vatRecoverable===true')
 assert page.evaluate("[projPL('v').costNet,projectCloseoutSnapshot('v').costNet,projectRecoverableVAT('v')]")==[1000,1000,150]
 page.locator('#det-body select').select_option('no');page.wait_for_function('invs[0].vatRecoverable===false')
 assert page.evaluate("[projPL('v').costNet,projectCloseoutSnapshot('v').costNet]")==[1150,1150]
 page.evaluate("closeDet();qEditInv('e')");assert page.locator('#qe-vat-recovery').input_value()=='no'
 page.locator('#qe-vat-recovery').select_option('yes');page.evaluate('saveQe()');page.wait_for_function('invs[0].vatRecoverable===true')
 page.evaluate("showProj('v');editProj()")
 page.locator('#pe-se').fill('2300');page.locator('#pe-vat-recovery').select_option('yes');page.locator('#pe-expense-vat').fill('300');page.evaluate('savePe()');page.wait_for_function('projs[0].siteVATRecoverable===true')
 assert page.evaluate("[projPL('v').costNet,projectCloseoutSnapshot('v').recoverableVAT,projectCloseoutSnapshot('v').profit]")==[2000,300,98000]
 page.evaluate("showProj('v');editProj()");assert page.locator('#pe-vat-recovery').input_value()=='yes' and page.locator('#pe-expense-vat').input_value()=='300'
 # Pure source examples include manual override and linked PO de-duplication.
 source=page.evaluate('''()=>{window.opsData.purchaseOrders=[{id:'po',projectId:'v',total:1150,vat:150,vatRecoverable:true},{id:'linked',projectId:'v',invoiceId:'e',total:1150,vat:150,vatRecoverable:true}];window.opsData.claims=[{id:'sub',projectId:'v',partyType:'subcontractor',total:1150,vat:150,vatRecoverable:true,status:'approved'}];const p=projPL('v'),r=projectCloseoutSnapshot('v');return [p.cost,p.costNet,p.costPerUnit,r.costNet,r.recoverableVAT];}''')
 assert source==[4600,4000,4,4000,600],source
 # A locked period blocks changing the invoice selection.
 page.evaluate("window.opsData.periods=[{month:'2026-11',status:'closed'}]")
 assert page.evaluate("setInvoiceVATRecovery('e','no')") is False
 assert page.evaluate('invs[0].vatRecoverable') is True
 print('PASS no automatic deduction from supplier VAT; yes/no UI persists; manual override, linked POs, subcontract costs and unit/closeout totals agree; closed period blocked')
 b.close()
server.shutdown()
