"""دمج تعارضات المزامنة دون الكتابة إلى خدمة الإنتاج."""
import http.server, threading, os, json
from pathlib import Path
from playwright.sync_api import sync_playwright
os.chdir(Path(__file__).resolve().parents[1])
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args): pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Quiet)
threading.Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 page=b.new_page();page.context.route('https://**',lambda r:r.abort())
 page.goto(f'http://127.0.0.1:{server.server_port}',wait_until='domcontentloaded')
 page.wait_for_function('typeof showSyncConflicts==="function"')
 page.evaluate("document.getElementById('hdGate').style.setProperty('display','none','important')")
 result=page.evaluate('''()=>{
 const base={id:'p',name:'base',paidAmount:0,notes:'',updatedAt:1};
 const local={...base,name:'local',updatedAt:2},remote={...base,paidAmount:100,updatedAt:3};
 _cloudBases.clear();_rememberBase('projects:_all',[base]);
 const before=JSON.stringify({base,local,remote});
 const disjoint=_hdMergeById([local],[remote],'projects:_all');
 const untouched=before===JSON.stringify({base,local,remote});
 const metadata=_hdMergeById([{id:'p',name:'same',updatedAt:3}],[{name:'same',id:'p',updatedAt:4}],'metadata');
 const left={...base,paidAmount:100,notes:'local note'},right={...base,paidAmount:200,name:'cloud name'};
 let blocked=false;try{_hdMergeById([left],[right],'projects:_all')}catch(e){blocked=e.code==='SYNC_CONFLICT'}
 const entry=[..._syncConflicts.values()][0];
 window._conflictTest={base,left,right,chosen:null,calls:0,archives:[]};
 _stGet=async()=>null;_svRetry=async(key,value)=>{_conflictTest.archives.push(JSON.parse(value));return true};
 cloudSyncNow=async()=>{_conflictTest.calls++;_conflictTest.chosen=_hdMergeById([left],[right],'projects:_all');return true;};
 showSyncStatus();
 return {disjoint,untouched,metadata,blocked,entry};
 }''')
 assert result['disjoint'][0]['name']=='local' and result['disjoint'][0]['paidAmount']==100
 assert result['untouched'] and result['metadata'][0]['name']=='same'
 assert result['blocked'] and [x['path'] for x in result['entry']['fields']]==['paidAmount']
 assert page.locator('#sync-conflict-dialog').is_visible()
 assert page.locator('#sync-conflict-dialog').inner_text().find('100')>=0
 page.get_by_role('button',name='اعتماد قيمة على هذا الجهاز',exact=True).click()
 page.wait_for_function('_conflictTest.calls===1')
 state=page.evaluate('_conflictTest')
 assert state['chosen'][0]['paidAmount']==100 and state['chosen'][0]['name']=='cloud name' and state['chosen'][0]['notes']=='local note'
 assert state['archives'][0]['snapshots'][0]['local']['paidAmount']==100
 assert state['archives'][0]['snapshots'][0]['cloud']['paidAmount']==200
 result=page.evaluate('''()=>{
 const {base,left,right}=_conflictTest;
 let stale=false;try{_hdMergeById([left],[{...right,paidAmount:300}],'projects:_all')}catch(e){stale=e.code==='SYNC_CONFLICT'}
 _syncResolutions.clear();_conflictTest.calls=0;_svRetry=async()=>false;
 showSyncConflicts();return {stale};
 }''')
 assert result['stale']
 page.get_by_role('button',name='اعتماد قيمة على هذا الجهاز',exact=True).click()
 page.wait_for_function('document.getElementById("toast").textContent.includes("لم يُطبّق")')
 assert page.evaluate('_conflictTest.calls')==0 and page.evaluate('_syncResolutions.size')==0
 result=page.evaluate('''()=>{
 _syncConflicts.clear();
 const base={id:'p',name:'base',payments:[]};
 _rememberBase('payment-test',[base]);
 let paymentBlocked=false;try{_hdMergeById([{...base,payments:[{id:'a',amount:100}]}],[{...base,payments:[{id:'b',amount:100}]}],'payment-test')}catch(e){paymentBlocked=e.code==='SYNC_CONFLICT'}
 _rememberBase('delete-test',[{id:'p',value:1}]);
 let deleteBlocked=false;try{_hdMergeById([],[{id:'p',value:2}],'delete-test')}catch(e){deleteBlocked=e.code==='SYNC_CONFLICT'}
 const deleted=_hdMergeById([],[{id:'p',value:1}],'delete-test');
 return {paymentBlocked,deleteBlocked,deleted};
 }''')
 assert result['paymentBlocked'] and result['deleteBlocked'] and result['deleted']==[]
 b.close()
server.shutdown()
print('PASS disjoint field merge, metadata/key order, same-field conflict UI, archive before resolution, choice preserves independent edits, stale choice rejected, failed archive blocks writes, financial payment conflict, deletion conflict')
