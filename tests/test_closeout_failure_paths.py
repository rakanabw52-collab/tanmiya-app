"""Closeout failure, role and stale-data gates must never leave a false lock or report."""
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
  document.getElementById('hdGate').style.setProperty('display','none','important');window.HD_ROLE='owner';_cloudOn=false;projs=[{id:'fail',name:'اختبار فشل',status:'done',quantity:1000,contractValue:100000,paidAmount:115000}];invs=[];window.opsData={claims:[],purchaseOrders:[],changeOrders:[],suppliers:[]};progress=[];
  const checkAll=()=>document.querySelectorAll('[data-close-check]').forEach(c=>c.checked=true);
  openProjectCloseout('fail');checkAll();const write=_stSet;_stSet=async()=>({ok:false,err:'test quota'});const failed=await approveProjectCloseout();_stSet=write;
  const noGhost=!projs[0].closeout&&projectCloseAllows('fail');const canSave=(await svPDetailed()).ok;
  openProjectCloseout('fail');checkAll();projs[0].contractValue=110000;const stale=await approveProjectCloseout();projs[0].contractValue=100000;
  window.HD_ROLE='accountant';openProjectCloseout('fail');checkAll();const role=await approveProjectCloseout();window.HD_ROLE='owner';
  projs[0].paidAmount=100000;const due=projectCloseoutSnapshot('fail').blockers.length>0;
  projs[0].paidAmount=115000;projs[0].status='active';const active=projectCloseoutSnapshot('fail').blockers.length>0;
  projs[0].status='done';invs=[{id:'unknown',type:'expense',projectId:'fail',total:100,vat:15}];const choice=projectCloseoutSnapshot('fail').blockers.some(x=>x.includes('استرجاع الضريبة'));
  return {failed,noGhost,canSave,stale,role,due,active,choice,neverApproved:!projs[0].closeout};
 }''')
 assert result=={'failed':False,'noGhost':True,'canSave':True,'stale':False,'role':False,'due':True,'active':True,'choice':True,'neverApproved':True},result
 print('PASS save failure rolls back without ghost lock; stale review, accountant role, outstanding balance, active status and unspecified expense tax block approval')
 b.close()
server.shutdown()
