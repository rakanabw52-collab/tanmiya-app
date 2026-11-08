"""Regression tests for financial, persistence and synchronization fixes in v1121.

Synthetic fixtures only. HTTPS is blocked and no production data is modified.
Run: python3 tests/test_audit_regressions_1121.py
"""
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
try:
    with sync_playwright() as p:
        system_chromium = Path("/usr/bin/chromium")
        opts = {"headless": True, "args": ["--no-sandbox"]}
        if system_chromium.exists():
            opts["executable_path"] = str(system_chromium)
        browser = p.chromium.launch(**opts)
        context = browser.new_context(timezone_id="Asia/Riyadh")
        context.route("https://**", lambda route: route.abort())
        page = context.new_page()
        page.goto("http://127.0.0.1:" + str(server.server_port), wait_until="domcontentloaded")
        page.wait_for_function("typeof renderBuy1077 === 'function'")
        page.evaluate("document.getElementById('hdGate').style.setProperty('display','none','important')")

        result = page.evaluate("""async () => {
          const originalGet=_stGet,originalRetry=_svRetry,originalConfirm=confirm2;
          const originalSaveOps=svOps,originalRole=window.HD_ROLE,originalCloud=_cloudOn;
          const originalAuth=window.HD_AUTHED,originalSupa=_supa;
          const originalInvo=invs,originalProj=projs,originalOps=window.opsData;
          const originalMode=ST.mode;
          const report={};
          try {
            // Preserve an earlier archive record rather than parse its wrapper object.
            let archived=null;
            _stGet=async()=>({key:'history',value:JSON.stringify({version:1,snapshots:[{id:'older',signature:'first'}]})});
            _svRetry=async(_key,val)=>{archived=JSON.parse(val);return true;};
            _syncConflicts.clear();
            _syncConflicts.set('projects:_all:p',{id:'projects:_all:p',signature:'second',local:{id:'p',paidAmount:10},cloud:{id:'p',paidAmount:20}});
            report.archiveSaved=await _persistSyncConflicts();
            report.archiveIds=archived.snapshots.map(x=>x.id);
            let overwritten=false;
            _stGet=async()=>({key:'history',value:'invalid-json'});
            _svRetry=async()=>{overwritten=true;return true;};
            report.corruptedArchiveAccepted=await _persistSyncConflicts();
            report.corruptedArchiveOverwritten=overwritten;
            _syncConflicts.clear();
            _stGet=originalGet;_svRetry=originalRetry;

            // Memory-only storage is not a durable financial save.
            ST.mode='memory';
            report.memorySave=await _stSet('test-audit-memory','123');
            ST.mode=originalMode;

            projs=[{id:'p',name:'Test project',contractValue:500,paidAmount:0,goals:{}}];
            invs=[{id:'void',projectId:'p',type:'purchase',status:'cancelled',subtotal:100,vat:15,total:115}];
            window.opsData={purchaseOrders:[{id:'order',projectId:'p',invoiceId:'void',directPurchase:true,amount:100,vat:15,total:115,status:'open'}],claims:[],changeOrders:[],suppliers:[]};
            report.cancelledLinkCost=projPL('p').opsPur;
            report.cancelledLinkSource=_financialInvoices().filter(x=>x._source==='purchase').length;

            const taxNumber='311111111111113';
            report.taxEligibility={
              legacy:_vatEligPurchase({number:'T1',vendorVAT:taxNumber}),
              explicit:_vatEligPurchase({number:'T2',vendorVAT:taxNumber,taxDecl:true}),
              badNumber:_vatEligPurchase({number:'T3',vendorVAT:'1234567890',taxDecl:true}),
              missingInvoiceNumber:_vatEligPurchase({number:'',vendorVAT:taxNumber,taxDecl:true})
            };

            const revenue={type:'revenue',number:'R1',subtotal:100,vat:15,total:115};
            const purchase={type:'purchase',number:'P1',subtotal:50,vat:7.5,total:57.5,taxDecl:true,vendorVAT:taxNumber};
            const eligible=_monthlyInvoiceTotals([revenue,purchase]);
            const ineligible=_monthlyInvoiceTotals([revenue,{...purchase,taxDecl:false}]);
            report.monthly={eligible:{rev:eligible.rev,cost:eligible.cost,profit:eligible.profit,netVat:eligible.netVat},
              ineligible:{rev:ineligible.rev,cost:ineligible.cost,profit:ineligible.profit,inVat:ineligible.inVat}};

            _cloudBases.clear();
            _rememberBase('ops:zatca',[{id:'zatca',environment:'sandbox',certificateStatus:'none'}]);
            const reconciled=opsMergeData({zatca:{environment:'production',certificateStatus:'none'}},
              {zatca:{environment:'sandbox',certificateStatus:'ready'}});
            report.mergedZatca=reconciled.zatca;
            _cloudBases.clear();

            window.HD_ROLE='accountant';
            window.opsData.periods=[{id:'closed',month:'2026-11',status:'closed'}];
            window.opsData.periodEvents=[];
            await opsTogglePeriod('2026-11',false);
            report.accountantPeriodStatus=window.opsData.periods[0].status;
            report.accountantPeriodEvents=window.opsData.periodEvents.length;

            window.HD_ROLE='owner';
            window.opsData.periods=[{id:'open',month:'2026-11',status:'open'}];
            window.opsData.periodEvents=[];
            confirm2=async()=>true;
            svOps=async()=>({ok:false});
            await opsTogglePeriod('2026-11',true);
            report.failedPeriodSave={period:window.opsData.periods[0].status,events:window.opsData.periodEvents.length};

            window.opsData.suppliers=[{id:'s1',name:'Supplier 1'}];
            await delSup1077('s1');
            report.failedSupplierDelete=window.opsData.suppliers.length;

            const local=new Date();
            report.localDate=_today();
            report.expectedLocalDate=local.getFullYear()+'-'+String(local.getMonth()+1).padStart(2,'0')+'-'+String(local.getDate()).padStart(2,'0');
          } finally {
            _stGet=originalGet;_svRetry=originalRetry;confirm2=originalConfirm;
            svOps=originalSaveOps;ST.mode=originalMode;
            window.HD_ROLE=originalRole;_cloudOn=originalCloud;window.HD_AUTHED=originalAuth;_supa=originalSupa;
            invs=originalInvo;projs=originalProj;window.opsData=originalOps;
            _syncConflicts.clear();_syncResolutions.clear();_cloudBases.clear();
          }
          return report;
        }""")

        assert result["archiveSaved"] is True
        assert result["archiveIds"] == ["older", "projects:_all:p"]
        assert result["corruptedArchiveAccepted"] is False
        assert result["corruptedArchiveOverwritten"] is False
        assert result["memorySave"]["ok"] is False
        assert result["cancelledLinkCost"] == 115
        assert result["cancelledLinkSource"] == 1
        assert result["taxEligibility"] == {
            "legacy": False, "explicit": True, "badNumber": False, "missingInvoiceNumber": False
        }
        assert result["monthly"]["eligible"] == {"rev": 100, "cost": 50, "profit": 50, "netVat": 7.5}
        assert result["monthly"]["ineligible"] == {"rev": 100, "cost": 57.5, "profit": 42.5, "inVat": 0}
        assert result["mergedZatca"]["environment"] == "production"
        assert result["mergedZatca"]["certificateStatus"] == "ready"
        assert result["accountantPeriodStatus"] == "closed"
        assert result["accountantPeriodEvents"] == 0
        assert result["failedPeriodSave"] == {"period": "open", "events": 0}
        assert result["failedSupplierDelete"] == 1
        assert result["localDate"] == result["expectedLocalDate"]
        browser.close()
finally:
    server.shutdown()

print("PASS v1121: conflict archive, durable saves, cancelled invoices, conservative VAT, financial summary, ZATCA merge, periods, deletion, Saudi dates")
