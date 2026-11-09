"""Daily operating KPIs: net tax basis, study exclusion and payable de-duplication."""
import http.server,threading,os
from pathlib import Path
from playwright.sync_api import sync_playwright
os.chdir(Path(__file__).resolve().parents[1])
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Quiet);threading.Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=b.new_page();page.route('https://**',lambda r:r.abort());page.goto(f'http://127.0.0.1:{server.server_port}');page.wait_for_function('typeof renderBuy1077==="function"');page.wait_for_timeout(400)
 result=page.evaluate('''()=>{
  projs=[{id:'p',name:'نشط',status:'active',contractValue:1000,paidAmount:500,endDate:_addDays(_todayStr(),-1)},{id:'done',name:'منجز',status:'done',contractValue:2000,paidAmount:2300,siteExpensesTotal:500,endDate:'2020-01-01'},{id:'study',name:'دراسة',status:'study',contractValue:90000}];
  invs=[{id:'i',projectId:'p',type:'purchase',total:115,vat:15,taxDecl:true},{id:'manual',projectId:'done',type:'purchase',total:115,vat:15,taxDecl:true},{id:'general',type:'purchase',total:115,vat:15,taxDecl:true,paid:115},{id:'rev',type:'revenue',total:999,vat:100},{id:'cancelled',type:'purchase',total:9999,status:'cancelled'}];
  window.opsData={suppliers:[],changeOrders:[],purchaseOrders:[{id:'linked',invoiceId:'i',projectId:'p',total:115,paid:25,status:'partial',directPurchase:true,taxDecl:true,vat:15},{id:'formal',projectId:'p',total:230,vat:30,taxDecl:true,paid:30},{id:'study-po',projectId:'study',total:9999}],claims:[{id:'sub',partyType:'subcontractor',projectId:'p',total:115,vat:15,taxDecl:true,paid:15,status:'approved'},{id:'draft',partyType:'subcontractor',projectId:'study',total:99999,status:'draft'}]};renderDB();
  return {metrics:dashboardOperatingMetrics(1075),money:[...document.querySelectorAll('#dashboard-money-kpis .kp-v')].map(e=>e.textContent),counts:[...document.querySelectorAll('#dashboard-operating-kpis .mtc-v')].map(e=>e.textContent),summaryMoved:!!document.querySelector('#sec-acc #hero-profit')&&!document.querySelector('#sec-db #s-vat')&&!document.querySelector('#sec-db #m-margin'),note:document.getElementById('dashboard-cost-note').textContent};
 }''')
 assert result['metrics']=={'costNet':1000,'recoverable':75,'payable':505,'active':1,'late':1,'manualUnknown':True},result
 assert result['money']==['3,000','1,000','2,800','650'],result
 assert result['counts']==['1','1','81.2%','505'],result
 assert result['summaryMoved'] and 'اليدوية' in result['note']
 page.evaluate("document.getElementById('hdGate').style.setProperty('display','none','important')")
 for width in [1920,1280,390,320]:
  page.set_viewport_size({'width':width,'height':1000});page.wait_for_timeout(200)
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),width
 page.set_viewport_size({'width':1920,'height':1300});page.screenshot(path='/tmp/dashboard1136.png',full_page=True)
 print('PASS 8 KPIs, net expense basis, study and cancelled exclusion, linked payable counted once, active/late counts, moved summary, desktop/mobile fit')
 b.close()
server.shutdown()
