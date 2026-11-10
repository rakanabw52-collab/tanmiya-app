"""Actual purchase/order/subcontractor forms persist the explicit recovery choice."""
import http.server,threading,os
from pathlib import Path
from playwright.sync_api import sync_playwright
os.chdir(Path(__file__).resolve().parents[1])
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Quiet);threading.Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=b.new_page();page.route('https://**',lambda r:r.abort());page.goto(f'http://127.0.0.1:{server.server_port}');page.wait_for_function('typeof openProjectCloseout==="function" && typeof renderBuy1077==="function"');page.wait_for_timeout(400)
 result=page.evaluate('''async()=>{
  _cloudOn=false;window.HD_ROLE='owner';projs=[{id:'v',name:'مشروع اختبار',status:'active',contractValue:100000,quantity:1000}];invs=[];window.opsData={suppliers:[{id:'s',name:'مورد',vat:'300000000000003'}],purchaseOrders:[],claims:[],changeOrders:[],subcontractors:[{id:'sub',name:'باطن'}]};
  const set=(id,value)=>document.getElementById(id).value=value;
  opsOpen('purchase','','v');set('of-supplier','s');set('of-no','DIRECT1');set('of-pay','آجل');set('of-vendorvat','300000000000003');document.querySelector('.pi-desc').value='مواد';document.querySelector('.pi-amt').value='100';poItemsRecalc();set('of-vat-recovery','yes');await opsSaveForm();
  const direct=window.opsData.purchaseOrders[0];
  opsOpen('po','','v');set('of-proj','v');set('of-supplier','s');set('of-no','FORMAL1');document.querySelector('.pi-desc').value='أعمال';document.querySelector('.pi-amt').value='200';poItemsRecalc();set('of-vat-recovery','yes');await opsSaveForm();
  const formal=window.opsData.purchaseOrders.find(o=>o.number==='FORMAL1');
  opsOpen('claim','','v');set('of-proj','v');set('of-party','subcontractor');set('of-sub','sub');set('of-gross','300');set('of-ret','0');set('of-paid','0');set('of-status','approved');set('of-vat-recovery','yes');await opsSaveForm();
  const claim=window.opsData.claims[0];return {direct:direct?.vatRecoverable,formal:formal?.vatRecoverable,claim:claim?.vatRecoverable,party:claim?.partyType,tax:projectRecoverableVAT('v')};
 }''')
 assert result=={'direct':True,'formal':True,'claim':True,'party':'subcontractor','tax':90},result
 batch=page.evaluate("""async()=>{openBatchExp('v');document.getElementById('bx-vnd').value='مصروف اختبار';document.getElementById('bx-dt').value='2026-11-01';const input=document.querySelector('#bx-cats input[data-cid]'),cid=input.dataset.cid;input.value='115';document.getElementById('bx-vat-'+cid).value='15';const before=invs.length;await saveBatchExp();const prevented=invs.length===before;document.getElementById('bx-rec-'+cid).value='yes';confirm2=async()=>true;await saveBatchExp();const i=invs.find(i=>i.source==='batch');return {prevented,selected:i?.vatRecoverable,vat:i?.vat,net:i?.subtotal,total:i?.total};}""")
 assert batch=={'prevented':True,'selected':True,'vat':15,'net':100,'total':115},batch
 print('PASS purchase, formal order and subcontractor-claim forms save yes/no; no forced party change; source VAT totals agree')
 b.close()
server.shutdown()
