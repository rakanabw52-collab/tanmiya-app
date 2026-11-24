"""Explicit general purchases remain in company costs/VAT without changing project P&L."""
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
        context = browser.new_context(service_workers='block', viewport={'width':390, 'height':844})
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.route('**/*', lambda route: route.continue_()
                   if route.request.url.startswith(url) else route.abort())
        page.goto(url, wait_until='domcontentloaded')
        page.wait_for_function('typeof renderBuy1077==="function" && typeof vatTotals==="function"')
        page.wait_for_timeout(300)
        page.evaluate('''() => {
            document.getElementById('hdGate').style.setProperty('display','none','important');
            _cloudOn=false;window.HD_AUTHED=false;window.HD_ROLE='owner';
            applyConfirmedUnitPrices=async()=>{};applyConfirmedProjectSettlements=async()=>{};
            projs=[{id:'p1',name:'مشروع أول مصطنع',status:'active',contractValue:1000},
                   {id:'p2',name:'مشروع ثان مصطنع',status:'active',contractValue:2000}];
            invs=[{id:'project-invoice',type:'purchase',projectId:'p1',number:'PROJECT-TEST-1',
                date:'2026-11-01',vendor:'مورد مشروع',vendorVAT:'300000000000003',
                subtotal:100,vat:15,total:115,vatRate:15,vatRecoverable:true}];
            journals=[];trash=[];
            window.opsData={suppliers:[{id:'supplier',name:'مورد عام',vat:'300000000000011'}],
                purchaseOrders:[],changeOrders:[],claims:[],budgets:[],periods:[]};
            hdIsPeriodClosed=()=>false;
            window.projectSnapshot=()=>projs.map(p=>{
                const f=projPL(p.id);return {id:p.id,cost:f.cost,costNet:f.costNet,profit:f.profit};
            });
            window.beforeProjects=projectSnapshot();
            window.prepareGeneralPurchase=number=>{
                opsOpen('purchase','','');
                const set=(id,value)=>document.getElementById(id).value=value;
                set('of-date','2026-11-01');set('of-supplier','supplier');
                set('of-no',number);set('of-vendorvat','300000000000011');
                set('of-vrate','15');set('of-vat-recovery','yes');
                set('of-paid','0');set('of-pay','آجل');
                document.querySelector('.pi-desc').value='شراء عام مصطنع';
                document.querySelector('.pi-amt').value='200';poItemsRecalc();
            };
            prepareGeneralPurchase('GENERAL-TEST-1');
        }''')

        # A new blank form never silently means "general": the user must select it.
        assert page.locator('#of-proj').input_value() == '__select__'
        assert 'مشتريات عامة / بدون مشروع' in page.locator('#of-proj').inner_text()
        assert 'لا تؤثر في ربح أي مشروع' in page.locator('#ops-modal-body').inner_text()
        page.evaluate('opsSaveForm()')
        assert page.evaluate('opsData.purchaseOrders.length') == 0
        page.locator('#of-proj').select_option('')

        # Date and tax-document validation still apply to general purchases.
        page.locator('#of-date').fill('')
        page.evaluate('opsSaveForm()')
        assert page.evaluate('opsData.purchaseOrders.length') == 0
        page.locator('#of-date').fill('2026-11-01')
        page.locator('#of-vendorvat').fill('invalid')
        page.evaluate('opsSaveForm()')
        assert page.evaluate('opsData.purchaseOrders.length') == 0
        page.locator('#of-vendorvat').fill('300000000000011')
        page.locator('#of-no').fill('')
        page.evaluate('opsSaveForm()')
        assert page.evaluate('opsData.purchaseOrders.length') == 0
        page.locator('#of-no').fill('GENERAL-TEST-1')
        page.evaluate('opsSaveForm()')

        result = page.evaluate('''() => {
            renderDB();const vat=vatTotals(2026,'m11');
            const general=opsData.purchaseOrders[0];
            const source=_financialInvoices().find(i=>i._source==='purchase'&&i._sourceId===general?.id);
            return {count:opsData.purchaseOrders.length,general,projects:projectSnapshot(),beforeProjects,
                source:{projectId:source?.projectId,eligible:source&&_vatEligPurchase(source),vat:source?.vat},
                vat:{base:vat.inBase,input:vat.inVat,count:vat.cs.length},
                main:{cost:document.getElementById('s-cst').textContent,profit:document.getElementById('s-pft').textContent}};
        }''')
        assert result['count'] == 1 and result['general']['projectId'] == '', result
        assert result['general']['vatRecoverable'] is True, result
        assert [result['general'][k] for k in ['amount','vat','total']] == [200,30,230], result
        assert result['projects'] == result['beforeProjects'] == [
            {'id':'p1','cost':115,'costNet':100,'profit':900},
            {'id':'p2','cost':0,'costNet':0,'profit':2000}], result
        assert result['source'] == {'projectId':'','eligible':True,'vat':30}, result
        assert result['vat'] == {'base':300,'input':45,'count':2}, result
        assert result['main'] == {'cost':'300','profit':'2,700'}, result
        assert 'GENERAL-TEST-1' in page.locator('#h1077-buy').inner_text()
        saved = json.loads(page.evaluate('localStorage.getItem(SOPS)'))
        assert saved['purchaseOrders'][0]['projectId'] == ''

        # A manually selected Arabic fuel category routes an actual save to general.
        page.evaluate('''() => {
            prepareGeneralPurchase('FUEL-GENERAL-TEST');
            document.getElementById('of-proj').value='p1';
            document.getElementById('of-cat').value='محروقات';
            document.querySelector('.pi-desc').value='بنزين 91 — 20 لتر';
        }''')
        page.evaluate('opsSaveForm()')
        fuel = page.evaluate("opsData.purchaseOrders.find(o=>o.number==='FUEL-GENERAL-TEST')")
        assert fuel['projectId'] == '' and fuel['previousProjectId'] == 'p1', fuel
        assert fuel['category'] == 'محروقات' and fuel['vatRecoverable'] is True, fuel
        assert page.evaluate('projectSnapshot()') == result['beforeProjects']

        # Existing general records reopen as general; missing project links stay visible and invalid.
        page.evaluate("opsOpen('purchase',opsData.purchaseOrders[0].id)")
        assert page.locator('#of-proj').input_value() == ''
        page.evaluate('''() => {
            opsData.purchaseOrders.push({...opsData.purchaseOrders[0],id:'missing-link',projectId:'missing-project'});
            opsOpen('purchase','missing-link');
            window.beforeMissing=JSON.stringify(opsData.purchaseOrders);
        }''')
        assert page.locator('#of-proj').input_value() == 'missing-project'
        assert 'مشروع غير موجود' in page.locator('#of-proj option:checked').inner_text()
        page.evaluate('opsSaveForm()')
        assert page.evaluate('JSON.stringify(opsData.purchaseOrders)===beforeMissing') is True
        page.evaluate("opsData.purchaseOrders=opsData.purchaseOrders.filter(o=>o.id!=='missing-link')")

        # An unsuccessful write leaves the previously saved purchase and disk state intact.
        page.evaluate('''() => {
            window.beforeFailure=JSON.stringify(opsData.purchaseOrders);
            prepareGeneralPurchase('GENERAL-FAIL-TEST');
            document.getElementById('of-proj').value='';
            svOps=async()=>({ok:false,err:'injected local save failure'});
        }''')
        page.evaluate('opsSaveForm()')
        assert page.evaluate('JSON.stringify(opsData.purchaseOrders)===beforeFailure') is True
        assert len(json.loads(page.evaluate('localStorage.getItem(SOPS)'))['purchaseOrders']) == 2
        assert page.evaluate('projectSnapshot()') == result['beforeProjects']
        assert not errors, errors
        browser.close()
finally:
    server.shutdown()

print('PASS explicit general-purchase choice, required date/VAT documentation, saved general purchase '
      'in company costs and input VAT, actual fuel save routed to general, unchanged project profits, '
      'missing-link protection, save-failure rollback')
