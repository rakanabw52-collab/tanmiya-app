"""Scan autosave and manual review share one record and survive failed writes."""
import http.server
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

SETUP = '''() => {
    document.getElementById('hdGate').style.setProperty('display', 'none', 'important');
    _cloudOn = false;
    window.HD_AUTHED = false;
    window.HD_ROLE = 'owner';
    projs = [{id:'scan-project', name:'مشروع اختبار القراءة', status:'active', contractValue:10000}];
    invs = []; journals = []; trash = [];
    window.opsData = {purchaseOrders:[], changeOrders:[], claims:[], periods:[]};
    editId = null;
    confirm2 = async () => true;
    renderDB = () => {};
    renderList = () => {};
    renderProjList = () => {};
    logEvent = () => {};
    bumpEdits = async () => {};
    fillProjSel();
    window.scanPayload = {
        invoiceNumber:'SCAN-TEST-01', date:'2026-11-01',
        vendorName:'مورد اختبار القراءة', vendorVAT:'300000000000003',
        subtotal:100, vatAmount:15, totalAmount:115, vatRate:15,
        type:'purchase', category:'مواد', notes:'قراءة مصطنعة للاختبار'
    };
    window.prepareScan = payload => {
        fillAI(payload);
        document.getElementById('f-proj').value = 'scan-project';
        document.getElementById('f-vat-recovery').value = 'no';
    };
    window.writeCalls = 0;
    svDetailed = async () => { writeCalls++; return {ok:true}; };
}'''

try:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path='/usr/bin/chromium', args=['--no-sandbox']
        )
        context = browser.new_context(service_workers='block')
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        # Only this test's local server may be reached, including script/font requests.
        page.route('**/*', lambda route: route.continue_()
                   if route.request.url.startswith(url) else route.abort())

        def reset():
            page.goto(url, wait_until='domcontentloaded')
            page.wait_for_function('typeof doAS === "function" && typeof saveInv === "function"')
            page.wait_for_timeout(250)
            page.evaluate(SETUP)

        # Reviewing the scan must update the exact automatically saved record.
        reset()
        result = page.evaluate('''async () => {
            prepareScan(scanPayload);
            await doAS(scanPayload);
            const originalId = invs[0]?.id, editAfterAuto = editId;
            const autoBeforeReview = invs[0]?.auto;
            document.getElementById('f-nt').value = 'راجع المستخدم المستند';
            document.getElementById('f-vat-recovery').value = 'no';
            await saveInv();
            return {count:invs.length, originalId, editAfterAuto,
                    autoBeforeReview, stored:invs[0], writeCalls};
        }''')
        assert result['count'] == 1, result
        assert result['editAfterAuto'] == result['originalId'], result
        assert result['stored']['id'] == result['originalId'], result
        assert result['autoBeforeReview'] is True, result
        assert result['stored']['auto'] is False, result
        assert result['stored'].get('reviewedAt', 0) > 0, result
        assert result['stored']['notes'] == 'راجع المستخدم المستند', result
        assert result['writeCalls'] == 2, result

        # A rejected scan write restores all previous records and the editing state.
        reset()
        result = page.evaluate('''async () => {
            invs = [{id:'existing', type:'expense', number:'KEEP', date:'2026-10-01',
                     vendor:'مورد قديم', subtotal:20, vat:0, vatRate:0, total:20}];
            const before = JSON.stringify(invs);
            prepareScan(scanPayload);
            svDetailed = async () => {writeCalls++; return {ok:false, err:'test write failure'};};
            await doAS(scanPayload);
            return {unchanged:before===JSON.stringify(invs), editId, writeCalls};
        }''')
        assert result == {'unchanged': True, 'editId': None, 'writeCalls': 1}, result

        # A failed manual review must not remove the auto flag or add reviewedAt.
        reset()
        result = page.evaluate('''async () => {
            prepareScan(scanPayload); await doAS(scanPayload);
            const before = JSON.stringify(invs);
            document.getElementById('f-vat-recovery').value = 'no';
            document.getElementById('f-nt').value = 'تعديل لم يُحفظ';
            svDetailed = async () => ({ok:false, err:'test manual failure'});
            await saveInv();
            return {unchanged:before===JSON.stringify(invs), count:invs.length};
        }''')
        assert result == {'unchanged': True, 'count': 1}, result

        # Conflicting totals are left for review; they never reach persistence.
        reset()
        result = page.evaluate('''async () => {
            const payload = {...scanPayload, totalAmount:999};
            prepareScan(payload); await doAS(payload);
            return {count:invs.length, writeCalls};
        }''')
        assert result == {'count': 0, 'writeCalls': 0}, result

        # Zero VAT is meaningful and must not become the default 15 percent.
        reset()
        result = page.evaluate('''async () => {
            const payload = {...scanPayload, vatRate:0, vatAmount:0, totalAmount:100};
            prepareScan(payload); await doAS(payload);
            return {count:invs.length, vatRate:invs[0]?.vatRate,
                    vat:invs[0]?.vat, total:invs[0]?.total};
        }''')
        assert result == {'count': 1, 'vatRate': 0, 'vat': 0, 'total': 100}, result

        # A different OCR type for the same supplier/number/date/amount is not new.
        reset()
        result = page.evaluate('''async () => {
            prepareScan(scanPayload); await doAS(scanPayload);
            const originalId = invs[0]?.id;
            editId = null;
            const secondRead = {...scanPayload, type:'expense'};
            prepareScan(secondRead); await doAS(secondRead);
            return {count:invs.length, originalId, storedId:invs[0]?.id,
                    editId, formNumber:document.getElementById('f-no').value, writeCalls};
        }''')
        assert result['count'] == 1 and result['writeCalls'] == 1, result
        assert result['storedId'] == result['editId'] == result['originalId'], result
        assert result['formNumber'] == 'SCAN-TEST-01', result

        # Autosave must obey the same edit/closed-project gate as manual entry.
        reset()
        result = page.evaluate('''async () => {
            prepareScan(scanPayload);
            _canEditInvoice = () => false;
            await doAS(scanPayload);
            return {count:invs.length, writeCalls};
        }''')
        assert result == {'count': 0, 'writeCalls': 0}, result

        # Hold the first actual write pending, then click manual save immediately.
        # A second write may begin only once the scan commit sets the record's ID.
        reset()
        result = page.evaluate('''async () => {
            prepareScan(scanPayload);
            let signalStarted, releaseFirst;
            const started = new Promise(resolve => { signalStarted = resolve; });
            svDetailed = async () => {
                writeCalls++;
                if (writeCalls === 1) {
                    signalStarted();
                    return new Promise(resolve => { releaseFirst = resolve; });
                }
                return {ok:true};
            };
            const scan = doAS(scanPayload);
            await Promise.race([started, new Promise((_, reject) =>
                setTimeout(() => reject(new Error('scan did not start its write')), 5000))]);
            const scanId = invs[0]?.id;
            const manual = saveInv();
            await new Promise(resolve => setTimeout(resolve, 30));
            const writesBeforeRelease = writeCalls;
            releaseFirst({ok:true});
            await Promise.all([scan, manual]);
            return {writesBeforeRelease, writeCalls, count:invs.length,
                    scanId, record:invs[0]};
        }''')
        assert result['writesBeforeRelease'] == 1, result
        assert result['writeCalls'] == 2 and result['count'] == 1, result
        assert result['record']['id'] == result['scanId'], result
        assert result['record']['auto'] is False, result
        assert result['record'].get('reviewedAt', 0) > 0, result
        assert not errors, errors
        browser.close()
finally:
    server.shutdown()

print('PASS scan/manual same ID, failed-write rollback, invalid totals blocked, zero VAT, '
      'cross-type scan identity, edit gate, and delayed-write manual-save race')
