"""Duplicate archival preserves ledger history and rolls back incomplete local commits."""
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
        context = browser.new_context(service_workers='block')
        page = context.new_page()
        page.route('**/*', lambda route: route.continue_()
                   if route.request.url.startswith(url) else route.abort())
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(url, wait_until='domcontentloaded')
        page.wait_for_function('typeof removeDupGroup==="function" && typeof saveReviewArchive==="function"')
        page.wait_for_timeout(250)
        page.evaluate('window.realDetailed=_svDetailed;window.realGet=_stGet')

        def reset(extra=''):
            page.evaluate('''() => {
                clearTimeout(_pushTimer); _pushTimer=null;
                _cloudOn=false; _cloudReplacing=false; _dupRemoveBusy=false;
                window.HD_ROLE='owner'; window.HD_AUTHED=false;
                document.getElementById('hdGate').style.display='none';
                _svDetailed=realDetailed; _stGet=realGet;
                hdIsPeriodClosed=()=>false; confirm2=async()=>true;
                renderDB=()=>{};renderList=()=>{};logEvent=()=>{};
                window.messages=[];toast=(message,type)=>messages.push({message,type});
                projs=[];trash=[];window.opsData={purchaseOrders:[],claims:[],changeOrders:[],periods:[]};
                const base={number:'11903',date:'2026-11-01',vendor:'مورد اختبار',
                    vendorVAT:'300000000000003',subtotal:100,vat:15,total:115,vatRate:15};
                invs=[{...base,id:'keep',type:'expense',category:'other',vatRecoverable:false,
                       auto:false,reviewedAt:1},
                      {...base,id:'old',type:'purchase',category:'fuel',vatRecoverable:true,auto:true,vendor:'قراءة مورد أخرى',vendorVAT:'300000000000999'}];
                journals=[{id:'j-old',source:'inv',sourceId:'old',date:'2026-11-01',
                    desc:'قيد أصلي يجب حفظ حساباته',lines:[{acc:'5040',debit:100,credit:0},
                    {acc:'1030',debit:15,credit:0},{acc:'2010',debit:0,credit:115}]}];
                document.getElementById('dup-overlay')?.remove();
                // This suite isolates ledger preservation from the independently tested matching policy.
                findDupInvoices=()=>{const group=invs.filter(i=>['keep','old'].includes(i.id));return group.length>1?[group]:[];};
                window.selectKeeper=()=>{openDupCheck();
                    document.querySelector('input[name="dup-keep-0"][value="0"]').checked=true;};
            }''')
            if extra:
                page.evaluate(extra)
            page.evaluate('''() => {
                localStorage.setItem(SK,JSON.stringify(invs));
                localStorage.setItem(SJRN,JSON.stringify(journals));
                localStorage.setItem(STRA,JSON.stringify(trash));
                window.beforeInvoiceJSON=JSON.stringify(invs);
                window.beforeJournalJSON=JSON.stringify(journals);
                selectKeeper();
            }''')

        def archive():
            return page.evaluate('removeDupGroup(0)')

        def unchanged():
            return page.evaluate('''() => ({
                memory:JSON.stringify(invs)===beforeInvoiceJSON&&JSON.stringify(journals)===beforeJournalJSON,
                disk:localStorage.getItem(SK)===beforeInvoiceJSON&&localStorage.getItem(SJRN)===beforeJournalJSON,
                success:messages.some(m=>m.type==='ok')
            })''')

        # The only ledger entry follows the retained invoice without reclassifying its accounts.
        reset()
        assert archive() is True
        result = page.evaluate('''() => {
            const entry=trash.find(t=>t.data.id==='old');
            const lines=JSON.stringify(journals[0].lines),date=journals[0].date;
            _syncInvJournals();const generated=genInvJournals();
            return {invoiceIds:invs.map(i=>i.id),ledgerId:journals[0].id,sourceId:journals[0].sourceId,
                pending:journals[0].sourceLinkPendingReview,prior:journals[0].sourceLinkHistory.at(-1).sourceId,
                original:entry.sourceJournals[0],snapshot:entry.replacementSnapshot,
                unchangedLines:lines===JSON.stringify(journals[0].lines),unchangedDate:date===journals[0].date,
                generated,journalCount:journals.length,issues:_journalSyncIssues};
        }''')
        assert result['invoiceIds'] == ['keep'] and result['ledgerId'] == 'j-old', result
        assert result['sourceId'] == 'keep' and result['prior'] == 'old', result
        assert result['pending'] is True and result['unchangedLines'] and result['unchangedDate'], result
        assert result['original']['sourceId'] == 'old', result
        assert result['original']['lines'][0]['acc'] == '5040', result
        assert result['snapshot']['id'] == 'keep' and result['snapshot']['auto'] is False, result
        assert result['generated'] == 0 and result['journalCount'] == 1 and result['issues'], result

        # Equivalent duplicate postings can be archived when the retained invoice has its own entry.
        reset("journals.push({..._hdCopy(journals[0]),id:'j-keep',sourceId:'keep'})")
        assert archive() is True
        assert page.evaluate('journals.map(j=>j.id)') == ['j-keep']
        assert page.evaluate('journals[0].sourceLinkPendingReview') is True
        original_keeper_lines=page.evaluate('JSON.stringify(journals[0].lines)')
        page.evaluate('_syncInvJournals()')
        assert page.evaluate('JSON.stringify(journals[0].lines)') == original_keeper_lines
        assert page.evaluate("trash[0].sourceJournals[0].id") == 'j-old'

        # Different accounts on existing keeper/source postings remain intact, pending human review.
        reset("journals.push({..._hdCopy(journals[0]),id:'j-keep',sourceId:'keep',lines:[{acc:'6010',debit:115,credit:0},{acc:'2010',debit:0,credit:115}]})")
        assert archive() is True
        assert page.evaluate('journals.length') == 2
        assert page.evaluate("journals.find(j=>j.id==='j-old').sourceId") == 'old'
        assert page.evaluate("journals.find(j=>j.id==='j-old').sourceLinkPendingReview") is True

        # Different financial splits/date must not move or rewrite the original posting.
        for change in [
            "invs[0].subtotal=115;invs[0].vat=0;invs[0].vatRate=0",
            "journals[0].date='2026-10-31'",
        ]:
            reset(change)
            assert archive() is True
            result = page.evaluate('''() => {
                const before=JSON.parse(beforeJournalJSON)[0],after=journals[0];
                const sourceId=after.sourceId;_syncInvJournals();const generated=genInvJournals();
                return {sourceId,pending:after.sourceLinkPendingReview,target:after.replacementInvoiceId,
                    same:JSON.stringify(before.lines)===JSON.stringify(after.lines)&&before.date===after.date,
                    count:journals.length,generated};
            }''')
            assert result == {'sourceId':'old','pending':True,'target':'keep','same':True,'count':1,'generated':0}, result

        # Ambiguous, closed, and reversed entries are refused before changing either collection.
        for setup in [
            "journals.push({..._hdCopy(journals[0]),id:'j-old-2'})",
            "journals[0].date='2026-10-31';hdIsPeriodClosed=d=>d==='2026-10-31'",
            "journals.push({id:'reversal',source:'manual',reverses:'j-old',date:'2026-11-02',lines:[]})",
            "journals[0].reverses='earlier-entry'",
        ]:
            reset(setup)
            assert archive() is False
            assert unchanged() == {'memory':True,'disk':True,'success':False}

        # A failed journal or invoice write restores memory+disk; the recovery archive remains.
        for key_name in ['SJRN', 'SK']:
            reset()
            page.evaluate('''keyName => {
                const target=keyName==='SJRN'?SJRN:SK;let injected=false;
                _svDetailed=async(k,v)=>{
                    if(k===target&&!injected){injected=true;return {ok:false,err:'injected failure'};}
                    return realDetailed(k,v);
                };
            }''', key_name)
            assert archive() is False
            assert unchanged() == {'memory':True,'disk':True,'success':False}
            assert page.evaluate("trash.some(t=>t.sourceJournals?.[0]?.id==='j-old'&&t.replacementSnapshot?.id==='keep')")
            saved_trash = json.loads(page.evaluate('localStorage.getItem(STRA)'))
            assert saved_trash[0]['sourceJournals'][0]['sourceId'] == 'old'

        # Read-back failure counts as failed persistence even if a write itself succeeded.
        reset()
        page.evaluate('''() => {let injected=false;_stGet=async k=>{
            if(k===SJRN&&!injected){injected=true;return {key:k,value:'corrupt read-back'};}
            return realGet(k);
        };}''')
        assert archive() is False
        assert unchanged() == {'memory':True,'disk':True,'success':False}
        assert page.evaluate('trash.length') == 1
        assert not errors, errors
        browser.close()
finally:
    server.shutdown()

print('PASS duplicate archival: journal/account history preserved, pending links protected, '
      'closed/reversed/ambiguous cases refused, journal+invoice write/read-back failures rolled back')
