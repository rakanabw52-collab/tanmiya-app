import http.server,threading,json,os
from pathlib import Path
os.chdir(Path(__file__).resolve().parents[1])
from playwright.sync_api import sync_playwright
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args): pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Quiet);threading.Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=b.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://127.0.0.1:'+str(server.server_port),wait_until='domcontentloaded');page.wait_for_function('typeof renderBuy1077 === "function"');page.wait_for_timeout(1200)
 page.evaluate('''()=>{document.getElementById('hdGate').style.setProperty('display','none','important');window.opsData.purchaseOrders=[{id:'a',directPurchase:true,date:'2026-11-01',dueDate:'2026-11-15',projectId:projs[0].id,supplierName:'مورد اختبار',total:115,amount:100,vatRate:15,paid:15,status:'partial',updatedAt:1},{id:'b',directPurchase:true,date:'2026-11-01',dueDate:'2026-12-01',supplierName:'مورد آخر',total:50,paid:50,status:'paid'}];svOps=async()=>({ok:true});hdIsPeriodClosed=()=>false;goTab('proc');renderBuy1077();}''')
 assert page.locator('#h1077-buy tr.buy-unpaid').count()==1
 page.evaluate("setBuyFilter('status','unpaid')");assert page.locator('#h1077-buy tbody tr').count()==1
 page.evaluate("setBuyFilter('from','2026-11-20')");assert page.locator('#h1077-buy tbody tr').count()==0;page.evaluate('resetBuyFilters()')
 page.evaluate("openBuyPayment('a')");page.locator('#pay-account').select_option('1010');page.locator('#pay-amount').fill('30');page.evaluate("saveBuyPayment('a')")
 r=page.evaluate('opsData.purchaseOrders[0]');assert r['paid']==45 and r['payments'][0]['amount']==30 and r['status']=='partial'
 page.evaluate("openBuyPayment('a')");page.locator('#pay-account').select_option('1010');page.locator('#pay-amount').fill('1000');page.evaluate("saveBuyPayment('a')");assert page.evaluate('opsData.purchaseOrders[0].paid')==45
 page.locator('#pay-account').select_option('1010');page.locator('#pay-amount').fill('70');page.evaluate("saveBuyPayment('a')");assert page.evaluate('opsData.purchaseOrders[0].status')=='paid'
 page.evaluate("supplierStatement('name:مورد اختبار')");text=page.locator('#supplier-statement').inner_text();assert '115' in text and '30' in text and '70' in text
 page.evaluate("opsOpen('purchase','a')");assert page.locator('#of-paid').get_attribute('readonly') is not None;assert page.locator('#expense-categories option').count()==9
 # Local persistence failure rolls back the attempted payment.
 page.evaluate("opsData.purchaseOrders[0].paid=45;opsData.purchaseOrders[0].status='partial';svOps=async()=>({ok:false});openBuyPayment('a')")
 page.locator('#pay-account').select_option('1010');page.locator('#pay-amount').fill('10');page.evaluate("saveBuyPayment('a')");assert page.evaluate('opsData.purchaseOrders[0].paid')==45
 print('PASS payment partial/full, invalid excess, failed local-save rollback, supplier ledger, filters, categories')
 # Completed projects freeze their schedule without changing recorded work quantities.
 result=page.evaluate('''()=>{
 const saved={projs,invs,progress,ops:window.opsData};
 projs=[{id:'metrics',name:'مشروع اختبار المؤشرات',status:'done',startDate:'2026-10-20',endDate:'2026-11-06',actualEndDate:'2026-10-27',contractValue:50000,paidAmount:50000,siteExpensesTotal:28372.25,goals:{}}];
 invs=[];progress=[];window.opsData={};
 const time=projTimeStatus(projs[0]),completion=projProgress('metrics'),financial=projPL('metrics');
 showProj('metrics');const text=document.getElementById('pd-body').textContent;
 const bytesBefore=JSON.stringify(progress);
 projs[0].status='active';const reopened=projProgress('metrics').overall;
 projs[0].status='done';delete projs[0].actualEndDate;const missingDate=projTimeStatus(projs[0]);
 window.opsData={changeOrders:[{projectId:'metrics',status:'approved',amount:10000}]};showProj('metrics');
 const changedText=document.getElementById('pd-body').textContent;
 const noProgressMutation=bytesBefore===JSON.stringify(progress);
 projs=saved.projs;invs=saved.invs;progress=saved.progress;window.opsData=saved.ops;
 return {time,completion,financial,text,reopened,missingDate,changedText,noProgressMutation};
 }''')
 assert result['time']['dur']==17 and result['time']['elapsed']==7 and result['time']['remaining']==0
 assert abs(result['time']['timePct']-700/17)<.00001
 assert result['completion']['overall']==100 and result['completion']['recordedOverall']==0
 assert result['reopened']==0 and result['missingDate'] is None and result['noProgressMutation']
 assert result['financial']['outstanding']==7500
 assert 'رصيد ميزانية العقد بعد المصروفات' in result['text'] and 'المتبقي من العقد' not in result['text']
 assert '60,000' in result['changedText'] and '47.3%' in result['changedText']
 print('PASS completed project time/progress, reopening, missing actual date, budget label, change-order denominator, customer balance unchanged')

 # Three-way reconciliation preserves independent edits and detects conflicting changes/deletions.
 result=page.evaluate('''()=>{_cloudBases.clear();_rememberBase('test',[{id:'1',value:'base'},{id:'2',value:'base'}]);let independent=_hdMergeById([{id:'1',value:'local'},{id:'2',value:'base'}],[{id:'1',value:'base'},{id:'2',value:'remote'}],'test');let conflict=false;try{_hdMergeById([{id:'1',value:'local'}],[{id:'1',value:'remote'}],'test')}catch(e){conflict=true}let deleted=_hdMergeById([{id:'2',value:'base'}],[{id:'1',value:'base'},{id:'2',value:'base'}],'test');return {independent,conflict,deleted}}''')
 assert result['independent']==[{'id':'1','value':'local'},{'id':'2','value':'remote'}] and result['conflict'] and len(result['deleted'])==1
 print('PASS three-way independent edits, conflicting edits, deletion propagation')
 # Supabase stub validates stale-write rejection and no false green indicator.
 result=page.evaluate('''async()=>{window.HD_AUTHED=true;_cloudOn=true;_supa={from:()=>({update:()=>({eq:()=>({eq:()=>({select:async()=>({data:[],error:null})})})})})};_cloudVersions.set('invoices:_all','2026-01-01');const cas=await cloudPush('invoices','_all',[]);const oldPull=cloudPullAll,oldPush=cloudPush;cloudPullAll=async()=>({ok:true});cloudPush=async()=>false;const upload=await cloudPushAll();cloudPullAll=oldPull;cloudPush=oldPush;return {cas,upload,badge:document.getElementById('sync-badge').textContent}}''')
 assert not result['cas'] and not result['upload'] and 'مُزامن' not in result['badge']
 print('PASS stale-write rejected, failed upload never says synchronized')
 result=page.evaluate('''async()=>{const saved={load:_bkpLoadHandle,verify:_bkpVerifyPermission,build:buildBackupData};let text='';const h={getFileHandle:async()=>({createWritable:async()=>({write:async s=>{text=s},close:async()=>{}}),getFile:async()=>({text:async()=>text})})};_bkpLoadHandle=async()=>h;_bkpVerifyPermission=async()=>true;buildBackupData=async()=>({invs:[],projs:[],docs:[],lets:[],ops:{},backupWarnings:[]});const ok=await autoBackup(false);const last=localStorage.getItem(_BKP_LAST_KEY);h.getFileHandle=async()=>({createWritable:async()=>({write:async()=>{},close:async()=>{}}),getFile:async()=>({text:async()=>'{broken'})});const corrupt=await autoBackup(false);const unchanged=last===localStorage.getItem(_BKP_LAST_KEY);_bkpLoadHandle=saved.load;_bkpVerifyPermission=saved.verify;buildBackupData=saved.build;const data=await buildBackupData();return {ok,corrupt,unchanged,keys:Object.keys(data)}}''')
 assert result['ok'] and not result['corrupt'] and result['unchanged'];assert all(k in result['keys'] for k in ['coa','journals','progress','auditLog'])
 print('PASS backup read-back, corrupt file rejected, success timestamp unchanged on failure, financial records included')
 # Full read/merge/write pipeline against an in-memory Supabase contract.
 result=page.evaluate('''async()=>{
 const groups=[['invoices','_all',invs],['projects','_all',projs],['settings','main',sett],['progress','_all',progress],['letters','_all',lets],['audit','_all',auditLog],['trash','_all',trash],['audits','_all',audits],['cfo','_all',cfoReports],['coa','_all',coa],['journals','_all',journals],['settings','ops-v1',opsData]];
 const db=new Map(groups.map(([t,id,data])=>[t+':'+id,{id,data:JSON.parse(JSON.stringify(data)),updated_at:'2026-01-01T00:00:00.000Z'}]));
 _cloudBases.clear();localStorage.removeItem(_baseStorageKey());_cloudVersions.clear();window._hdSettingsBase=JSON.stringify(sett);
 _supa={from(table){const q={filters:{},action:'read',payload:null,select(){return this},eq(k,v){this.filters[k]=v;return this},is(k,v){this.filters[k]=v;return this},update(p){this.action='update';this.payload=p;return this},insert(p){this.action='insert';this.payload=p;return this},async maybeSingle(){return {data:db.get(table+':'+this.filters.id)||null,error:null}},then(resolve,reject){const key=table+':'+this.payload.id,old=db.get(key);let data=[];if((this.action==='insert'&&!old)||(this.action==='update'&&old&&old.updated_at===this.filters.updated_at)){db.set(key,JSON.parse(JSON.stringify(this.payload)));data=[{id:this.payload.id,updated_at:this.payload.updated_at}]}return Promise.resolve({data,error:null}).then(resolve,reject)}};return q;}};
 const ok=await cloudPushAll();return {ok,badge:document.getElementById('sync-badge').textContent,written:db.size};}''')
 assert result['ok'] and 'مُزامن' in result['badge'] and result['written']==12,result
 page.evaluate("window._opsView='overview';window._opsProject=projs[0].id;renderOps()")
 assert 'تفاصيل العقد والتكلفة والتحصيل والربح' in page.locator('#ops-body').inner_text()
 assert 'مستحقات مشتريات المشروع' in page.locator('#ops-body').inner_text()
 page.evaluate("supplierStatement('name:مورد اختبار')")
 with page.expect_popup() as popup:
  page.evaluate('printSupplierStatement()')
 printed=popup.value;assert 'كشف حساب — مورد اختبار' in printed.locator('body').inner_text();printed.close()
 print('PASS complete sync round-trip, project detail breakdown, supplier printable document')
 # Missing auxiliary tables use the existing settings table, including safe writes.
 result=page.evaluate('''async()=>{const calls=[];_cloudRoutes.clear();_supa={from(table){calls.push(table);let insert=null;const q={select(){if(insert)return Promise.resolve({data:[{id:insert.id,updated_at:insert.updated_at}],error:null});return this},eq(){return this},insert(p){insert=p;return this},async maybeSingle(){return table==='audit'?{data:null,error:{code:'PGRST205'}}:{data:null,error:null}}};return q;}};const read=await cloudPull('audit','_all');const written=await cloudPush('audit','_all',[{id:'a'}]);return {read,written,calls,route:_cloudRoutes.get('audit:_all')}}''')
 assert result['written'] and result['route']=={'table':'settings','id':'aux:audit:_all'} and result['calls']==['audit','settings','settings'],result
 result=page.evaluate('''async()=>{const calls=[];_cloudRoutes.clear();_cloudReadErrors=[];_supa={from(t){calls.push(t);return {select(){return this},eq(){return this},async maybeSingle(){return {data:null,error:{code:'42501'}}}}}};await cloudPull('audit','_all');return {calls,errors:_cloudReadErrors,route:_cloudRoutes.has('audit:_all')}}''')
 assert result['calls']==['audit'] and not result['route'] and '42501' in result['errors'][0]
 page.evaluate("opsCloseModal();goTab('proc');renderBuy1077()")
 for width in [1024,1280,1600]:
  page.set_viewport_size({'width':width,'height':900});page.wait_for_timeout(100)
  assert page.locator('#sec-proc').evaluate('(e)=>e.getBoundingClientRect().width')>width*.85
  size=page.locator('#h1077-buy .h1077-tw').evaluate('(e)=>({scroll:e.scrollWidth,width:e.clientWidth})')
  assert size['scroll']<=size['width']+1,(width,size)
 page.screenshot(path='/tmp/tanmiya-1109-desktop.png')
 page.set_viewport_size({'width':390,'height':844})
 assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth'), 'Mobile viewport overflows'
 print('PASS missing-table fallback read/write, permission error preserved, desktop table fits 1024/1280/1600, mobile page fits')
 result=page.evaluate('''async()=>{_cloudVersions.set('invoices:_all','2026-01-01');_supa={from:()=>({update(){return this},eq(){return this},select:async()=>({data:null,error:{code:'42501',message:'new row violates row-level security policy <test>'}})})};await cloudPush('invoices','_all',[]);showSyncStatus();return {code:_lastSyncFailure.code,badge:document.getElementById('sync-badge').textContent,details:document.getElementById('sync-details').textContent,html:document.querySelector('#sync-details pre').innerHTML};}''')
 assert result['code']=='42501' and 'invoices' in result['badge'] and '42501' in result['badge']
 assert 'new row violates row-level security policy <test>' in result['details']
 assert '&lt;test&gt;' in result['html']
 print('PASS upload server code preserved, table identified, details dialog renders server message safely')
 assert not errors,errors
 print('PASS no unhandled JavaScript exceptions');b.close()
server.shutdown()
