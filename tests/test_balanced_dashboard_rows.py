"""Balanced dashboard: full width unit table, readable disclosures and consistent responsive rows."""
import http.server,threading,os
from pathlib import Path
from playwright.sync_api import sync_playwright
os.chdir(Path(__file__).resolve().parents[1])
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Quiet);threading.Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=b.new_page();page.route('https://**',lambda r:r.abort());page.goto(f'http://127.0.0.1:{server.server_port}');page.wait_for_function('typeof renderBuy1077==="function"');page.wait_for_timeout(400)
 page.evaluate('''()=>{
  document.getElementById('hdGate').style.setProperty('display','none','important');
  projs=Array.from({length:8},(_,i)=>({id:'layout-'+i,name:'مشروع اختبار '+(i+1),status:'done',quantity:1000+i*100,unit:'م.ط',contractValue:100000,siteExpensesTotal:50000+i*1000,paidAmount:i<3?100000:115000}));invs=[];window.opsData={claims:[],changeOrders:[],purchaseOrders:[]};renderDB();
 }''')
 assert page.locator('.unit-project-table tbody tr').count()==8
 assert not page.locator('#hero-profit details').evaluate('(e)=>e.open')
 assert page.locator('.expense-preview>div').count()==5
 assert page.locator('.expense-more').is_visible()
 assert page.locator('#db-allcats-projs').is_hidden()
 more=page.locator('#r-projects>details');assert more.count()==1 and not more.evaluate('(e)=>e.open')
 more.locator('summary').click();assert more.evaluate('(e)=>e.open');assert more.get_by_text('مشروع اختبار 3',exact=True).is_visible();more.locator('summary').click()
 for width in [1920,1440,1024,900,650,390,320]:
  page.set_viewport_size({'width':width,'height':1100});page.wait_for_timeout(100)
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),width
  if width>1000:
   hero=page.locator('#hero-profit').bounding_box();kpi=page.locator('.dashboard-kpi-panel').bounding_box()
   assert abs(hero['height']-kpi['height'])<2 and hero['x']>kpi['x']
   pair=page.locator('.dashboard-row-pair>div').all();bounds=[x.bounding_box() for x in pair]
   assert abs(bounds[0]['height']-bounds[1]['height'])<2
  unit=page.locator('.dashboard-unit-section').bounding_box();expenses=page.locator('#db-allcats-card').bounding_box()
  assert abs(unit['width']-expenses['width'])<2
 page.set_viewport_size({'width':1440,'height':1200});page.screenshot(path='/tmp/balanced-1142-desktop.png',full_page=True)
 page.set_viewport_size({'width':390,'height':900});page.screenshot(path='/tmp/balanced-1142-mobile.png',full_page=True)
 assert page.locator('#db-cashflow,#db-insights,#db-alerts').count()==0
 print('PASS equal row heights, profit at right, 8-project full width table, expandable unpaid/expense details, removed cards absent, mobile overflow avoided')
 b.close()
server.shutdown()
