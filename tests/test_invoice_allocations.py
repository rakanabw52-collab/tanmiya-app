"""One cost invoice can feed two projects without duplicating company costs or input VAT."""
import http.server
import json
import os
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
os.chdir(ROOT)
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Quiet)
threading.Thread(target=server.serve_forever,daemon=True).start()
url=f'http://127.0.0.1:{server.server_port}/'
try:
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
        context=browser.new_context(service_workers='block',viewport={'width':390,'height':844})
        page=context.new_page();errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.route('**/*',lambda route:route.continue_() if route.request.url.startswith(url) else route.abort())
        page.goto(url,wait_until='domcontentloaded')
        page.wait_for_function('typeof projPL==="function" && typeof saveInvoiceProjectAllocations==="function"')
        if not page.evaluate('typeof invoiceProjectRows==="function"'):
            page.add_script_tag(path=str(ROOT/'invoice-allocations.js'))
        page.wait_for_timeout(250)
        baseline=page.evaluate('''()=>{
            document.getElementById('hdGate').style.setProperty('display','none','important');
            HD_ROLE='owner';HD_AUTHED=false;_cloudOn=false;confirm2=async()=>true;
            applyConfirmedUnitPrices=async()=>{};applyConfirmedProjectSettlements=async()=>{};
            projs=[{id:'wahe',name:'مشروع الواحة 1609',status:'active',contractValue:165000},
                   {id:'anwar',name:'مشروع الأنوار 1607',status:'active',contractValue:170000}];
            invs=[{id:'shared-invoice',type:'purchase',number:'250214',date:'2026-11-01',
                vendor:'مورد اختبار مصطنع',vendorVAT:'300000000000003',category:'design',notes:'تصميم مشترك',
                projectId:'',subtotal:12000,vat:1800,total:13800,vatRate:15,vatRecoverable:true}];
            opsData={suppliers:[],purchaseOrders:[],claims:[],changeOrders:[],budgets:[],periods:[]};
            journals=[{id:'original-journal',source:'inv',sourceId:'shared-invoice',date:invs[0].date,
                desc:'قيد الفاتورة الأصلية',lines:_invPostings(invs[0])}];
            window.originalJournal=JSON.stringify(journals);
            window.fields=r=>({id:r.id,number:r.number,date:r.date,subtotal:r.subtotal,vat:r.vat,total:r.total,vatRecoverable:r.vatRecoverable});
            window.beforeFields=fields(invs[0]);
            window.metrics=()=>{renderDB();return {projects:projs.map(p=>{
                const f=projPL(p.id);return {id:p.id,cost:f.cost,costNet:f.costNet,recoverableVAT:f.recoverableVAT};}),
                mainCost:document.getElementById('s-cst').textContent,mainProfit:document.getElementById('s-pft').textContent,
                financialRows:_financialInvoices().length,inputVAT:vatTotals(2026,'m11').inVat};};
            return metrics();
        }''')
        assert baseline['projects']==[
            {'id':'wahe','cost':0,'costNet':0,'recoverableVAT':0},
            {'id':'anwar','cost':0,'costNet':0,'recoverableVAT':0}],baseline
        assert baseline['mainCost']=='12,000' and baseline['inputVAT']==1800,baseline

        # Half of the recorded net, VAT and gross amount goes to each project.
        page.evaluate("openInvoiceAllocationReview('shared-invoice')")
        page.locator('#allocation-project-0').select_option('wahe')
        page.locator('#allocation-project-1').select_option('anwar')
        preview=page.locator('#invoice-allocation-review').inner_text()
        assert '6,900.00' in preview and '900.00' in preview and '6,000.00' in preview,preview
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        assert page.evaluate("document.querySelector('#invoice-allocation-review>div').getBoundingClientRect().right<=innerWidth")
        page.evaluate("document.getElementById('save-invoice-allocation').onclick()")
        allocated=page.evaluate('''()=>({metrics:metrics(),rows:invoiceProjectRows('wahe'),
            original:fields(invs[0]),beforeFields,label:invoiceAllocationLabel(invs[0]),
            allocations:validInvoiceAllocations(invs[0]),journalUnchanged:JSON.stringify(journals)===originalJournal,
            recordCount:invs.length,masterProject:invs[0].projectId})''')
        assert allocated['metrics']['projects']==[
            {'id':'wahe','cost':6900,'costNet':6000,'recoverableVAT':900},
            {'id':'anwar','cost':6900,'costNet':6000,'recoverableVAT':900}],allocated
        assert allocated['metrics']['mainCost']==baseline['mainCost'],allocated
        assert allocated['metrics']['mainProfit']==baseline['mainProfit'],allocated
        assert allocated['metrics']['financialRows']==1 and allocated['metrics']['inputVAT']==1800,allocated
        assert allocated['rows'][0]['id']=='shared-invoice' and allocated['rows'][0]['total']==6900,allocated
        assert allocated['original']==allocated['beforeFields'],allocated
        assert allocated['recordCount']==1 and allocated['masterProject']=='',allocated
        assert allocated['journalUnchanged'],allocated
        assert 'الواحة' in allocated['label'] and 'الأنوار' in allocated['label'],allocated

        # Invalid or unknown allocations cannot create virtual financial entries.
        valid=page.evaluate('''()=>{
            const original=invs[0],copy=()=>JSON.parse(JSON.stringify(original));
            const unknown=copy();unknown.projectAllocations[0].projectId='missing';
            const duplicate=copy();duplicate.projectAllocations[1].projectId='wahe';
            const badSum=copy();badSum.projectAllocations[0].vat+=.01;
            const revenue=copy();revenue.type='revenue';
            const legacy=copy();delete legacy.vatRecoverable;
            return {bad:[unknown,duplicate,badSum,revenue].map(r=>validInvoiceAllocations(r).length),
                rowKeepsMissingEligibility:!Object.hasOwn(invoiceProjectRows('wahe',[legacy])[0],'vatRecoverable')};
        }''')
        assert valid=={'bad':[0,0,0,0],'rowKeepsMissingEligibility':True},valid
        page.evaluate("revInv('shared-invoice');renderInvoiceAllocationHint(invs[0],'f-proj')")
        assert 'الواحة' in page.locator('#f-proj-allocation-hint').inner_text()
        assert 'الأنوار' in page.locator('#f-proj-allocation-hint').inner_text()

        # Failed persistence keeps the previous distribution and all source values.
        page.evaluate('''()=>{
            window.beforeFailure=JSON.stringify(invs);
            window.savedDetailed=_svDetailed;let failed=false;
            _svDetailed=async(k,v)=>{if(k===SK&&!failed){failed=true;return {ok:false,err:'injected invoice failure'};}return savedDetailed(k,v);};
            openInvoiceAllocationReview('shared-invoice');
        }''')
        page.locator('#allocation-percent-0').fill('60')
        page.locator('#allocation-percent-1').fill('40')
        page.evaluate("document.getElementById('save-invoice-allocation').onclick()")
        assert page.evaluate('JSON.stringify(invs)===beforeFailure') is True
        assert page.locator('#invoice-allocation-review').is_visible()
        assert page.evaluate('JSON.stringify(journals)===originalJournal') is True
        page.evaluate('_svDetailed=savedDetailed')

        # Cancellation makes the single invoice general again, retaining raw input VAT.
        page.evaluate("document.getElementById('cancel-invoice-allocation').onclick()")
        cancelled=page.evaluate('''()=>({allocated:hasInvoiceProjectAllocations(invs[0]),metrics:metrics(),
            fields:fields(invs[0]),beforeFields,journalUnchanged:JSON.stringify(journals)===originalJournal})''')
        assert cancelled['allocated'] is False,cancelled
        assert cancelled['metrics']==baseline,cancelled
        assert cancelled['fields']==cancelled['beforeFields'] and cancelled['journalUnchanged'],cancelled
        assert not errors,errors
        browser.close()
finally:server.shutdown()
print('PASS one invoice allocated 50/50 with recorded VAT, original IDs/amounts/date/eligibility/journals '
      'preserved, project and company totals reconcile, invalid allocations rejected, save failure rollback, '
      'cancellation returns to general, mobile preview/hints')
