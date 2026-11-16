"""Review fixes: no missing costs, conservative deduplication, and recoverable writes."""
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
  b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  page=b.new_page(viewport={'width':390,'height':844});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.route('https://**',lambda r:r.abort());page.goto(f'http://127.0.0.1:{server.server_port}');page.wait_for_function('typeof getDataQualityIssues==="function"');page.wait_for_timeout(700)
  result=page.evaluate('''()=>{
   document.getElementById('hdGate').style.display='none';HD_ROLE='owner';_cloudOn=false;HD_AUTHED=false;applyConfirmedUnitPrices=async()=>{};applyConfirmedProjectSettlements=async()=>{};
   projs=[{id:'p',name:'مشروع قائم',status:'active',contractValue:1000},{id:'s',name:'دراسة',status:'study',contractValue:2700000,feasibility:{contractValue:2700000,estTotal:636000}}];
   invs=[{id:'orphan',type:'expense',number:'orphan-1',vendor:'legacy',projectId:'missing',date:'2026-01-01',subtotal:100,vat:0,total:100}];
   opsData={purchaseOrders:[],claims:[],changeOrders:[],budgets:[]};journals=[];trash=[];renderDB();renderProjList();
   const cost=document.getElementById('s-cst').textContent;
   const study=[...document.querySelectorAll('.pcard')].find(x=>x.textContent.includes('دراسة')).textContent;
   showProj('s');const detail=document.querySelector('#pd-body .proj-pl-tot').textContent;closePd();
   return {cost,issues:getDataQualityIssues().map(x=>x.kind),study,detail};
  }''')
  assert result['cost']=='100',result
  assert 'orphan' in result['issues']
  assert '2,064,000' in result['detail'] and '100.0%' not in result['detail'],result
  assert '636,000' in result['study'] and '2,064,000' in result['study'] and '100.0%' not in result['study']
  result=page.evaluate('''()=>{
   const common={type:'purchase',date:'2026-01-01',number:'A-1',subtotal:100,vat:15,total:115,vendorVAT:'300000000000003'};
   invs=[{...common,id:'a',vendor:'الاسم الأول',category:'fuel'},{...common,id:'b',vendor:'قراءة أخرى',category:'other'},{...common,id:'c',number:'A-2'}];
   const groups=findDupInvoices();
   const bad={...common,id:'bad',subtotal:100,vat:15,total:90};
   invs.push(bad);journals=[{id:'j',source:'inv',sourceId:'bad',date:'2026-01-01',lines:[{acc:'1020',debit:90,credit:0},{acc:'4010',debit:0,credit:90}]}];
   const before=JSON.stringify(journals);svJRN=()=>{};_syncInvJournals();
   _cloudBases.clear();localStorage.removeItem(_baseStorageKey());window._hdServerArchive=[{type:'proj',data:{id:'gone'}}];
   let blocked=false;try{_hdMergeById([{id:'gone',name:'deleted'}],[],'projects:_all');}catch(e){blocked=e.code==='SYNC_CONFLICT';}
   _cloudBases.set('projects:_all',[]);let emptyBaseBlocked=false;try{_hdMergeById([{id:'gone',name:'deleted'}],[],'projects:_all');}catch(e){emptyBaseBlocked=e.code==='SYNC_CONFLICT';}
   return {emptyBaseBlocked,groups:groups.map(g=>g.map(i=>i.id)),postBad:_invPostings(bad),unchanged:before===JSON.stringify(journals),blocked};
  }''')
  assert result=={'emptyBaseBlocked':True,'groups':[['a','b']],'postBad':None,'unchanged':True,'blocked':True},result
  page.evaluate('''()=>{invs=invs.filter(i=>i.id!=='bad');journals=[];confirm2=async()=>true;window.failArchive=true;window.failSave=false;window.realReviewArchive=saveReviewArchive;saveReviewArchive=async(k,v)=>failArchive?false:realReviewArchive(k,v);svDetailed=async()=>({ok:!failSave});openDupCheck();}''')
  # Explicit selection required: no silently chosen oldest record.
  page.evaluate('removeDupGroup(0)');assert page.evaluate('invs.length')==3
  page.locator('input[name="dup-keep-0"][value="1"]').check()
  page.evaluate('removeDupGroup(0)');assert page.evaluate('invs.length')==3
  page.evaluate('failArchive=false;failSave=true');page.evaluate('removeDupGroup(0)');assert page.evaluate('invs.length')==3
  page.evaluate('failSave=false');page.evaluate('removeDupGroup(0)')
  assert page.evaluate('invs.map(i=>i.id)')==['b','c']
  assert page.evaluate("trash.some(t=>t.type==='inv'&&t.data.id==='a')")
  # Assignment failure preserves the original group; success changes only linkage.
  page.evaluate('''()=>{document.getElementById('dup-overlay')?.remove();invs=[{id:'o',number:'old',type:'expense',date:'2026-01-01',vendor:'x',projectId:'missing',subtotal:100,vat:0,total:100}];failSave=true;openDataQualityReview();openOrphanAssignment('missing');}''')
  page.locator('#orphan-project-choice').select_option('p');page.evaluate("[...document.querySelectorAll('#data-quality-review button')].find(b=>b.textContent==='حفظ الربط').onclick()")
  assert page.evaluate('invs[0].projectId')=='missing'
  page.evaluate('failSave=false');page.evaluate("[...document.querySelectorAll('#data-quality-review button')].find(b=>b.textContent==='حفظ الربط').onclick()")
  assert page.evaluate('invs[0].projectId')=='p' and page.evaluate('invs[0].total')==100,page.locator('#toast').inner_text()
  page.evaluate("document.getElementById('data-quality-review')?.remove();curProjId='p';editProj()")
  page.locator('#pe-se').fill('10');page.locator('#pe-vat-recovery').select_option('no');page.locator('#pe-se-date').fill('')
  page.evaluate('savePe()');assert 'تاريخ المصروفات' in page.locator('#toast').inner_text()
  assert page.evaluate("projs.find(p=>p.id==='p').siteExpensesTotal||0")==0
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  assert not errors,errors
  b.close()
finally:server.shutdown()
print('PASS: orphan costs included, feasible study profit, VAT-identity duplicates, distinct invoice numbers preserved, bad journals blocked, archived resurrection blocked, dedup selection/backup/rollback, bulk reassignment rollback, mobile.')
