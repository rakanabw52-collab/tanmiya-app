"""Narrow user-confirmed contract correction persists once and fails safely."""
import http.server,threading,os
from pathlib import Path
from playwright.sync_api import sync_playwright
os.chdir(Path(__file__).resolve().parents[1])
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Quiet)
threading.Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=b.new_page();page.route('https://**',lambda r:r.abort());page.goto(f'http://127.0.0.1:{server.server_port}');page.wait_for_function('typeof renderBuy1077==="function"');page.wait_for_timeout(400)
 result=page.evaluate('''async()=>{
  window.HD_ROLE='owner';_cloudOn=false;invs=[];window.opsData={changeOrders:[]};
  projs=[{id:'q',name:'مشروع القيروان الرياض',status:'done',unit:'م.ط',quantity:4398,contractValue:191217.39,paidAmount:219900,siteExpensesTotal:60000},{id:'a',name:'مشروع الأمانة',status:'done',unit:'م.ط',quantity:6498,contractValue:281869.57,paidAmount:324150,siteExpensesTotal:210000},{id:'other',name:'مشروع آخر',status:'done',quantity:100,contractValue:10000},{id:'different',name:'القيروان آخر',status:'done',quantity:900,contractValue:191217.39}];
  await applyConfirmedUnitPrices();await applyConfirmedUnitPrices();
  return {q:projs[0].contractValue,a:projs[1].contractValue,qp:projPL('q').valuePerUnit,ap:projPL('a').valuePerUnit,paid:projs[0].paidAmount,cost:projPL('q').cost,other:projs[2].contractValue,different:projs[3].contractValue,previous:projs[0].contractPriceCorrection.previousNet};
 }''')
 assert result=={'q':219900,'a':324900,'qp':50,'ap':50,'paid':219900,'cost':60000,'other':10000,'different':191217.39,'previous':191217.39},result
 page.reload();page.wait_for_function("projs.some(p=>p.id==='q')")
 assert page.evaluate("projs.find(p=>p.id==='q').contractValue")==219900
 failure=page.evaluate('''async()=>{_confirmedPriceAttempts.clear();projs=[{id:'f',name:'القيروان',status:'done',quantity:4398,contractValue:191217.39}];svPDetailed=async()=>({ok:false,err:'test'});await applyConfirmedUnitPrices();return projs[0].contractValue;}''')
 assert failure==191217.39
 print('PASS confirmed 50/m net prices persist across reload; idempotent, paid and cost preserved, unrelated project untouched, failed save rolled back')
 b.close()
server.shutdown()
