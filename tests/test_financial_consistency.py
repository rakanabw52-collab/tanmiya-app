"""Independent regression examples for audited financial inconsistencies.

All records are synthetic. HTTPS requests are blocked and no production data is
read or written. Expected amounts are literal calculations from each fixture.
"""
import http.server
import json
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
results = {}

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
    page = browser.new_page()
    page.context.route("https://**", lambda route: route.abort())
    page.goto(f"http://127.0.0.1:{server.server_port}", wait_until="domcontentloaded")
    page.wait_for_function('typeof renderBuy1077 === "function"')
    page.evaluate("""()=>{
      window._testOriginalConfirm=confirm2;
      window._testReset=()=>{
        projs=[{id:'p',name:'مشروع اختبار',client:'شركة اختبار',contractValue:1000,paidAmount:0,status:'active',startDate:'2026-11-01',endDate:'2026-11-11',goals:{}}];
        invs=[];progress=[];journals=[];docs=[];lets=[];auditLog=[];
        window.opsData={suppliers:[{id:'s',name:'مورد اختبار',vat:'311111111111113'}],purchaseOrders:[],claims:[],changeOrders:[]};
        coa=_COA_DEFAULT.map(a=>({...a}));
        _cloudOn=false;window.HD_AUTHED=false;window.HD_ROLE='owner';window._opsProject='p';
        editId=null;curProjId=null;pendingFeasibility=null;qeId=null;
        confirm2=window._testOriginalConfirm;
        svDetailed=async()=>({ok:true});svPDetailed=async()=>({ok:true});
        svP=async()=>true;svPR=async()=>true;svJRN=()=>true;svOps=async()=>({ok:true});
        bumpEdits=async()=>{};cloudPushDebounced=()=>{};
        document.getElementById('hdGate').style.setProperty('display','none','important');
        opsCloseModal();resetBuyFilters();
      };
    }""")

    def check(name, script, assertion):
        try:
            page.evaluate("_testReset()")
            value = page.evaluate(script)
            results[name] = value
            assertion(value)
            print("PASS", name)
        except Exception as error:
            failures.append(f"{name}: {error}")
            print("FAIL", name, str(error)[:350])

    def equal(actual, expected):
        assert actual == expected, f"expected {expected!r}, got {actual!r}"

    def assert_positive(value):
        assert value > 0, f"expected positive value, got {value!r}"

    def assert_contains(text, needle):
        assert needle in text, f"expected {needle!r} in {text!r}"

    def assert_not_contains(text, needle):
        assert needle not in text, f"unexpected {needle!r} in {text!r}"

    check("Arabic decimal parsing", """()=>({
      decimal:toNum('١٢٣٫٤٥'),thousands:toNum('١٬٢٣٤٫٥٦'),
      english:toNum('1,234.56')
    })""", lambda r: equal(r, {"decimal":123.45,"thousands":1234.56,"english":1234.56}))

    check("Previous month boundaries", """()=>({
      jan:vatPrev(2026,'m1'),feb:vatPrev(2026,'m2'),q1:vatPrev(2026,'1')
    })""", lambda r: equal(r, {
        "jan":{"yr":2025,"sel":"m12"},"feb":{"yr":2026,"sel":"m1"},"q1":{"yr":2025,"sel":"4"}
    }))

    check("Collection uses tax-inclusive denominator", """()=>{
      projs[0].paidAmount=1150;renderDB();
      return {project:projPL('p').paidPct,dashboard:document.getElementById('r-pct').textContent};
    }""", lambda r: (equal(r["project"],100), equal(r["dashboard"],"100.0%")))

    check("Approved change order agrees across dashboards", """()=>{
      opsData.changeOrders=[{id:'vo',projectId:'p',amount:100,status:'approved'}];
      invs=[{id:'expense',projectId:'p',type:'expense',total:100,subtotal:100,vat:0,date:'2026-11-01',category:'other'}];
      renderDB();renderProjDash();
      return {contract:projPL('p').contract,projectProfit:projPL('p').profit,
        dashboardRevenue:document.getElementById('s-rev').textContent,
        dashboardProfit:document.getElementById('s-pft').textContent,
        projectDashboard:document.getElementById('proj-dash').textContent};
    }""", lambda r: (
        equal(r["contract"],1100),equal(r["projectProfit"],1000),
        equal(r["dashboardRevenue"],"1,100"),equal(r["dashboardProfit"],"1,000"),
        assert_contains(r["projectDashboard"],"1,100")
    ))

    check("Cost categories reconcile with manual override and operating costs", """()=>{
      projs[0].siteExpensesTotal=200;
      invs=[{id:'i',projectId:'p',type:'purchase',total:115,date:'2026-11-01',category:'materials'}];
      opsData.purchaseOrders=[{id:'po',projectId:'p',total:230,amount:200,vat:30,status:'open',category:'materials'}];
      opsData.claims=[{id:'sub',projectId:'p',partyType:'subcontractor',total:345,paid:0,status:'approved'}];
      const pl=projPL('p');return {cost:pl.cost,categories:Object.values(pl.byCat).reduce((a,b)=>a+b,0)};
    }""", lambda r: equal(r,{"cost":775,"categories":775}))

    check("Cross-year invoice remains in its financial year", """()=>{
      projs[0].startDate='2025-01-01';
      invs=[{id:'cross',projectId:'p',type:'expense',subtotal:100,vat:15,total:115,date:'2026-01-05',category:'other'}];
      return {oldYear:_finReal(2025).cost,newYear:_finReal(2026).cost};
    }""", lambda r: equal(r,{"oldYear":0,"newYear":115}))

    check("Annual costs include explicitly dated manual and operating sources", """()=>{
      projs[0].siteExpensesTotal=200;projs[0].siteExpensesDate='2026-11-01';
      invs=[{id:'replaced',projectId:'p',type:'purchase',subtotal:100,vat:15,total:115,date:'2026-11-01',category:'materials'}];
      opsData.purchaseOrders=[{id:'po',projectId:'p',amount:200,total:230,vat:30,date:'2026-11-02',status:'open'}];
      opsData.claims=[{id:'sub',projectId:'p',partyType:'subcontractor',total:345,paid:0,date:'2026-11-03',status:'approved'}];
      return {yearCost:_finReal(2026).cost,projectCost:projPL('p').cost};
    }""", lambda r: equal(r,{"yearCost":775,"projectCost":775}))

    check("Undated manual cost is flagged instead of assigned an invented year", """()=>{
      projs[0].siteExpensesTotal=200;delete projs[0].siteExpensesDate;
      const f=_finReal(2026);
      return {cost:f.cost,unallocated:f.unallocatedManual,preliminary:f.preliminary,notice:_finNotice(f)};
    }""", lambda r: (equal(r["cost"],0),equal(r["unallocated"],200),
                     equal(r["preliminary"],True),assert_contains(r["notice"],"غير مكتملة")))

    check("Cancelled purchases excluded from list and supplier statement", """()=>{
      opsData.purchaseOrders=[
        {id:'active',directPurchase:true,projectId:'p',supplierName:'مورد اختبار',date:'2026-11-01',amount:100,total:115,paid:0,vat:15,status:'open'},
        {id:'void',directPurchase:true,projectId:'p',supplierName:'مورد اختبار',date:'2026-11-01',amount:100,total:115,paid:0,vat:15,status:'cancelled'}];
      goTab('proc');renderBuy1077();supplierStatement('name:مورد اختبار');
      return {cost:projPL('p').cost,rows:document.querySelectorAll('#h1077-buy tbody tr').length,
        statementRows:document.querySelectorAll('#supplier-statement tbody tr').length,
        text:document.getElementById('supplier-statement').textContent};
    }""", lambda r: (equal(r["cost"],115),equal(r["rows"],1),equal(r["statementRows"],1),
                     assert_not_contains(r["text"],"230")))

    check("Exempt invoice is preserved by quick edit", """async()=>{
      invs=[{id:'zero',type:'expense',number:'ZERO',date:'2026-11-01',vendor:'مورد',subtotal:100,vat:0,vatRate:0,total:100,category:'other',projectId:'p'}];
      qEditInv('zero');await saveQe();
      return {subtotal:invs[0].subtotal,vat:invs[0].vat,vatRate:invs[0].vatRate,total:invs[0].total};
    }""", lambda r: equal(r,{"subtotal":100,"vat":0,"vatRate":0,"total":100}))

    check("Saving an exempt invoice retains zero rate and audit does not invent tax", """async()=>{
      setType('purchase');document.getElementById('f-no').value='EXEMPT';
      document.getElementById('f-dt').value='2026-11-01';document.getElementById('f-vnd').value='مورد';
      document.getElementById('f-sub').value='100';fExempt();await saveInv();
      return {vatRate:invs[0].vatRate,vat:invs[0].vat,total:invs[0].total,
        mathErrors:_qfDetect('all','').mathErrs.length};
    }""", lambda r: equal(r,{"vatRate":0,"vat":0,"total":100,"mathErrors":0}))

    check("Purchase overpayment and negative payment are rejected", """async()=>{
      opsOpen('purchase','','p');document.querySelector('.pi-desc').value='مواد';
      document.querySelector('.pi-amt').value='100';poItemsRecalc();
      document.getElementById('of-paid').value='200';await opsSaveForm();
      const excess=opsData.purchaseOrders.length;
      opsOpen('purchase','','p');document.querySelector('.pi-desc').value='مواد';
      document.querySelector('.pi-amt').value='100';poItemsRecalc();
      document.getElementById('of-paid').value='-1';await opsSaveForm();
      return {excess,negative:opsData.purchaseOrders.length};
    }""", lambda r: equal(r,{"excess":0,"negative":0}))

    check("Client claim summary excludes cancelled and subcontractor claims", """()=>{
      opsData.claims=[
        {id:'active',partyType:'client',projectId:'p',total:100,paid:0,status:'approved'},
        {id:'void',partyType:'client',projectId:'p',total:500,paid:0,status:'cancelled'},
        {id:'sub',partyType:'subcontractor',projectId:'p',total:200,paid:0,status:'approved'}];
      window._opsView='claims';renderOps();
      return {rows:document.querySelectorAll('#ops-body tbody tr').length,
        values:Array.from(document.querySelectorAll('#ops-body .ops-kpi .v')).map(e=>e.textContent)};
    }""", lambda r: (equal(r["rows"],1),equal(r["values"][:3],["100 ر.س","0 ر.س","100 ر.س"])))

    check("Legacy zero-tax invoice is not converted despite stale 15 percent metadata", """async()=>{
      invs=[{id:'legacy-zero',type:'expense',number:'LEGACY-ZERO',date:'2026-11-01',vendor:'مورد',
        subtotal:100,vat:0,vatRate:15,total:100,category:'other',projectId:'p'}];
      qEditInv('legacy-zero');await saveQe();
      return {subtotal:invs[0].subtotal,vat:invs[0].vat,vatRate:invs[0].vatRate,total:invs[0].total};
    }""", lambda r: equal(r,{"subtotal":100,"vat":0,"vatRate":0,"total":100}))

    check("Sub-riyal customer balance is retained", """()=>{
      projs[0].contractValue=100;projs[0].paidAmount=114.01;
      const pl=projPL('p');return {gross:pl.contractGross,paid:pl.paid,outstanding:pl.outstanding};
    }""", lambda r: equal(r,{"gross":115,"paid":114.01,"outstanding":0.99}))

    check("Receipt displays use the same tax-inclusive contract value", """()=>{
      projs[0].contractValue=50000;projs[0].paidAmount=50000;
      renderDB();showProj('p');
      const row=Array.from(document.querySelectorAll('#pd-body .vrow')).find(e=>
        e.querySelector('.lbl')?.textContent==='قيمة العقد شاملة الضريبة');
      return {dashboardValue:document.getElementById('r-total').textContent,
        detailValue:row?.querySelector('.val')?.textContent,
        dashboardPercentage:document.getElementById('r-pct').textContent};
    }""", lambda r: equal(r,{"dashboardValue":"57,500","detailValue":"57,500 ر.س","dashboardPercentage":"87.0%"}))

    check("Approved extension requires explicit opt-in and is not applied twice", """()=>{
      opsData.changeOrders=[{id:'extension',projectId:'p',status:'approved',days:5,amount:0}];
      projs[0].applyApprovedExtensions=false;
      const legacy=_projectPlan(projs[0]),legacyTime=projTimeStatus(projs[0]);
      projs[0].applyApprovedExtensions=true;
      const first=_projectPlan(projs[0]),second=_projectPlan(projs[0]),explicitTime=projTimeStatus(projs[0]);
      return {legacyDuration:legacy.dur,legacyPending:legacy.pendingExtension,legacyTimeDuration:legacyTime.dur,
        explicitDuration:first.dur,explicitEnd:first.end,secondEnd:second.end,
        explicitTimeDuration:explicitTime.dur,baseEnd:projs[0].endDate};
    }""", lambda r: equal(r,{"legacyDuration":10,"legacyPending":True,"legacyTimeDuration":10,
        "explicitDuration":15,"explicitEnd":"2026-11-16","secondEnd":"2026-11-16",
        "explicitTimeDuration":15,"baseEnd":"2026-11-11"}))

    check("Fully collected subtracts all recorded collection sources", """()=>{
      invs=[{id:'income',projectId:'p',type:'revenue',date:'2026-11-01',total:100}];
      opsData.claims=[{id:'claim',projectId:'p',partyType:'client',status:'paid',paid:200,total:200}];
      editId='p';document.getElementById('pe-cv').value='1000';cvVatMode='excl';
      markFullyCollected();projs[0].paidAmount=Number(document.getElementById('pe-pa').value);
      return {manual:projs[0].paidAmount,paid:projPL('p').paid,gross:projPL('p').contractGross};
    }""", lambda r: equal(r,{"manual":850,"paid":1150,"gross":1150}))

    check("Quick edit respects closed accounting period", """async()=>{
      opsData.periods=[{month:'2026-11',status:'closed'}];
      invs=[{id:'locked',type:'expense',number:'LOCK',date:'2026-11-01',vendor:'مورد',subtotal:100,vat:15,vatRate:15,total:115,category:'other',projectId:'p'}];
      qEditInv('locked');document.getElementById('qe-amt').value='230';setQeVat('incl');await saveQe();
      return {total:invs[0].total,subtotal:invs[0].subtotal};
    }""", lambda r: equal(r,{"total":115,"subtotal":100}))

    check("Posted journal follows edited and cancelled invoice", """async()=>{
      invs=[{id:'posted',type:'revenue',number:'POST',date:'2026-11-01',subtotal:100,vat:15,vatRate:15,total:115,projectId:'p'}];
      genInvJournals();const before=_fin().revenue;
      invs[0]={...invs[0],subtotal:200,vat:30,total:230};
      await _syncInvJournals();const edited=_fin().revenue;
      invs[0].status='cancelled';await _syncInvJournals();
      return {before,edited,cancelled:_fin().revenue};
    }""", lambda r: equal(r,{"before":100,"edited":200,"cancelled":0}))

    check("Feasibility only pools compatible units", """()=>{
      projs=[{id:'linear',name:'طولي',status:'done',quantity:100,unit:'م.ط'},
             {id:'area',name:'مساحة',status:'done',quantity:10,unit:'م²'}];
      invs=[{id:'l',projectId:'linear',type:'expense',total:1000,date:'2026-01-01'},
            {id:'a',projectId:'area',type:'expense',total:1000,date:'2026-01-01'}];
      document.getElementById('fs-ref').innerHTML='<option value="avg">avg</option>';
      document.getElementById('fs-qty').value='50';document.getElementById('fs-unit').value='م.ط';
      document.getElementById('fs-cv').value='2000';document.getElementById('fs-name').value='طولي جديد';
      calcFeasibility();return {estimate:pendingFeasibility.estTotal,unit:pendingFeasibility.unit};
    }""", lambda r: equal(r,{"estimate":500,"unit":"م.ط"}))

    check("Unit cost references remain separate by measurement unit", """()=>{
      projs=[{id:'linear',name:'طولي',status:'done',quantity:100,unit:'م.ط'},
             {id:'area',name:'مساحة',status:'done',quantity:10,unit:'م²'}];
      invs=[{id:'l',projectId:'linear',type:'expense',total:1000,date:'2026-01-01'},
            {id:'a',projectId:'area',type:'expense',total:1000,date:'2026-01-01'}];
      renderUnitCost();return document.getElementById('db-unitcost').textContent;
    }""", lambda r: (assert_contains(r,"10 ر.س/م.ط"),assert_contains(r,"100 ر.س/م²"),
                     assert_not_contains(r,"18 ر.س/"),assert_not_contains(r,"110 ر.س/")))

    check("Journal correction preserves closed periods and reports the issue", """async()=>{
      invs=[{id:'posted',type:'revenue',number:'POST',date:'2026-11-01',subtotal:100,vat:15,vatRate:15,total:115,projectId:'p'}];
      genInvJournals();opsData.periods=[{month:'2026-11',status:'closed'}];
      invs[0]={...invs[0],subtotal:200,vat:30,total:230};
      await _syncInvJournals();
      return {revenue:_fin().revenue,issues:_journalSyncIssues.length};
    }""", lambda r: (equal(r["revenue"],100),assert_positive(r["issues"])))

    check("Negative progress rejected; Arabic quantity correctly saved", """async()=>{
      const wt=WORKTYPES.find(w=>w.unit);projs[0].goals={[wt.id]:10};
      openProgForm('p');document.getElementById('prog-wt').value=wt.id;
      document.getElementById('prog-date').value='2026-11-01';document.getElementById('prog-qty').value='-3';
      await saveProg();const negativeCount=progress.length;
      openProgForm('p');document.getElementById('prog-wt').value=wt.id;
      document.getElementById('prog-date').value='2026-11-01';document.getElementById('prog-qty').value='٣';
      await saveProg();return {negativeCount,qty:progress[0]?.qty,percentage:projProgress('p').overall};
    }""", lambda r: equal(r,{"negativeCount":0,"qty":3,"percentage":30}))

    check("Completion before project start is rejected", """async()=>{
      confirm2=async()=>{
        let input=document.getElementById('cpd-date');
        if(!input){input=document.createElement('input');input.id='cpd-date';document.body.appendChild(input);}
        input.value='2026-10-01';return true;
      };
      await closeProjDone('p');
      return {status:projs[0].status,actual:projs[0].actualEndDate||null};
    }""", lambda r: equal(r,{"status":"active","actual":None}))

    check("Direct purchase tax is visible in eligible input tax", """()=>{
      opsData.purchaseOrders=[{id:'taxpo',directPurchase:true,projectId:'p',supplierId:'s',
        number:'TAXPO',vendorVAT:'300000000000003',date:'2026-11-01',amount:100,total:115,paid:0,vat:15,vatRate:15,status:'open',taxDecl:true}];
      return {input:vatTotals(2026,'m11').inVat,cost:projPL('p').cost};
    }""", lambda r: equal(r,{"input":15,"cost":115}))

    check("Cancelled invoices do not reappear in project export details", """()=>{
      invs=[{id:'active',projectId:'p',type:'expense',number:'KEEP',date:'2026-11-01',total:100,category:'other'},
        {id:'void',projectId:'p',type:'expense',number:'VOID',date:'2026-11-02',total:500,status:'cancelled',category:'other'}];
      curProjId='p';const sheets=[];
      const oldXLSX=window.XLSX;
      window.XLSX={utils:{book_new:()=>({}),aoa_to_sheet:rows=>({rows}),
        book_append_sheet:(wb,ws,name)=>sheets.push({name,rows:ws.rows})},writeFile:()=>{}};
      expProjPDF();window.XLSX=oldXLSX;
      return sheets[0].rows.flat().map(x=>String(x)).join('|');
    }""", lambda r: (assert_contains(r,"KEEP"),assert_not_contains(r,"VOID")))

    browser.close()

server.shutdown()
if failures:
    raise AssertionError("\n".join(failures))
print("PASS all independent financial consistency scenarios")
