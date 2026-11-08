"""استعادة المرفقات فقط من ملفات نسخ صناعية دون استيراد السجلات."""
import http.server, threading, os
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
    result=page.evaluate('''async()=>{
      invs=[{id:'current',total:700}];docs=[];lets=[];
      projs=[{id:'project',name:'الأمانة',contractValue:12345,attachments:Array.from({length:10},(_,i)=>({fileRef:'recovery_'+i,fileName:'doc_'+i+'.pdf',fileSize:3}))}];
      const before=JSON.stringify({invs,projs});
      const data={invs:[{id:'outdated',total:1}],projs:[{id:'outdated'}],files:Object.fromEntries(Array.from({length:10},(_,i)=>['recovery_'+i,'data:application/pdf;base64,YWJj']))};
      data.files.unrelated='data:application/pdf;base64,YWJj';
      const missing=await _missingBackupAttachments();
      const entries=[{kind:'file',name:'هدف_بكاب_2026-11-08.json',getFile:async()=>({text:async()=>'{broken'})},
        {kind:'file',name:'هدف_بكاب_2026-11-07.json',getFile:async()=>({text:async()=>JSON.stringify(data)})}];
      const handle={name:'test',async *values(){yield* entries;}};
      const recovery=await _recoverBackupFolderAttachments(handle,missing);
      const built=await buildBackupData(Infinity);
      const unchanged=before===JSON.stringify({invs,projs});
      const extra=await _fileGet('unrelated');
      const noOverwrite=new Map([['recovery_0',{fileSize:3}]]);
      const wrongSize=await _recoverAttachmentData({files:{recovery_0:'data:application/pdf;base64,YWJjZA=='}},noOverwrite);
      const oldMissing=new Map([['legacy',{fileSize:3}]]);
      const legacy=await _recoverAttachmentData({projs:[{attachments:[{fileRef:'legacy',fileData:'data:application/pdf;base64,YWJj'}]}]},oldMissing);
      const readOnlyError=await _recoverBackupFolderAttachments({async *values(){throw Error('permission');}},new Map([['x',{}]]));
      const saved=new Map();_bkpLoadHandle=async()=>({...handle,getFileHandle:async name=>({
        createWritable:async()=>({write:async t=>saved.set(name,t),close:async()=>{}}),
        getFile:async()=>({text:async()=>saved.get(name)})})});
      _bkpVerifyPermission=async()=>true;
      localStorage.setItem('hd-backup-partial-v1',JSON.stringify({at:'1',fileName:'partial.json',warnings:['missing']}));
      const complete=await autoBackup(false);
      return {recovery,remaining:missing.size,built,unchanged,extra:!!extra,wrongSize,leftWrongSize:noOverwrite.size,legacy,readOnlyError,complete,cleared:!localStorage.getItem('hd-backup-partial-v1'),saved:[...saved.values()].map(JSON.parse)};
    }''')
    assert result['recovery']=={'restored':10,'checked':1,'errors':1},result['recovery']
    assert result['remaining']==0 and result['built']['backupComplete'] and result['built']['filesCount']==10
    assert result['unchanged'] and not result['extra']
    assert result['wrongSize']==0 and result['leftWrongSize']==1
    assert result['legacy']==1 and result['readOnlyError']['errors']==1
    assert result['complete'] and result['cleared'] and result['saved'][0]['filesCount']==10
    b.close()
server.shutdown()
print('PASS recovery of 10 missing attachments, exact references, unchanged current records, legacy inline recovery, wrong-size rejection, corrupt backup skipped, permission failure, verified complete backup')
