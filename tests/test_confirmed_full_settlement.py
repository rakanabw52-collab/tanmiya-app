"""Owner-confirmed settlement reconciles corrected contracts without duplicate collection."""
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
  window.HD_ROLE='owner';_cloudOn=false;window.opsData={changeOrders:[],claims:[],purchaseOrders:[]};
  projs=[{id:'q',name:'مشروع القيروان الرياض',status:'done',unit:'م.ط',quantity:4398,contractValue:219900,paidAmount:200000,contractPriceCorrection:{version:1133}},{id:'a',name:'مشروع الأمانة',status:'done',unit:'م.ط',quantity:6498,contractValue:324900,paidAmount:300000,contractPriceCorrection:{version:1133}},{id:'n',name:'الأنوار',status:'done',contractValue:170000,paidAmount:176400},{id:'r',name:'الراكة',status:'done',contractValue:50000,paidAmount:50000}];
  invs=[{id:'qi',projectId:'q',type:'revenue',total:19900},{id:'ai',projectId:'a',type:'revenue',total:24150}];
  const invoiceBefore=JSON.stringify(invs);await applyConfirmedProjectSettlements();await applyConfirmedProjectSettlements();renderDB();
  return {q:projPL('q').outstanding,a:projPL('a').outstanding,qpaid:projPL('q').paid,apaid:projPL('a').paid,invoiceUnchanged:invoiceBefore===JSON.stringify(invs),n:projs[2].paidAmount,r:projs[3].paidAmount,flow:document.getElementById('db-cashflow').textContent,receivable:document.getElementById('r-projects').textContent};
 }''')
 assert result['q']==0 and result['a']==0 and result['qpaid']==252885 and result['apaid']==373635,result
 assert result['invoiceUnchanged'] and result['n']==176400 and result['r']==50000
 assert '26,600' in result['flow'] and 'القيروان' not in result['flow'] and 'الأمانة' not in result['flow']
 assert 'القيروان' not in result['receivable'] and 'الأمانة' not in result['receivable']
 page.reload();page.wait_for_function("projs.some(p=>p.id==='q')")
 assert page.evaluate("projs.find(p=>p.id==='q').confirmedFullSettlement.confirmedCollected")==252885
 failure=page.evaluate('''async()=>{_confirmedSettlementAttempts.clear();projs=[{id:'f',name:'القيروان',status:'done',quantity:4398,contractValue:219900,paidAmount:219900,contractPriceCorrection:{version:1133}}];invs=[];svPDetailed=async()=>({ok:false,err:'test'});await applyConfirmedProjectSettlements();return projs[0].paidAmount;}''')
 assert failure==219900
 print('PASS owner-confirmed full settlement persists once, receipt sources preserved, only 26600 remains, settled projects hidden, failed save rolls back')
 b.close()
server.shutdown()
