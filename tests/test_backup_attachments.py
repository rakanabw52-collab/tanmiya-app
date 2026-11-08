"""اختبار مرفقات النسخ بذاكرة متصفح وملفات مجلد صناعية فقط."""
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
    page=b.new_page();page.route('https://**',lambda r:r.abort())
    page.goto(f'http://127.0.0.1:{server.server_port}',wait_until='domcontentloaded')
    result=page.evaluate('''async()=>{
      invs=[];docs=[];lets=[];projs=[{id:'p',name:'مشروع اختبار',attachments:[
        {fileRef:'inline',fileName:'قديم.pdf',fileData:'data:application/pdf;base64,YWJj'},
        {fileRef:'missing',fileName:'<img src=x onerror=alert(1)>.pdf'}]}];
      const originalGet=_fileGet;_fileGet=async()=>null;
      const built=await buildBackupData(Infinity);
      const capped=await buildBackupData(1);
      const files=new Map(),names=[];let corrupt=false;
      _bkpLoadHandle=async()=>({name:'test',getFileHandle:async(name)=>{names.push(name);return {
        createWritable:async()=>({write:async text=>files.set(name,text),close:async()=>{}}),
        getFile:async()=>({text:async()=>corrupt?'{broken':files.get(name)})};}});
      _bkpVerifyPermission=async()=>true;
      localStorage.setItem(_BKP_LAST_KEY,'123');localStorage.setItem('hd-backup-verified','123');
      const partialResult=await autoBackup(true);
      const partial=JSON.parse(localStorage.getItem('hd-backup-partial-v1'));
      const afterPartial={last:localStorage.getItem(_BKP_LAST_KEY),verified:localStorage.getItem('hd-backup-verified'),
        status:document.getElementById('backup-status').textContent,
        unsafeImages:document.querySelectorAll('#backup-status img').length};
      const partialData=JSON.parse(files.get(names[0]));
      corrupt=true;await autoBackup(false);
      const corruptDidNotAdvance=JSON.parse(localStorage.getItem('hd-backup-partial-v1')).at===partial.at;
      corrupt=false;_fileGet=async()=>new Blob(['available'],{type:'application/pdf'});
      const completeResult=await autoBackup(false);
      const cleared=!localStorage.getItem('hd-backup-partial-v1');
      _fileGet=originalGet;
      return {built,capped,partialResult,partial,afterPartial,partialData,names,corruptDidNotAdvance,completeResult,cleared};
    }''')
    assert result['built']['filesCount']==1 and 'inline' in result['built']['files']
    assert not result['built']['backupComplete'] and len(result['built']['backupMissingFiles'])==1
    assert result['capped']['backupMissingFiles'][0]['reason']=='مرفق يتجاوز حد حجم التصدير'
    assert not result['partialResult'] and 'غير_مكتملة' in result['names'][0]
    assert result['afterPartial']['last']=='123' and result['afterPartial']['verified']=='123'
    assert result['afterPartial']['unsafeImages']==0 and 'نسخة غير مكتملة' in result['afterPartial']['status']
    assert result['partialData']['filesCount']==1 and len(result['partialData']['backupWarnings'])==1
    assert result['corruptDidNotAdvance'] and result['completeResult'] and result['cleared']
    assert 'غير_مكتملة' not in result['names'][-1]
    b.close()
server.shutdown()
print('PASS inline attachment fallback, size warnings, separate partial file, complete backup preserved, read-back validation, escaped missing list, complete recovery')
