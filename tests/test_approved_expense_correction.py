"""Approved expense corrections preserve history and cannot be undone piecemeal."""
import http.server
import os
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)


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
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.route('**/*', lambda route: route.continue_()
                   if route.request.url.startswith(url) else route.abort())
        page.goto(url, wait_until='domcontentloaded')
        page.wait_for_function('''typeof approvedExpenseCorrectionState === 'function'
            && typeof opsReverseJournal === 'function' && typeof delJE === 'function' ''')
        page.wait_for_timeout(250)

        page.evaluate('''() => {
            clearTimeout(_pushTimer); _pushTimer=null;
            _cloudOn=false; _cloudReplacing=false;
            window.HD_ROLE='owner'; window.HD_AUTHED=false;
            document.getElementById('hdGate').style.setProperty('display','none','important');
            hdIsPeriodClosed=()=>false;
            applyConfirmedUnitPrices=async()=>{};applyConfirmedProjectSettlements=async()=>{};
            cloudPushDebounced=()=>{};logEvent=()=>{};
            svJRN=()=>true;_svRetry=async()=>true;
            renderList=()=>{};renderLetters=()=>{};renderLogView=()=>{};
            renderOps=()=>{};accGo=()=>{};
            coa=_COA_DEFAULT.map(a=>({...a}));
            window.oldExpense={id:'old-approved-summary',type:'expense',number:'SUMMARY-OLD',
                date:'2026-05-26',vendor:'مورد اختبار مصطنع',vendorVAT:'',
                category:'materials',projectId:'p',subtotal:600,vat:0,total:600,vatRate:0};
            window.makeApprovedRows=count=>Array.from({length:count},(_,index)=>({
                id:'approved-'+(index+1),type:'expense',number:'APPROVED-'+(index+1),
                date:'2026-05-26',vendor:'مورد اختبار مصطنع',vendorVAT:'',category:'materials',
                projectId:'p',subtotal:50,vat:0,total:50,vatRate:0}));
            window.originalPosting={id:'j-old',source:'inv',sourceId:oldExpense.id,
                date:oldExpense.date,desc:'القيد التاريخي للمصروف المجمع',
                lines:_invPostings(oldExpense),t:100,u:'اختبار'};
            window.originalInvoiceJSON=JSON.stringify(oldExpense);
            window.originalPostingJSON=JSON.stringify(originalPosting);
            window.resetCorrection=(count=6,batch='anwar-approved-20261125',oldAmount=600)=>{
                window.correctionBatch=batch;window.approvedRows=makeApprovedRows(count);
                window.oldExpense={...oldExpense,subtotal:oldAmount,vat:0,total:oldAmount,vatRate:0};
                delete oldExpense.vatRecoverable;
                window.originalPosting={...originalPosting,lines:_invPostings(oldExpense)};
                window.originalInvoiceJSON=JSON.stringify(oldExpense);
                window.originalPostingJSON=JSON.stringify(originalPosting);
                projs=[{id:'p',name:'مشروع اختبار',status:'active',contractValue:1000,
                    startDate:'2026-05-01',quantity:1,unit:'م.ط',siteExpensesTotal:0}];
                window.opsData={purchaseOrders:[],claims:[],changeOrders:[],periods:[],suppliers:[]};
                invs=[_hdCopy(oldExpense),..._hdCopy(approvedRows)];
                journals=[_hdCopy(originalPosting),...approvedRows.map(i=>({
                    id:'j-'+i.id,source:'inv',sourceId:i.id,date:i.date,
                    desc:'قيد الفاتورة المعتمدة '+i.number,lines:_invPostings(i)}))];
                trash=[];_journalSyncIssues=[];
                window.messages=[];toast=(message,type)=>messages.push({message,type});
                window.dialogs={prompt:0,confirm:0};
                window.prompt=()=>{dialogs.prompt++;return '2026-11-25';};
                confirm2=async()=>{dialogs.confirm++;return true;};
            };
            window.applySyntheticCorrection=()=>{
                invs=invs.filter(i=>i.id!==oldExpense.id);
                trash=[{id:correctionBatch+':'+oldExpense.id,type:'inv',t:200,u:'اختبار',
                    data:_hdCopy(oldExpense),archiveBatchId:correctionBatch,
                    restorationRequiresAccountingReview:true,
                    sourceJournals:[_hdCopy(originalPosting)],
                    approvedReplacementCount:approvedRows.length,
                    replacementIds:approvedRows.map(i=>i.id)}];
                journals.push({id:'approved-reversal',source:'reversal',
                    correctionKind:'approvedExpenseBatch',archiveBatchId:correctionBatch,
                    sourceInvoiceId:oldExpense.id,reverses:originalPosting.id,
                    archiveEntryId:correctionBatch+':'+oldExpense.id,
                    date:'2026-11-25',desc:'عكس مصروف مجمع بعد اعتماد التفصيل',
                    lines:originalPosting.lines.map(l=>({acc:l.acc,debit:l.credit,credit:l.debit})),
                    t:200,u:'اختبار'});
            };
            window.resetTrialCorrection=()=>{
                resetCorrection(0,'trial-entry-discard-20261126',1000);
                window.oldExpense={...oldExpense,vat:150,total:1150,vatRate:15,vatRecoverable:true};
                window.originalPosting={...originalPosting,lines:_invPostings(oldExpense)};
                window.originalInvoiceJSON=JSON.stringify(oldExpense);
                window.originalPostingJSON=JSON.stringify(originalPosting);
                invs=[_hdCopy(oldExpense)];journals=[_hdCopy(originalPosting)];
            };
            window.applySyntheticTrialCorrection=()=>{
                applySyntheticCorrection();trash[0].ownerConfirmedTrial=true;
                const reversal=journals.find(j=>j.id==='approved-reversal');
                reversal.correctionKind='discardedTrialEntry';reversal.date='2026-11-26';
                reversal.desc='عكس قيد تجريبي بتأكيد المالك';
            };
            window.correctionMetrics=()=>{
                renderDB();const pl=projPL('p');
                return {projectCost:pl.costNet,projectProfit:pl.profit,
                    mainCost:Number(document.getElementById('s-cst').textContent.replaceAll(',','')),
                    mainProfit:Number(document.getElementById('s-pft').textContent.replaceAll(',',''))};
            };
            resetCorrection();
        }''')

        # Removing the approved aggregate changes operating totals once; the historical
        # original and its new exact inverse remain a balanced, immutable pair.
        baseline = page.evaluate('correctionMetrics()')
        assert baseline == {'projectCost': 900, 'projectProfit': 100,
                            'mainCost': 900, 'mainProfit': 100}, baseline
        result = page.evaluate('''() => {
            applySyntheticCorrection();const metrics=correctionMetrics();
            const state=approvedExpenseCorrectionState(journals.find(j=>j.id==='approved-reversal'));
            const changes=_syncInvJournals(),generated=genInvJournals();
            const pair=journals.filter(j=>['j-old','approved-reversal'].includes(j.id));
            const balances={};pair.forEach(j=>j.lines.forEach(l=>{
                balances[l.acc]=(balances[l.acc]||0)+l.debit-l.credit;
            }));
            return {metrics,state,changes,generated,issues:_journalSyncIssues.slice(),balances,
                journalCount:journals.length,invoiceCount:invs.length,
                sourceAbsent:!invs.some(i=>i.id===oldExpense.id),
                originalUnchanged:JSON.stringify(journals.find(j=>j.id==='j-old'))===originalPostingJSON,
                archivedInvoiceUnchanged:JSON.stringify(trash[0].data)===originalInvoiceJSON,
                archivedJournalUnchanged:JSON.stringify(trash[0].sourceJournals[0])===originalPostingJSON,
                financialExpenses:_fin().expenses};
        }''')
        assert result['metrics'] == {'projectCost': 300, 'projectProfit': 700,
                                      'mainCost': 300, 'mainProfit': 700}, result
        assert result['metrics']['mainProfit'] - baseline['mainProfit'] == 600, result
        assert baseline['mainCost'] - result['metrics']['mainCost'] == 600, result
        assert result['state']['tagged'] is True and result['state']['complete'] is True, result
        assert result['changes'] == 0 and result['generated'] == 0 and not result['issues'], result
        assert result['balances'] and all(value == 0 for value in result['balances'].values()), result
        assert result['journalCount'] == 8 and result['invoiceCount'] == 6, result
        assert result['sourceAbsent'] and result['originalUnchanged'], result
        assert result['archivedInvoiceUnchanged'] and result['archivedJournalUnchanged'], result
        assert result['financialExpenses'] == 300, result

        # Each batch declares its replacement count; neither one fixed count nor
        # one fixed project batch name determines whether a correction is valid.
        for replacement_count, batch in [
            (7, 'anwar-approved-20261125'),
            (16, 'otaim-approved-20261125'),
        ]:
            result = page.evaluate('''({count,batch}) => {
                resetCorrection(count,batch);applySyntheticCorrection();
                const before=JSON.stringify(journals),archive=JSON.stringify(trash);
                const state=approvedExpenseCorrectionState(journals.find(j=>j.id==='approved-reversal'));
                const changes=_syncInvJournals(),generated=genInvJournals();
                return {state,changes,generated,issues:_journalSyncIssues.slice(),
                    unchanged:JSON.stringify(journals)===before,
                    archiveUnchanged:JSON.stringify(trash)===archive,
                    originalUnchanged:JSON.stringify(journals.find(j=>j.id==='j-old'))===originalPostingJSON,
                    sourceAbsent:!invs.some(i=>i.id===oldExpense.id),
                    invoiceCount:invs.length,journalCount:journals.length,
                    financialExpenses:_fin().expenses};
            }''', {'count': replacement_count, 'batch': batch})
            assert result['state']['tagged'] is True and result['state']['complete'] is True, result
            assert result['changes'] == 0 and result['generated'] == 0 and not result['issues'], result
            assert result['unchanged'] and result['archiveUnchanged'] and result['originalUnchanged'], result
            assert result['sourceAbsent'] and result['invoiceCount'] == replacement_count, result
            assert result['journalCount'] == replacement_count + 2, result
            assert result['financialExpenses'] == replacement_count * 50, result

        # A missing or altered inverse is retained for accounting review, never
        # silently dropped or rewritten merely because the source was archived.
        for mutation in [
            "journals=journals.filter(j=>j.id!=='approved-reversal')",
            "journals.find(j=>j.id==='approved-reversal').lines[0].credit=599",
            "journals.find(j=>j.id==='approved-reversal').archiveEntryId='wrong-entry'",
            "trash[0].sourceJournals[0].lines[0].debit=599",
            "trash[0].replacementIds.pop()",
            "journals.push({..._hdCopy(journals.find(j=>j.id==='approved-reversal')),id:'second-approved-reversal'})",
            "journals.find(j=>j.id==='approved-reversal').date='2026-02-30'",
            "invs.push(_hdCopy(oldExpense))",
            "trash[0].sourceJournals={invalid:'not an array'}",
            "delete trash[0].approvedReplacementCount",
            "trash[0].approvedReplacementCount=0",
            "trash[0].approvedReplacementCount=-1",
            "trash[0].approvedReplacementCount=1001",
            "trash[0].approvedReplacementCount=NaN",
            "trash[0].approvedReplacementCount='6'",
            "trash[0].approvedReplacementCount=6.5",
            "trash[0].approvedReplacementCount=7",
            "trash[0].replacementIds[5]=trash[0].replacementIds[0]",
            "trash[0].replacementIds[5]='missing-approved-source'",
        ]:
            result = page.evaluate('''mutation => {
                resetCorrection();applySyntheticCorrection();(0,eval)(mutation);
                const before=JSON.stringify(journals),archived=JSON.stringify(trash);
                const reversal=journals.find(j=>j.id==='approved-reversal');
                const state=reversal?approvedExpenseCorrectionState(reversal):null;
                _syncInvJournals();const generated=genInvJournals();
                return {state,generated,unchanged:JSON.stringify(journals)===before,
                    archiveUnchanged:JSON.stringify(trash)===archived,
                    originalUnchanged:JSON.stringify(journals.find(j=>j.id==='j-old'))===originalPostingJSON,
                    issues:_journalSyncIssues.slice()};
            }''', mutation)
            assert result['unchanged'] and result['originalUnchanged'] and result['archiveUnchanged'], (mutation, result)
            assert result['issues'] and result['generated'] == 0, (mutation, result)
            if result['state'] is not None:
                assert result['state']['tagged'] is True and result['state']['complete'] is False, (mutation, result)
                assert result['state']['reason'], (mutation, result)

        # Both sides of this specific approved correction and the archived source
        # are guarded before confirmation dialogs, so callers cannot undo one leg.
        for action in ['delJE', 'opsReverseJournal']:
            for journal_id in ['j-old', 'approved-reversal']:
                result = page.evaluate('''async ({action,id}) => {
                    resetCorrection();applySyntheticCorrection();
                    const before=JSON.stringify({invs,journals,trash});
                    await window[action](id);await Promise.resolve();
                    return {unchanged:JSON.stringify({invs,journals,trash})===before,
                        dialogs,messages};
                }''', {'action': action, 'id': journal_id})
                assert result['unchanged'] and result['messages'], (action, journal_id, result)
                assert result['dialogs'] == {'prompt': 0, 'confirm': 0}, (action, journal_id, result)

        result = page.evaluate('''async () => {
            resetCorrection();applySyntheticCorrection();
            const before=JSON.stringify({invs,journals,trash});
            await restoreTrash(trash[0].id);
            return {unchanged:JSON.stringify({invs,journals,trash})===before,dialogs,messages};
        }''')
        assert result['unchanged'] and result['messages'], result
        assert result['dialogs'] == {'prompt': 0, 'confirm': 0}, result

        # An owner-confirmed trial expense can be discarded without pretending
        # that replacement invoices exist; its complete original/inverse pair stays.
        result = page.evaluate('''() => {
            resetTrialCorrection();const beforeMetrics=correctionMetrics();
            applySyntheticTrialCorrection();const before=JSON.stringify(journals);
            const archive=JSON.stringify(trash),metrics=correctionMetrics();
            const state=approvedExpenseCorrectionState(journals.find(j=>j.id==='approved-reversal'));
            const changes=_syncInvJournals(),generated=genInvJournals();
            const balances={};journals.forEach(j=>j.lines.forEach(l=>{
                balances[l.acc]=(balances[l.acc]||0)+l.debit-l.credit;
            }));
            return {beforeMetrics,metrics,state,changes,generated,balances,
                issues:_journalSyncIssues.slice(),unchanged:JSON.stringify(journals)===before,
                archiveUnchanged:JSON.stringify(trash)===archive,
                originalUnchanged:JSON.stringify(journals.find(j=>j.id==='j-old'))===originalPostingJSON,
                archivedInvoiceUnchanged:JSON.stringify(trash[0].data)===originalInvoiceJSON,
                archivedJournalUnchanged:JSON.stringify(trash[0].sourceJournals[0])===originalPostingJSON,
                replacementCount:trash[0].approvedReplacementCount,replacementIds:trash[0].replacementIds,
                sourceAbsent:!invs.some(i=>i.id===oldExpense.id),invoiceCount:invs.length,
                journalCount:journals.length,financialExpenses:_fin().expenses,
                archivedAmount:trash[0].data.total,archivedVAT:trash[0].data.vat,
                archivedEligibility:trash[0].data.vatRecoverable,
                originalLines:journals.find(j=>j.id==='j-old').lines,
                reversalLines:journals.find(j=>j.id==='approved-reversal').lines};
        }''')
        assert result['beforeMetrics'] == {'projectCost': 1000, 'projectProfit': 0,
                                           'mainCost': 1000, 'mainProfit': 0}, result
        assert result['metrics'] == {'projectCost': 0, 'projectProfit': 1000,
                                     'mainCost': 0, 'mainProfit': 1000}, result
        assert result['state']['tagged'] is True and result['state']['complete'] is True, result
        assert result['changes'] == 0 and result['generated'] == 0 and not result['issues'], result
        assert result['balances'] and all(value == 0 for value in result['balances'].values()), result
        assert result['unchanged'] and result['archiveUnchanged'] and result['originalUnchanged'], result
        assert result['archivedInvoiceUnchanged'] and result['archivedJournalUnchanged'], result
        assert result['replacementCount'] == 0 and result['replacementIds'] == [], result
        assert result['sourceAbsent'] and result['invoiceCount'] == 0 and result['journalCount'] == 2, result
        assert result['financialExpenses'] == 0, result
        assert result['archivedAmount'] == 1150 and result['archivedVAT'] == 150, result
        assert result['archivedEligibility'] is True and result['balances']['1030'] == 0, result
        assert len(result['originalLines']) == 3 and len(result['reversalLines']) == 3, result
        assert next(line for line in result['originalLines'] if line['acc'] == '1030')['debit'] == 150, result
        assert next(line for line in result['reversalLines'] if line['acc'] == '1030')['credit'] == 150, result

        # Zero replacements belong only to an explicit owner-confirmed trial.
        for mutation in [
            "journals.find(j=>j.id==='approved-reversal').correctionKind='approvedExpenseBatch'",
            "delete trash[0].ownerConfirmedTrial",
            "trash[0].ownerConfirmedTrial=false",
            "trash[0].approvedReplacementCount=1;trash[0].replacementIds=['approved-1'];"
            "invs=makeApprovedRows(1);journals.push({id:'j-approved-1',source:'inv',"
            "sourceId:'approved-1',date:invs[0].date,lines:_invPostings(invs[0])})",
        ]:
            result = page.evaluate('''mutation => {
                resetTrialCorrection();applySyntheticTrialCorrection();(0,eval)(mutation);
                const before=JSON.stringify({invs,journals,trash});
                const state=approvedExpenseCorrectionState(journals.find(j=>j.id==='approved-reversal'));
                _syncInvJournals();const generated=genInvJournals();
                return {state,generated,unchanged:JSON.stringify({invs,journals,trash})===before,
                    issues:_journalSyncIssues.slice()};
            }''', mutation)
            assert result['state']['tagged'] is True and result['state']['complete'] is False, (mutation, result)
            assert result['state']['reason'] and result['issues'], (mutation, result)
            assert result['unchanged'] and result['generated'] == 0, (mutation, result)

        for action in ['delJE', 'opsReverseJournal']:
            for journal_id in ['j-old', 'approved-reversal']:
                result = page.evaluate('''async ({action,id}) => {
                    resetTrialCorrection();applySyntheticTrialCorrection();
                    const before=JSON.stringify({invs,journals,trash});
                    await window[action](id);await Promise.resolve();
                    return {unchanged:JSON.stringify({invs,journals,trash})===before,dialogs,messages};
                }''', {'action': action, 'id': journal_id})
                assert result['unchanged'] and result['messages'], (action, journal_id, result)
                assert result['dialogs'] == {'prompt': 0, 'confirm': 0}, (action, journal_id, result)

        result = page.evaluate('''async () => {
            resetTrialCorrection();applySyntheticTrialCorrection();
            const before=JSON.stringify({invs,journals,trash});
            await restoreTrash(trash[0].id);
            return {unchanged:JSON.stringify({invs,journals,trash})===before,dialogs,messages};
        }''')
        assert result['unchanged'] and result['messages'], result
        assert result['dialogs'] == {'prompt': 0, 'confirm': 0}, result
        assert not errors, errors
        browser.close()
finally:
    server.shutdown()

print('PASS approved expense correction: original and archive unchanged, exact balanced reversal, '
      'one-time operating cost reduction, generic 6/7/16-row batches accepted, invalid replacement '
      'counts/references rejected, complete correction quiet, malformed/missing correction '
      'held for review, owner-confirmed trial disposal needs no replacements, and '
      'original/reversal deletion, re-reversal and archive restoration blocked')
