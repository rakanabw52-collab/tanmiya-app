"""Regression checks for the second review: no production requests or user data."""
import http.server
import os
import threading
from pathlib import Path
from playwright.sync_api import sync_playwright

os.chdir(Path(__file__).resolve().parents[1])

class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Quiet)
threading.Thread(target=server.serve_forever, daemon=True).start()
failures = []

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
    page = browser.new_page()
    page.context.route("https://**", lambda route: route.abort())
    page.goto(f"http://127.0.0.1:{server.server_port}", wait_until="domcontentloaded")
    page.wait_for_function('typeof renderBuy1077 === "function"')
    page.evaluate("""()=>{
      window._reviewOriginal={
        sv,svP,svDetailed,svPDetailed,_svRetry,confirm2,buildBackupData,
        load:_bkpLoadHandle,verify:_bkpVerifyPermission,missing:_missingBackupAttachments,
        recover:_recoverBackupFolderAttachments
      };
      window._reviewReset=()=>{
        projs=[{id:'p',name:'مشروع اختبار',client:'عميل',status:'active',
          contractValue:1000,startDate:'2026-01-01',attachments:[],goals:{}}];
        invs=[];docs=[];lets=[];progress=[];trash=[];journals=[];auditLog=[];coa=_COA_DEFAULT.map(a=>({...a}));_journalSyncIssues=[];
        window.opsData={purchaseOrders:[],claims:[],changeOrders:[],periods:[]};
        _cloudOn=false;window.HD_AUTHED=false;window.HD_ROLE='owner';
        editId=null;curProjId=null;detId=null;
        _syncConflicts.clear();_syncResolutions.clear();_cloudBases.clear();
        confirm2=async()=>true;sv=async()=>true;svP=async()=>true;
        svDetailed=async()=>({ok:true});svPDetailed=async()=>({ok:true});
        _svRetry=async()=>true;buildBackupData=_reviewOriginal.buildBackupData;
        _bkpLoadHandle=_reviewOriginal.load;_bkpVerifyPermission=_reviewOriginal.verify;
        _missingBackupAttachments=_reviewOriginal.missing;
        _recoverBackupFolderAttachments=_reviewOriginal.recover;
        cloudPushDebounced=()=>{};bumpEdits=async()=>{};
        document.getElementById('hdGate').style.setProperty('display','none','important');
      };
    }""")

    def equal(value, expected):
        assert value == expected, f"expected {expected!r}, got {value!r}"

    def check(name, script, assertion):
        try:
            page.evaluate("_reviewReset()")
            value = page.evaluate(script)
            assertion(value)
            print("PASS", name)
        except Exception as error:
            failures.append(f"{name}: {error}")
            print("FAIL", name, str(error)[:400])

    check("Deleted project keeps blobs and safely restores invoice links", """async()=>{
      projs[0].attachments=[{id:'attachment',fileRef:'review-delete-blob',fileName:'test.pdf'}];
      await _filePut('review-delete-blob',new Blob(['pdf-data'],{type:'application/pdf'}));
      invs=[{id:'moved',type:'expense',projectId:'p',total:10},
            {id:'same',type:'expense',projectId:'p',total:20}];
      editId='p';await delPe();
      const deleted={projectCount:projs.length,links:invs.map(i=>i.projectId),
        blobSize:(await _fileGet('review-delete-blob'))?.size,trashCount:trash.length};
      const trashId=trash.find(x=>x.type==='proj')?.id;
      projs.push({id:'other',name:'مشروع آخر',status:'active',contractValue:100});
      invs[0].projectId='other';
      if(trashId)await restoreTrash(trashId);
      return {deleted,restored:projs.some(p=>p.id==='p'),links:invs.map(i=>i.projectId),
        blobSize:(await _fileGet('review-delete-blob'))?.size,remainingTrash:trash.length};
    }""", lambda r: (
        equal(r["deleted"],{"projectCount":0,"links":["",""],"blobSize":8,"trashCount":1}),
        equal(r["restored"],True),equal(r["links"],["other","p"]),
        equal(r["blobSize"],8),equal(r["remainingTrash"],0)
    ))

    check("Failed project deletion rolls back project, invoice links, trash and blobs", """async()=>{
      projs[0].attachments=[{id:'attachment',fileRef:'review-fail-blob',fileName:'test.pdf'}];
      await _filePut('review-fail-blob',new Blob(['pdf-data'],{type:'application/pdf'}));
      invs=[{id:'linked',type:'expense',projectId:'p',total:10}];
      editId='p';svP=async()=>false;sv=async()=>false;
      svPDetailed=async()=>({ok:false,err:'simulated local failure'});
      svDetailed=async()=>({ok:false,err:'simulated local failure'});_svRetry=async()=>false;
      await delPe();
      return {projectCount:projs.length,link:invs[0].projectId,trashCount:trash.length,
        blobSize:(await _fileGet('review-fail-blob'))?.size};
    }""", lambda r: equal(r,{"projectCount":1,"link":"p","trashCount":0,"blobSize":8}))

    check("Every complete backup has a unique name and corrupt read-back preserves prior good file", """async()=>{
      const files=new Map(),names=[];let corrupt=false,revision=0;
      const handle={name:'test',getFileHandle:async name=>{
        names.push(name);
        return {createWritable:async()=>({write:async text=>files.set(name,text),close:async()=>{}}),
          getFile:async()=>({text:async()=>corrupt?'{broken':files.get(name)})};
      }};
      _bkpLoadHandle=async()=>handle;_bkpVerifyPermission=async()=>true;
      _missingBackupAttachments=async()=>new Map();
      _recoverBackupFolderAttachments=async()=>({restored:0,checked:0,errors:0});
      buildBackupData=async()=>({invs:[],projs:[],docs:[],lets:[],backupWarnings:[],revision:++revision});
      const first=await autoBackup(false),firstName=names[0],firstText=files.get(firstName);
      const second=await autoBackup(false),secondName=names[1],secondText=files.get(secondName);
      const lastGood=localStorage.getItem(_BKP_LAST_KEY);
      const verifiedGood=localStorage.getItem('hd-backup-verified');
      corrupt=true;
      const third=await autoBackup(false);
      return {first,second,third,names,count:files.size,
        firstPreserved:files.get(firstName)===firstText,secondPreserved:files.get(secondName)===secondText,
        timestampPreserved:localStorage.getItem(_BKP_LAST_KEY)===lastGood,
        verifiedPreserved:localStorage.getItem('hd-backup-verified')===verifiedGood};
    }""", lambda r: (
        equal(r["first"],True),equal(r["second"],True),equal(r["third"],False),
        equal(len(set(r["names"])),3),equal(r["firstPreserved"],True),
        equal(r["secondPreserved"],True),equal(r["timestampPreserved"],True),
        equal(r["verifiedPreserved"],True)
    ))

    check("Advanced invoice edit retains cancellation and tax decision", """async()=>{
      invs=[{id:'advanced',type:'purchase',number:'ADV',date:'2026-11-01',
        vendor:'مورد',vendorVAT:'300000000000003',subtotal:100,vat:15,vatRate:15,total:115,
        category:'materials',projectId:'p',notes:'original',taxDecl:false,status:'cancelled',
        cancelledAt:123,sourceId:'original-import'}];
      revInv('advanced');setVatRecovery('f-vat-recovery',false);document.getElementById('f-nt').value='changed note';await saveInv();
      return {taxDecl:invs[0].taxDecl,status:invs[0].status,cancelledAt:invs[0].cancelledAt,
        sourceId:invs[0].sourceId,notes:invs[0].notes,total:invs[0].total};
    }""", lambda r: equal(r,{"taxDecl":False,"status":"cancelled","cancelledAt":123,
                              "sourceId":"original-import","notes":"changed note","total":115}))

    check("Tax declaration decision cannot change in a closed accounting period", """async()=>{
      invs=[{id:'tax',type:'purchase',number:'TAX',date:'2026-11-01',vendor:'مورد',
        subtotal:100,vat:15,vatRate:15,total:115,taxDecl:false}];
      opsData.periods=[{month:'2026-11',status:'closed'}];detId='tax';
      await toggleTaxDecl();
      return {taxDecl:invs[0].taxDecl};
    }""", lambda r: equal(r,{"taxDecl":False}))

    check("General operating purchase agrees between main and annual costs", """()=>{
      opsData.purchaseOrders=[{id:'general-po',directPurchase:true,projectId:'',
        date:'2026-11-01',supplierName:'مورد',amount:100,vat:15,total:115,paid:0,status:'open'}];
      renderDB();
      return {dashboard:document.getElementById('s-cst').textContent,annual:_finReal(2026).cost};
    }""", lambda r: equal(r,{"dashboard":"115","annual":115}))

    check("Mixed conflict choices cannot separate paid total from payment ledger", """()=>{
      const base={id:'po',total:500,paid:100,status:'partial',payments:[{id:'base',amount:100}]};
      const left={...base,paid:150,payments:[...base.payments,{id:'left',amount:50}]};
      const right={...base,paid:170,payments:[...base.payments,{id:'right',amount:70}]};
      _rememberBase('ops:purchaseOrders',[base]);
      let firstBlocked=false;
      try{_hdMergeById([left],[right],'ops:purchaseOrders');}
      catch(e){firstBlocked=e.code==='SYNC_CONFLICT';}
      const entry=[..._syncConflicts.values()].find(x=>x.recordId==='po');
      if(!entry)return {firstBlocked,consistent:false,rejected:false};
      for(const field of entry.fields){
        const choice=field.path==='payments'?'cloud':'local';
        _syncResolutions.set(entry.id+'|'+field.path,{signature:entry.signature,choice});
      }
      let rejected=false,consistent=false;
      try{
        const chosen=_hdMergeById([left],[right],'ops:purchaseOrders')[0];
        const paymentTotal=(chosen.payments||[]).reduce((s,p)=>s+Number(p.amount||0),0);
        consistent=chosen.paid===paymentTotal &&
          ((chosen.paid===150&&chosen.payments.some(p=>p.id==='left')&&!chosen.payments.some(p=>p.id==='right'))||
           (chosen.paid===170&&chosen.payments.some(p=>p.id==='right')&&!chosen.payments.some(p=>p.id==='left')));
      }catch(e){rejected=e.code==='SYNC_CONFLICT';}
      return {firstBlocked,consistent,rejected};
    }""", lambda r: (equal(r["firstBlocked"],True),equal(r["consistent"] or r["rejected"],True)))

    check("Documented purchase payment clears payable once and closed payment journal is preserved", """()=>{
      opsData.purchaseOrders=[{id:'paid-po',directPurchase:true,number:'PAID',projectId:'p',
        date:'2026-11-01',amount:100,vat:15,total:115,paid:115,status:'paid',
        payments:[{id:'pay1',amount:115,date:'2026-11-02',cashAccount:'1010'}]}];
      genInvJournals();_syncPurchasePaymentJournals();
      const firstCount=journals.filter(j=>j.source==='purchase-payment').length;
      const balance=_accBalances(),payable=balance['2010'].c-balance['2010'].d;
      _syncPurchasePaymentJournals();
      const secondCount=journals.filter(j=>j.source==='purchase-payment').length;
      const original=JSON.stringify(journals.find(j=>j.source==='purchase-payment').lines);
      opsData.periods=[{month:'2026-11',status:'closed'}];
      opsData.purchaseOrders[0].paid=100;opsData.purchaseOrders[0].payments[0].amount=100;
      _syncPurchasePaymentJournals();
      return {firstCount,secondCount,payable,
        closedPreserved:JSON.stringify(journals.find(j=>j.source==='purchase-payment').lines)===original,
        issues:_journalSyncIssues.length};
    }""", lambda r: (equal(r["firstCount"],1),equal(r["secondCount"],1),
                     equal(r["payable"],0),equal(r["closedPreserved"],True),
                     equal(r["issues"]>0,True)))

    check("Historical purchase settlement needs evidence before a payment journal is created", """()=>{
      opsData.purchaseOrders=[{id:'historical-po',directPurchase:true,number:'HIST',projectId:'p',
        date:'2026-11-01',amount:100,vat:15,total:115,paid:50,status:'partial',payments:[]}];
      genInvJournals();_syncPurchasePaymentJournals();
      const withoutEvidence=journals.filter(j=>j.source==='purchase-payment').length;
      const flagged=_journalSyncIssues.length>0;
      opsData.purchaseOrders[0].openingPayment={amount:50,date:'2026-11-02',cashAccount:'1010'};
      _syncPurchasePaymentJournals();
      const withEvidence=journals.filter(j=>j.source==='purchase-payment').length;
      const balance=_accBalances();
      return {withoutEvidence,flagged,withEvidence,payable:balance['2010'].c-balance['2010'].d};
    }""", lambda r: equal(r,{"withoutEvidence":0,"flagged":True,"withEvidence":1,"payable":65}))

    browser.close()

server.shutdown()
if failures:
    raise AssertionError("\n".join(failures))
print("PASS all review regressions")
