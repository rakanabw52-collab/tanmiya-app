"""Profit and margin must share net revenue including unlinked income, without receipt duplication."""
import http.server,threading,os
from pathlib import Path
from playwright.sync_api import sync_playwright
os.chdir(Path(__file__).resolve().parents[1])
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Quiet);threading.Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=b.new_page();page.route('https://**',lambda r:r.abort());page.goto(f'http://127.0.0.1:{server.server_port}');page.wait_for_function('typeof renderBuy1077==="function"');page.wait_for_timeout(400)
 example=page.evaluate('''()=>{
  projs=[{id:'p',name:'اختبار',status:'done',contractValue:1650808,siteExpensesTotal:997757},{id:'study',status:'study',contractValue:9999999}];invs=[{id:'extra',type:'revenue',total:115000,vat:15000},{id:'receipt',type:'revenue',projectId:'p',total:500000,vat:0},{id:'cancelled',type:'revenue',total:999999,status:'cancelled'}];window.opsData={claims:[],purchaseOrders:[],changeOrders:[]};renderDB();return {profit:document.querySelector('#hero-profit .hp-val').textContent,margin:document.querySelector('#hero-profit .hp-tag').textContent,revenue:document.getElementById('s-rev').textContent,cost:document.getElementById('s-cst').textContent,detail:document.querySelector('.profit-calculation').textContent};}''')
 assert example['profit']=='753,051 ر.س' and example['margin']=='هامش 43.0%' and example['revenue']=='1,750,808' and example['cost']=='997,757',example
 assert '100,000' in example['detail'] and 'نسبة الربح' in example['detail']
 net=page.evaluate('''()=>{projs=[{id:'p',status:'done',contractValue:1000}];invs=[{id:'other',type:'revenue',total:230,vat:30},{id:'cost',type:'purchase',projectId:'p',total:115,vat:15,taxDecl:true,vatRecoverable:true},{id:'receipt',type:'revenue',projectId:'p',total:500,vat:0}];renderDB();return {profit:document.getElementById('s-pft').textContent,margin:document.getElementById('m-margin').textContent,revenue:document.getElementById('s-rev').textContent,cost:document.getElementById('s-cst').textContent};}''')
 assert net=={'profit':'1,100','margin':'91.7%','revenue':'1,200','cost':'100'},net
 loss=page.evaluate('''()=>{invs.push({id:'loss',type:'expense',projectId:'p',total:1500,vat:0});renderDB();return {profit:document.getElementById('s-pft').textContent,margin:document.getElementById('m-margin').textContent,label:document.querySelector('#hero-profit .hp-lbl').textContent};}''')
 assert loss['profit']=='-400' and loss['margin']=='-33.3%' and 'صافي الخسارة' in loss['label'],loss
 print('PASS screenshot amounts produce 753051 and 43.0%; net unlinked revenue included; project receipts not double counted; eligible VAT excluded; loss shares same basis')
 b.close()
server.shutdown()
