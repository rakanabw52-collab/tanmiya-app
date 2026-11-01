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
 page.evaluate("openBuyPayment('a')");page.locator('#pay-amount').fill('30');page.evaluate("saveBuyPayment('a')")
 r=page.evaluate('opsData.purchaseOrders[0]');assert r['paid']==45 and r['payments'][0]['amount']==30 and r['status']=='partial'
 page.evaluate("openBuyPayment('a')");page.locator('#pay-amount').fill('1000');page.evaluate("saveBuyPayment('a')");assert page.evaluate('opsData.purchaseOrders[0].paid')==45
 page.locator('#pay-amount').fill('70');page.evaluate("saveBuyPayment('a')");assert page.evaluate('opsData.purchaseOrders[0].status')=='paid'
 page.evaluate("supplierStatement('name:مورد اختبار')");text=page.locator('#supplier-statement').inner_text();assert '115' in text and '30' in text and '70' in text
 page.evaluate("opsOpen('purchase','a')");assert page.locator('#of-paid').get_attribute('readonly') is not None;assert page.locator('#expense-categories option').count()==9
 # Local persistence failure rolls back the attempted payment.
 page.evaluate("opsData.purchaseOrders[0].paid=45;opsData.purchaseOrders[0].status='partial';svOps=async()=>({ok:false});openBuyPayment('a')")
 page.locator('#pay-amount').fill('10');page.evaluate("saveBuyPayment('a')");assert page.evaluate('opsData.purchaseOrders[0].paid')==45
 print('PASS payment partial/full, invalid excess, failed local-save rollback, supplier ledger, filters, categories')
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
 assert not errors,errors
 print('PASS no unhandled JavaScript exceptions');b.close()
server.shutdown()
