"""Contract input basis and review, synthetic amounts only; no production mutations."""
import http.server,threading,os
from pathlib import Path
from playwright.sync_api import sync_playwright
os.chdir(Path(__file__).resolve().parents[1])
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Quiet)
threading.Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=b.new_page();page.route('https://**',lambda r:r.abort());page.goto(f'http://127.0.0.1:{server.server_port}');page.wait_for_function('typeof reviewContractTaxes==="function"')
 results=page.evaluate('''()=>{
  projs=[{id:'q',name:'عقد اختبار بطول 4398',status:'done',contractValue:219900,quantity:4398,unit:'م.ط',paidAmount:219900},{id:'a',name:'عقد اختبار ثان',status:'active',contractValue:50000,quantity:1000,unit:'م.ط'},{id:'study',name:'دراسة',status:'study',contractValue:1000000}];invs=[];window.opsData={claims:[],changeOrders:[],purchaseOrders:[]};
  const pl=projPL('q');const before=JSON.stringify(projs);reviewContractTaxes();
  const audit=document.getElementById('ops-modal-body').textContent;
  const unchanged=before===JSON.stringify(projs);
  setCvVat('incl');applyExtractedContractAmount({contractValueWithoutVAT:219900});
  const net=cvNetFromInput(),netMode=cvVatMode;
  applyExtractedContractAmount({contractValueIncludingVAT:252885});const grossNet=cvNetFromInput();
  const raw=document.getElementById('pe-cv').value;
  const unknown=applyExtractedContractAmount({contractValue:219900});
  const noGuess=document.getElementById('pe-cv').value===raw&&unknown.includes('لم تُعبّأ');
  const conflict=applyExtractedContractAmount({contractValueWithoutVAT:219900,contractValueIncludingVAT:219900});
  return {net,netMode,grossNet,noGuess,conflict:conflict.includes('غير متطابقين'),unchanged,gross:pl.contractGross,vat:pl.contractGross-pl.contract,price:pl.contract/4398,remaining:pl.outstanding,totalIncludesOnlyOperational:audit.includes('310,385')&&!audit.includes('1,460,385')};
 }''')
 assert results=={'net':219900,'netMode':'excl','grossNet':219900,'noGuess':True,'conflict':True,'unchanged':True,'gross':252885,'vat':32985,'price':50,'remaining':32985,'totalIncludesOnlyOperational':True},results
 print('PASS 50 riyal net unit price; tax added once; gross input converted once; ambiguous/conflicting extraction rejected; audit read-only and study excluded from totals')
 b.close()
server.shutdown()
