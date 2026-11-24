"""Administrative classification preserves company totals, VAT and posted journal lines."""
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


server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Quiet)
threading.Thread(target=server.serve_forever, daemon=True).start()
url = f'http://127.0.0.1:{server.server_port}/'
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        context = browser.new_context(service_workers='block', viewport={'width': 390, 'height': 844})
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.route('**/*', lambda route: route.continue_()
                   if route.request.url.startswith(url) else route.abort())
        page.goto(url, wait_until='domcontentloaded')
        page.wait_for_function('typeof savePurchaseClassificationChange==="function" && typeof enforceFuelGeneral==="function"')
        page.wait_for_timeout(400)
        page.evaluate('''() => {
            window.actualReviewArchive=saveReviewArchive;
            window.resetClassificationFixture=(options={})=>{
                document.getElementById('hdGate').style.setProperty('display','none','important');
                _cloudOn=false;window.HD_AUTHED=false;window.HD_ROLE='owner';window.HD_USER='fixture-owner';
                applyConfirmedUnitPrices=async()=>{};applyConfirmedProjectSettlements=async()=>{};
                cloudPushDebounced=()=>{};logEvent=()=>{};hdIsPeriodClosed=()=>false;projectCloseAllows=()=>true;
                ST.mode='local';trash=[];_journalSyncIssues=[];
                projs=[{id:'p',name:'مشروع مصطنع أول',status:options.study?'study':'active',contractValue:1000,
                        siteExpensesTotal:options.manual?500:0},
                       {id:'q',name:'مشروع مصطنع ثان',status:'active',contractValue:2000}];
                coa=_COA_DEFAULT.map(a=>({...a}));
                invs=[{id:'inv-fuel',type:'purchase',projectId:'p',number:'CLASS-TEST-1',date:'2026-11-01',
                       vendor:'مورد مصطنع',vendorVAT:'300000000000003',subtotal:100,vat:15,vatRate:15,
                       total:115,paid:0,vatRecoverable:true,category:options.category||'fuel',
                       notes:options.notes||'تعبئة بنزين 91 — 20 لتر',createdAt:1}];
                window.opsData={suppliers:[],purchaseOrders:[],claims:[],changeOrders:[],budgets:[],periods:[]};
                if(options.linked)opsData.purchaseOrders=[{id:'po-linked',invoiceId:'inv-fuel',directPurchase:true,
                    number:'PO-CLASS-1',date:'2026-11-01',projectId:'p',category:'fuel',
                    notes:'تعبئة بنزين 91 — 20 لتر',amount:100,vat:15,vatRate:15,total:115,
                    paid:0,status:'open',vendorVAT:'300000000000003',vatRecoverable:true}];
                // The posted account deliberately differs from the suggested fuel account.
                journals=[{id:'j-original',source:'inv',sourceId:'inv-fuel',date:'2026-11-01',
                    desc:'قيد قديم مصطنع لا يُعاد تصنيفه إداريًا',
                    lines:[{acc:'5010',debit:100,credit:0},{acc:'1030',debit:15,credit:0},
                           {acc:'2010',debit:0,credit:115}]}];
                localStorage.setItem(SK,JSON.stringify(invs));localStorage.setItem(SOPS,JSON.stringify(opsData));
                window.failureMode='';window.failureUsed=false;window.writeCalls=[];
                saveReviewArchive=async(key,value)=>{
                    writeCalls.push(key);
                    if(failureMode==='archive'&&key.startsWith('hd-purchase-review:'))return false;
                    if(failureMode==='invoice'&&key===SK&&!failureUsed){failureUsed=true;return false;}
                    if(failureMode==='ops'&&key===SOPS&&!failureUsed){failureUsed=true;return false;}
                    const saved=await actualReviewArchive(key,value);
                    if(failureMode==='staleArchive'&&key.startsWith('hd-purchase-review:')&&!failureUsed){
                        failureUsed=true;invs=invs.map(i=>i.id==='inv-fuel'?{...i,notes:'تعديل وارد من جهاز آخر'}:i);
                        localStorage.setItem(SK,JSON.stringify(invs));
                    }
                    if(failureMode==='staleWrite'&&key===SK&&!failureUsed){
                        failureUsed=true;invs=invs.map(i=>i.id==='inv-fuel'?{...i,notes:'تعديل وارد أثناء كتابة المراجعة'}:i);
                        localStorage.setItem(SK,JSON.stringify(invs));
                    }
                    return saved;
                };
            };
            window.classificationMetrics=()=>{
                renderDB();const vat=vatTotals(2026,'m11');
                return {companyCost:document.getElementById('s-cst').textContent,
                        companyProfit:document.getElementById('s-pft').textContent,
                        vat:{base:vat.inBase,input:vat.inVat,count:vat.cs.length},
                        project:projs.map(p=>({id:p.id,cost:projPL(p.id).cost,costNet:projPL(p.id).costNet,
                                               profit:projPL(p.id).profit})),
                        journals:JSON.stringify(journals)};
            };
            window.classificationRequest=(changes={category:'fuel',projectId:''})=>({
                source:'inv',id:'inv-fuel',expectedSnapshot:JSON.stringify(invs[0]),changes,
                reason:'اختبار توزيع إداري مصطنع'});
            resetClassificationFixture();
        }''')

        before = page.evaluate('classificationMetrics()')
        result = page.evaluate('savePurchaseClassificationChange(classificationRequest())')
        assert result['ok'], result
        after = page.evaluate('classificationMetrics()')
        assert after['companyCost'] == before['companyCost'] == '100', (before, after)
        assert after['companyProfit'] == before['companyProfit'] == '2,900', (before, after)
        assert after['vat'] == before['vat'] == {'base': 100, 'input': 15, 'count': 1}, (before, after)
        assert before['project'][0]['profit'] == 900 and after['project'][0]['profit'] == 1000
        assert after['project'][0]['cost'] == after['project'][0]['costNet'] == 0
        assert after['journals'] == before['journals']
        record = page.evaluate('invs[0]')
        assert record['projectId'] == '' and record['previousProjectId'] == 'p'
        assert record['classificationAccount'] == '5010'
        assert record['classificationAccountSource']['journalId'] == 'j-original'
        assert {k: record[k] for k in ['subtotal','vat','vatRate','total','paid']} == {
            'subtotal':100,'vat':15,'vatRate':15,'total':115,'paid':0}
        page.evaluate('_syncInvJournals()')
        assert page.evaluate('JSON.stringify(journals)') == before['journals']
        archived = page.evaluate("Object.keys(localStorage).filter(k=>k.startsWith('hd-purchase-review:')).map(k=>JSON.parse(localStorage.getItem(k)))")
        assert any(b['records'][0]['data']['projectId'] == 'p' for b in archived)

        # Changing an administrative category keeps the historical posting account.
        page.evaluate("resetClassificationFixture({category:'infra',notes:'مواد خرسانة'})")
        before = page.evaluate('classificationMetrics()')
        result = page.evaluate("savePurchaseClassificationChange(classificationRequest({category:'services'}))")
        assert result['ok'], result
        assert page.evaluate('invs[0].classificationAccount') == '5010'
        assert page.evaluate('invs[0].category') == 'services'
        page.evaluate('_syncInvJournals()')
        assert page.evaluate('classificationMetrics()') == before

        # Historical aggregation and study exclusions cannot be migrated by clearing the link.
        for fixture in ({'manual': True}, {'study': True}):
            page.evaluate('options=>resetClassificationFixture(options)', fixture)
            original = page.evaluate('JSON.stringify([invs,opsData,journals])')
            result = page.evaluate('savePurchaseClassificationChange(classificationRequest())')
            assert not result['ok'], (fixture, result)
            assert page.evaluate('JSON.stringify([invs,opsData,journals])') == original
            assert page.evaluate('writeCalls.length') == 0
        page.evaluate('resetClassificationFixture({manual:true})')
        for changes in ({'projectId': None}, {'category': None}):
            result = page.evaluate('changes=>savePurchaseClassificationChange(classificationRequest(changes))', changes)
            assert not result['ok'], result
            assert page.evaluate('invs[0].projectId') == 'p'

        # A stale initial request never starts a write.
        page.evaluate('resetClassificationFixture()')
        result = page.evaluate("savePurchaseClassificationChange({...classificationRequest(),expectedSnapshot:'{}'})")
        assert not result['ok'] and page.evaluate('writeCalls.length') == 0, result

        # Failure to archive or persist restores both the visible data and local storage.
        for mode in ('archive', 'invoice'):
            page.evaluate('resetClassificationFixture()')
            page.evaluate('mode=>failureMode=mode', mode)
            original = page.evaluate('JSON.stringify([invs,opsData,journals])')
            original_disk = page.evaluate('localStorage.getItem(SK)')
            result = page.evaluate('savePurchaseClassificationChange(classificationRequest())')
            assert not result['ok'], (mode, result)
            assert page.evaluate('JSON.stringify([invs,opsData,journals])') == original
            assert page.evaluate('localStorage.getItem(SK)') == original_disk

        # Incoming edits during an awaited archive/write must survive the refused operation.
        for mode, note in (('staleArchive','تعديل وارد من جهاز آخر'),
                           ('staleWrite','تعديل وارد أثناء كتابة المراجعة')):
            page.evaluate('resetClassificationFixture()')
            page.evaluate('mode=>failureMode=mode', mode)
            result = page.evaluate('savePurchaseClassificationChange(classificationRequest())')
            assert not result['ok'], (mode, result)
            assert page.evaluate('invs[0].notes') == note
            assert page.evaluate('invs[0].projectId') == 'p'
            assert json.loads(page.evaluate('localStorage.getItem(SK)'))[0]['notes'] == note

        # Linked PO and invoice change scope together; the PO must not add a second cost.
        page.evaluate('resetClassificationFixture({linked:true})')
        before = page.evaluate('classificationMetrics()')
        result = page.evaluate('savePurchaseClassificationChange(classificationRequest())')
        assert result['ok'], result
        after = page.evaluate('classificationMetrics()')
        assert after['companyCost'] == before['companyCost'] == '100'
        assert after['vat'] == before['vat'] == {'base':100,'input':15,'count':1}
        assert after['journals'] == before['journals']
        assert page.evaluate('[invs[0].projectId,opsData.purchaseOrders[0].projectId]') == ['', '']
        assert page.evaluate('opsData.purchaseOrders.length') == 1
        assert json.loads(page.evaluate('localStorage.getItem(SOPS)'))['purchaseOrders'][0]['projectId'] == ''
        page.evaluate('_syncInvJournals()')
        assert page.evaluate('JSON.stringify(journals)') == before['journals']

        # A linked PO and invoice with separate active originals need accounting review.
        # Moving them must not silently let journal synchronization delete a source.
        page.evaluate("""() => {
            resetClassificationFixture({linked:true});
            journals.push({...JSON.parse(JSON.stringify(journals[0])),
                id:'j-purchase-extra',source:'purchase',sourceId:'po-linked'});
        }""")
        original = page.evaluate('JSON.stringify([invs,opsData,journals])')
        result = page.evaluate('savePurchaseClassificationChange(classificationRequest())')
        assert not result['ok'], result
        assert page.evaluate('JSON.stringify([invs,opsData,journals])') == original
        assert page.evaluate('writeCalls.length') == 0

        # If the second dataset write fails, the first dataset is rolled back too.
        page.evaluate('resetClassificationFixture({linked:true});failureMode="ops"')
        original = page.evaluate('JSON.stringify([invs,opsData,journals])')
        disk = page.evaluate('[localStorage.getItem(SK),localStorage.getItem(SOPS)]')
        result = page.evaluate('savePurchaseClassificationChange(classificationRequest())')
        assert not result['ok'], result
        assert page.evaluate('JSON.stringify([invs,opsData,journals])') == original
        assert page.evaluate('[localStorage.getItem(SK),localStorage.getItem(SOPS)]') == disk
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        assert not errors, errors
        browser.close()
finally:
    server.shutdown()

print('PASS classification save: company/VAT/journal invariance, project allocation, pinned account, protected historical sources, stale requests/edits, persistent archive, failed first/second writes and linked PO rollback.')
