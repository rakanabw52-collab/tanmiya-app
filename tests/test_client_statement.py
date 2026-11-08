"""كشف العميل باستخدام بيانات صناعية، دون اتصال بالخدمة الفعلية."""
import http.server
import os
import threading
from pathlib import Path
from playwright.sync_api import sync_playwright

os.chdir(Path(__file__).resolve().parents[1])
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args): pass
server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Quiet)
threading.Thread(target=server.serve_forever, daemon=True).start()
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
    page = browser.new_page()
    page.route('https://**', lambda route: route.abort())
    page.goto(f'http://127.0.0.1:{server.server_port}', wait_until='domcontentloaded')
    page.wait_for_function('typeof clientStatement === "function" && document.querySelector(".client-statement-button")')
    page.evaluate('''()=>{
      document.getElementById('hdGate').style.setProperty('display','none','important');
      projs=[{id:'c1',name:'مشروع أول',client:' ماني ',contractValue:1000,paidAmount:100},
             {id:'c2',name:'مشروع ثان',client:'ماني',contractValue:2000,paidAmount:300},
             {id:'paid',name:'مسدد',client:'ماني',contractValue:100,paidAmount:115},
             {id:'other',name:'شركة أخرى',client:'غير ماني',contractValue:9000},
             {id:'zero',name:'بلا رصيد',client:'شركة مسددة',contractValue:0},
             {id:'unsafe',name:'<img src=x onerror="window.injected=1">',client:'شركة <اختبار>',contractValue:100}];
      invs=[{id:'r',projectId:'c1',type:'revenue',total:50},
            {id:'cancelled',projectId:'c1',type:'revenue',total:999,status:'cancelled'}];
      window.opsData={changeOrders:[{projectId:'c1',status:'approved',amount:100}],
        claims:[{projectId:'c1',partyType:'client',paid:25},
                {projectId:'c1',partyType:'client',paid:999,status:'cancelled'}]};
      goTab('db');
    }''')
    page.locator('#sec-db .client-statement-button').click()
    assert page.locator('#client-statement-select').input_value() == ''
    page.locator('#client-statement-select').select_option(label='ماني')
    assert page.locator('#client-statement tbody tr').count() == 2
    text = page.locator('#client-statement').inner_text()
    # 1265 - 100 - 50 - 25 = 1090; 2300 - 300 = 2000.
    assert '3,090' in text and '1,090' in text and '2,000' in text
    assert 'مشروع أول' in text and 'مشروع ثان' in text
    assert 'شركة أخرى' not in text and 'مسدد' not in text
    assert page.locator('#client-statement-select option').count() == 5
    with page.expect_popup() as popup:
        page.get_by_role('button', name='طباعة / حفظ PDF').click()
    printed = popup.value
    assert '3,090' in printed.locator('body').inner_text()
    assert printed.locator('tbody tr').count() == 2
    printed.close()
    page.locator('#client-statement-select').select_option(label='شركة مسددة')
    assert 'لا توجد مبالغ متبقية' in page.locator('#client-statement').inner_text()
    page.locator('#client-statement-select').select_option(label='شركة <اختبار>')
    assert page.locator('#client-statement img').count() == 0
    assert not page.evaluate('Boolean(window.injected)')
    page.locator('#client-statement-select').select_option(label='ماني')
    page.evaluate("projs[0].paidAmount+=90;clientStatement('ماني')")
    assert '3,000' in page.locator('#client-statement').inner_text()
    page.set_viewport_size({'width':390,'height':844})
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    page.evaluate('projs=[];clientStatement()')
    assert 'أضف اسم الشركة' in page.locator('#ops-modal-body').inner_text()
    browser.close()
server.shutdown()
print('PASS company selection, grouping, existing financial calculations, isolation, printing, empty states, escaping, refresh, mobile')
