/* هدف التنمية — 1077
   واجهة مبسطة حسب أسلوب العمل الفعلي: شراء مباشر بدون مقاول باطن أو أوامر شراء. */
(function(){
'use strict';
if(window.__TANMIYA_1077__) return;
window.__TANMIYA_1077__=true;

const D=()=>window.opsData||(window.opsData={});
const arr=k=>Array.isArray(D()[k])?D()[k]:(D()[k]=[]);
const num=v=>{const n=Number(v||0);return Number.isFinite(n)?n:0;};
const money=v=>(typeof fmtI==='function'?fmtI(num(v)):Math.round(num(v)).toLocaleString('ar-SA'))+' ر.س';
const today=()=>new Date().toISOString().slice(0,10);
const bal=x=>Math.max(0,num(x.total||x.amount)-num(x.paid));
const projectName=id=>{const p=(window.projs||[]).find(x=>x.id===id);return p?p.name:'—';};
const supplierName=id=>{const s=arr('suppliers').find(x=>x.id===id);return s?s.name:'—';};
const esc2=s=>typeof esc==='function'?esc(s):String(s||'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

const baseRenderOps=window.renderOps;
const baseOpsOpen=window.opsOpen;
const baseOpsSave=window.opsSaveForm;
const baseOpenSet=window.openSet;
const baseGoTab=window.goTab;

function style(){
  if(document.getElementById('tanmiya-1077-style')) return;
  const s=document.createElement('style');s.id='tanmiya-1077-style';s.textContent=`
    #sec-ops{display:none!important}.tab[data-tab="ops"],.tab[data-tab="add"],.tab[data-tab="fs"],.tab[data-tab="vt"],.tab[data-tab="let"]{display:none!important}
    .ops1077-card{background:#fff;border:1px solid #dbe8f3;border-radius:14px;padding:14px;margin:12px 0;box-shadow:0 3px 12px rgba(23,73,111,.055)}
    .ops1077-head{display:flex;align-items:flex-start;justify-content:space-between;gap:10px;margin-bottom:10px}.ops1077-head h3{font-family:'Cairo',sans-serif;font-size:14px;color:#17496f;margin:0}.ops1077-head p{font-size:11.5px;color:#64748b;margin:3px 0 0;line-height:1.6}
    .ops1077-nav{display:flex;gap:7px;overflow-x:auto;padding:2px 0 10px}.ops1077-nav button{white-space:nowrap;border:1px solid #cfdeeb;background:#fff;color:#31516f;border-radius:999px;padding:8px 11px;font-family:'Tajawal',sans-serif;font-weight:800;font-size:11.5px;cursor:pointer}.ops1077-nav button.on{background:#2771ab;color:#fff;border-color:#2771ab}
    .ops1077-kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:10px 0}.ops1077-kpi{background:#f8fbfe;border:1px solid #e3edf5;border-radius:11px;padding:10px}.ops1077-kpi span{display:block;font-size:10.5px;color:#64748b}.ops1077-kpi b{display:block;font-family:'Cairo',sans-serif;font-size:15px;color:#153f63;margin-top:2px}
    .ops1077-actions{display:flex;gap:8px;flex-wrap:wrap;margin:9px 0}.ops1077-btn{border:0;border-radius:9px;padding:9px 12px;background:#2771ab;color:#fff;font-family:'Tajawal',sans-serif;font-weight:800;cursor:pointer}.ops1077-btn.alt{background:#edf5fb;color:#1d5e8e}.ops1077-btn.red{background:#b91c1c}
    .ops1077-tablewrap{overflow:auto;border:1px solid #e2e8f0;border-radius:11px}.ops1077-table{width:100%;border-collapse:collapse;min-width:720px;background:#fff}.ops1077-table th,.ops1077-table td{padding:9px 10px;text-align:right;border-bottom:1px solid #edf2f7;font-size:11.5px}.ops1077-table th{background:#f7fafc;color:#475569;font-weight:800}.ops1077-muted{color:#94a3b8;text-align:center;padding:18px}
    .ops1077-more{position:fixed;inset:0;background:rgba(15,23,42,.35);z-index:9990;display:none;align-items:flex-end;justify-content:center}.ops1077-more.show{display:flex}.ops1077-sheet{width:min(520px,100%);background:#fff;border-radius:20px 20px 0 0;padding:16px;box-shadow:0 -12px 35px rgba(0,0,0,.15)}.ops1077-sheet h3{font-family:Cairo,sans-serif;color:#17496f;margin:0 0 10px}.ops1077-moregrid{display:grid;grid-template-columns:1fr 1fr;gap:8px}.ops1077-moregrid button{border:1px solid #dbe8f3;background:#f8fbfe;color:#17496f;border-radius:12px;padding:13px;font-family:Tajawal,sans-serif;font-weight:800;cursor:pointer}
    .ops1077-projectbar{display:flex;gap:8px;align-items:center;flex-wrap:wrap}.ops1077-projectbar select{flex:1;min-width:200px;border:1px solid #cbd5e1;border-radius:9px;padding:9px;background:#fff;font-family:Tajawal,sans-serif}
    .ops1077-note{background:#eff8ff;border:1px solid #cfe8fa;color:#31516f;border-radius:10px;padding:10px;font-size:11.5px;line-height:1.7}
    @media(max-width:700px){.ops1077-kpis{grid-template-columns:1fr 1fr}.ops1077-card{padding:10px}.tabs .tab{min-width:72px}.ops1077-head{flex-direction:column}}
  `;document.head.appendChild(s);
}

function setVersion(){
  document.querySelectorAll('#sec-db bdi').forEach(x=>{if(/^107\d$/.test((x.textContent||'').trim()))x.textContent='1077';});
}

function projectOptions(sel){return '<option value="">— اختر المشروع —</option>'+(window.projs||[]).map(p=>'<option value="'+esc2(p.id)+'" '+(p.id===sel?'selected':'')+'>'+esc2(p.name)+'</option>').join('');}
function supplierOptions(sel){return '<option value="">— بدون تحديد مورد —</option>'+arr('suppliers').filter(x=>x.active!==false).map(s=>'<option value="'+esc2(s.id)+'" '+(s.id===sel?'selected':'')+'>'+esc2(s.name)+'</option>').join('');}
function kpis(items){return '<div class="ops1077-kpis">'+items.map(x=>'<div class="ops1077-kpi"><span>'+x[0]+'</span><b>'+x[1]+'</b></div>').join('')+'</div>';}
function table(headers,rows){if(!rows.length)return '<div class="ops1077-muted">لا توجد بيانات حتى الآن</div>';return '<div class="ops1077-tablewrap"><table class="ops1077-table"><thead><tr>'+headers.map(x=>'<th>'+x+'</th>').join('')+'</tr></thead><tbody>'+rows.join('')+'</tbody></table></div>';}

function ensureMore(){
  if(document.querySelector('.tab[data-tab="more1077"]')) return;
  const tabs=document.querySelector('.tabs');if(!tabs)return;
  const t=document.createElement('div');t.className='tab';t.dataset.tab='more1077';t.innerHTML='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="5" cy="12" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/></svg><span>المزيد</span>';
  tabs.appendChild(t);t.addEventListener('click',showMore);
  const m=document.createElement('div');m.id='more1077';m.className='ops1077-more';m.innerHTML='<div class="ops1077-sheet"><h3>المزيد</h3><div class="ops1077-moregrid"><button onclick="closeMore1077();goTab(\'fs\')">دراسة الجدوى</button><button onclick="closeMore1077();goTab(\'vt\')">الضريبة</button><button onclick="closeMore1077();goTab(\'let\')">الخطابات</button><button onclick="closeMore1077();openSet()">الإعدادات</button></div><button class="ops1077-btn alt" style="width:100%;margin-top:10px" onclick="closeMore1077()">إغلاق</button></div>';
  m.addEventListener('click',e=>{if(e.target===m)closeMore1077();});document.body.appendChild(m);
}
function showMore(){document.getElementById('more1077')?.classList.add('show');}
window.closeMore1077=function(){document.getElementById('more1077')?.classList.remove('show');};

function ensurePurchasesTab(){
  if(document.querySelector('.tab[data-tab="proc"]')) return;
  const ls=document.querySelector('.tab[data-tab="ls"]');if(!ls)return;
  const t=document.createElement('div');t.className='tab';t.dataset.tab='proc';t.innerHTML='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 3h2l2.2 10.2a2 2 0 0 0 2 1.6H18a2 2 0 0 0 2-1.6L21 7H6"/><circle cx="10" cy="20" r="1"/><circle cx="18" cy="20" r="1"/></svg><span>المشتريات</span>';
  ls.insertAdjacentElement('afterend',t);t.addEventListener('click',()=>goTab('proc'));
}
function ensurePurchasesSection(){
  if(document.getElementById('sec-proc'))return;
  const sec=document.createElement('section');sec.className='sec';sec.id='sec-proc';sec.innerHTML='<h2 class="sec-ttl">المشتريات</h2><div class="ops1077-card"><div class="ops1077-head"><div><h3>الشراء المباشر</h3><p>سجل مشتريات المؤسسة مباشرة بدون أوامر شراء أو مقاولين من الباطن.</p></div><button class="ops1077-btn" onclick="opsOpen(\'purchase\')">＋ إضافة شراء</button></div><div class="ops1077-nav"><button id="purch-nav-list" class="on" onclick="renderPurchases1077(\'list\')">سجل المشتريات</button><button id="purch-nav-sup" onclick="renderPurchases1077(\'suppliers\')">الموردون</button></div><div id="purchases1077-body"></div></div>';
  const main=document.querySelector('main');main?.appendChild(sec);
}

function directPurchases(){return arr('purchaseOrders').slice().sort((a,b)=>(b.date||'').localeCompare(a.date||''));}
window.renderPurchases1077=function(view='list'){
  const b=document.getElementById('purchases1077-body');if(!b)return;
  document.getElementById('purch-nav-list')?.classList.toggle('on',view==='list');document.getElementById('purch-nav-sup')?.classList.toggle('on',view==='suppliers');
  if(view==='suppliers')return renderSuppliers1077(b);
  const l=directPurchases(),month=today().slice(0,7),lm=l.filter(x=>(x.date||'').slice(0,7)===month),total=l.reduce((s,x)=>s+num(x.total),0),vat=l.reduce((s,x)=>s+num(x.vat),0),paid=l.reduce((s,x)=>s+num(x.paid),0);
  let h=kpis([['مشتريات هذا الشهر',money(lm.reduce((s,x)=>s+num(x.total),0))],['إجمالي المشتريات',money(total)],['ضريبة المشتريات',money(vat)],['غير المسدد',money(Math.max(0,total-paid))]]);
  const rows=l.map(x=>'<tr><td>'+esc2(typeof fmtD==='function'?fmtD(x.date):x.date)+'</td><td>'+esc2(projectName(x.projectId))+'</td><td>'+esc2(supplierName(x.supplierId))+'</td><td>'+esc2(x.category||'—')+'</td><td>'+money(x.total)+'</td><td>'+esc2(x.paymentMethod||'—')+'</td><td>'+esc2(x.number||'—')+'</td><td><button class="ops1077-btn alt" onclick="opsOpen(\'purchase\',\''+esc2(x.id)+'\')">تعديل</button> <button class="ops1077-btn red" onclick="deletePurchase1077(\''+esc2(x.id)+'\')">حذف</button></td></tr>');
  h+=table(['التاريخ','المشروع','المورد','التصنيف','الإجمالي','الدفع','رقم الفاتورة',''],rows);b.innerHTML=h;
};
function renderSuppliers1077(b){const l=arr('suppliers').slice().sort((a,b)=>String(a.name||'').localeCompare(String(b.name||''),'ar'));let h='<div class="ops1077-actions"><button class="ops1077-btn" onclick="opsOpen(\'supplier\')">＋ مورد</button></div>';const rows=l.map(x=>'<tr><td><b>'+esc2(x.name||'—')+'</b></td><td>'+esc2(x.vat||'—')+'</td><td>'+esc2(x.phone||'—')+'</td><td>'+esc2(x.category||'—')+'</td><td><button class="ops1077-btn alt" onclick="opsOpen(\'supplier\',\''+esc2(x.id)+'\')">تعديل</button></td></tr>');h+=table(['المورد','الرقم الضريبي','الجوال','التصنيف',''],rows);b.innerHTML=h;}

function renderProject1077(){
  const b=document.getElementById('ops-body');if(!b)return;
  if(!window._opsProject||(window.projs||[]).every(p=>p.id!==window._opsProject))window._opsProject=((window.projs||[]).find(p=>p.status==='active')||(window.projs||[])[0]||{}).id||'';
  const pid=window._opsProject,p=(window.projs||[]).find(x=>x.id===pid);let h='<div class="ops1077-projectbar"><select onchange="window._opsProject=this.value;renderOps()">'+projectOptions(pid)+'</select><button class="ops1077-btn alt" onclick="opsOpen(\'budget\',\''+(arr('budgets').find(x=>x.projectId===pid)?.id||'')+'\',\''+esc2(pid)+'\')">الميزانية</button><button class="ops1077-btn" onclick="goTab(\'proc\');setTimeout(()=>opsOpen(\'purchase\',\'\',\''+esc2(pid)+'\'),60)">＋ شراء للمشروع</button></div>';
  if(!p){b.innerHTML=h+'<div class="ops1077-muted">أضف مشروعًا أولاً</div>';return;}
  const pl=typeof projPL==='function'?projPL(pid):{cost:0,paid:0,outstanding:0};const changes=arr('changeOrders').filter(x=>x.projectId===pid&&x.status==='approved').reduce((s,x)=>s+num(x.amount),0);const contract=num(p.contractValue)+changes;const purchases=directPurchases().filter(x=>x.projectId===pid).reduce((s,x)=>s+num(x.total),0);const claims=arr('claims').filter(x=>x.projectId===pid&&x.partyType!=='subcontractor');const uncol=claims.reduce((s,x)=>s+bal(x),0);const profit=contract-num(pl.cost);const margin=contract?profit/contract*100:0;const budget=arr('budgets').find(x=>x.projectId===pid);const use=budget&&num(budget.total)?num(pl.cost)/num(budget.total)*100:0;
  h+=kpis([['قيمة العقد',money(contract)],['التكلفة الفعلية',money(pl.cost)],['المشتريات المسجلة',money(purchases)],['الربح المتوقع',money(profit)]]);
  h+='<div class="ops1077-note">هامش الربح الحالي: <b>'+margin.toFixed(1)+'%</b> · استهلاك الميزانية: <b>'+(budget?use.toFixed(1)+'%':'لم تحدد')+'</b> · مستخلصات غير محصلة: <b>'+money(uncol)+'</b></div>';
  h+='<div class="ops1077-actions"><button class="ops1077-btn alt" onclick="window._opsView=\'changes\';renderOps()">أوامر التغيير</button><button class="ops1077-btn alt" onclick="goTab(\'ls\');setTimeout(()=>window._opsView=\'claims\'&&renderOps(),50)">المستخلصات</button><button class="ops1077-btn alt" onclick="goTab(\'proc\')">المشتريات</button></div>';
  b.innerHTML=h;
}

function postProcess(view){
  const b=document.getElementById('ops-body');if(!b)return;
  if(view==='claims'){
    b.querySelectorAll('tr').forEach(r=>{if((r.textContent||'').includes('مقاول باطن'))r.remove();});
    b.innerHTML=b.innerHTML.replaceAll('المدفوع/المحصّل','المحصّل').replaceAll('الجهة','النوع');
  }
  if(view==='aging')b.innerHTML=b.innerHTML.replaceAll('أمر شراء','شراء مباشر').replaceAll('مقاول باطن','مورد/مصروف');
  if(view==='users')b.innerHTML=b.innerHTML.replaceAll('مشتريات','إدخال مشتريات');
}

window.renderOps=function(){
  if(window._opsView==='overview')return renderProject1077();
  if(window._opsView==='procurement'){goTab('proc');return;}
  if(window._opsView==='suppliers'){goTab('proc');setTimeout(()=>renderPurchases1077('suppliers'),20);return;}
  if(window._opsView==='subs'){window._opsView='overview';return renderProject1077();}
  if(typeof baseRenderOps==='function')baseRenderOps();postProcess(window._opsView);
};

window.opsOpen=function(type,id,preset){
  if(type==='purchase')return openPurchase1077(id,preset);
  if(typeof baseOpsOpen==='function')baseOpsOpen(type,id,preset);
  if(type==='claim')setTimeout(()=>{
    const party=document.getElementById('of-party');if(party){party.value='client';party.closest('.ops-f')?.style.setProperty('display','none');}
    document.getElementById('of-sub')?.closest('.ops-f')?.style.setProperty('display','none');document.getElementById('of-subcontract')?.closest('.ops-f')?.style.setProperty('display','none');
  },0);
  if(type==='budget')setTimeout(()=>document.getElementById('of-subcontracts')?.closest('.ops-f')?.style.setProperty('display','none'),0);
};
function openPurchase1077(id,preset){
  const x=id?Object.assign({},arr('purchaseOrders').find(z=>z.id===id)||{}):{};window._opsEdit={type:'purchase',id:id||'',preset:preset||''};
  const pid=preset||x.projectId||'';const f=`
    <div class="ops-f"><label>التاريخ</label><input id="of-date" type="date" value="${esc2(x.date||today())}"></div>
    <div class="ops-f"><label>المشروع</label><select id="of-proj">${projectOptions(pid)}</select></div>
    <div class="ops-f"><label>المورد</label><select id="of-supplier">${supplierOptions(x.supplierId)}</select></div>
    <div class="ops-f"><label>تصنيف المصروف</label><input id="of-cat" type="text" value="${esc2(x.category||'')}" placeholder="مواد، نقل، معدات، خدمات..."></div>
    <div class="ops-f"><label>القيمة قبل الضريبة</label><input id="of-amount" type="number" step="0.01" value="${esc2(x.amount||'')}"></div>
    <div class="ops-f"><label>الضريبة %</label><input id="of-vrate" type="number" step="0.01" value="${esc2(x.vatRate??15)}"></div>
    <div class="ops-f"><label>المبلغ المسدد</label><input id="of-paid" type="number" step="0.01" value="${esc2(x.paid??'')}"></div>
    <div class="ops-f"><label>طريقة الدفع</label><select id="of-pay"><option ${x.paymentMethod==='تحويل'?'selected':''}>تحويل</option><option ${x.paymentMethod==='بطاقة'?'selected':''}>بطاقة</option><option ${x.paymentMethod==='نقدي'?'selected':''}>نقدي</option><option ${x.paymentMethod==='آجل'?'selected':''}>آجل</option></select></div>
    <div class="ops-f"><label>رقم الفاتورة/الإيصال</label><input id="of-no" type="text" value="${esc2(x.number||'')}"></div>
    <div class="ops-f full"><label>ملاحظات</label><textarea id="of-notes">${esc2(x.notes||'')}</textarea></div>`;
  document.getElementById('ops-modal-title').textContent=id?'تعديل شراء':'إضافة شراء';document.getElementById('ops-modal-body').innerHTML='<div class="ops-form">'+f+'</div>';document.getElementById('ops-modal').classList.add('show');
}
window.opsSaveForm=async function(){
  if(window._opsEdit?.type!=='purchase')return typeof baseOpsSave==='function'?baseOpsSave():undefined;
  const v=id=>document.getElementById(id)?.value||'';const date=v('of-date');if(typeof hdIsPeriodClosed==='function'&&hdIsPeriodClosed(date))return toast('🔒 لا يمكن الحفظ في فترة مقفلة','er');
  if(!v('of-proj'))return toast('اختر المشروع','er');if(!num(v('of-amount')))return toast('اكتب قيمة الشراء','er');
  const a=num(v('of-amount')),vr=num(v('of-vrate')),vat=a*vr/100,total=a+vat;let paid=v('of-paid')===''?total:num(v('of-paid'));
  const old=window._opsEdit.id?arr('purchaseOrders').find(x=>x.id===window._opsEdit.id):null;const x=Object.assign(old||{id:typeof uid==='function'?uid('buy'):'buy_'+Date.now(),createdAt:Date.now()},{date,projectId:v('of-proj'),supplierId:v('of-supplier'),category:v('of-cat').trim(),amount:a,vatRate:vr,vat,total,paid,paymentMethod:v('of-pay'),number:v('of-no').trim(),dueDate:date,status:paid>=total?'paid':paid>0?'partial':'open',notes:v('of-notes').trim(),directPurchase:true,updatedAt:Date.now()});
  if(!old)arr('purchaseOrders').unshift(x);await svOps(false);window.opsCloseModal();renderPurchases1077('list');if(typeof renderOpsDashboardStrip==='function')renderOpsDashboardStrip();toast('✅ تم حفظ الشراء','ok');
};
window.deletePurchase1077=async function(id){const x=arr('purchaseOrders').find(z=>z.id===id);if(!x)return;const ok=typeof confirm2==='function'?await confirm2({title:'حذف الشراء',msg:'هل تريد حذف هذا الشراء؟',ok:'حذف',danger:true}):confirm('حذف؟');if(!ok)return;D().purchaseOrders=arr('purchaseOrders').filter(z=>z.id!==id);await svOps(false);renderPurchases1077('list');if(typeof renderOpsDashboardStrip==='function')renderOpsDashboardStrip();};

function dashboard(){
  window.renderOpsDashboardStrip=function(){const w=document.getElementById('ops-db-strip');if(!w)return;const claims=arr('claims').filter(x=>x.partyType!=='subcontractor'),p=directPurchases(),month=today().slice(0,7),ar=claims.filter(x=>!['paid','cancelled'].includes(x.status)).reduce((s,x)=>s+bal(x),0),pm=p.filter(x=>(x.date||'').slice(0,7)===month).reduce((s,x)=>s+num(x.total),0),alerts=(window.projs||[]).filter(x=>x.status==='active'&&!arr('budgets').some(b=>b.projectId===x.id)).length+claims.filter(x=>x.dueDate&&new Date(x.dueDate)<new Date()&&bal(x)>0).length;w.innerHTML='<div class="ops-db-strip"><div class="ops-db-mini" onclick="goTab(\'proj\')"><b>'+alerts+'</b><span>تنبيهات تحتاج متابعة</span></div><div class="ops-db-mini" onclick="goTab(\'ls\')"><b>'+money(ar)+'</b><span>مستخلصات غير محصلة</span></div><div class="ops-db-mini" onclick="goTab(\'proc\')"><b>'+money(pm)+'</b><span>مشتريات هذا الشهر</span></div></div>';};
  try{renderOpsDashboardStrip();}catch(e){}
}

function navigation(){
  if(typeof baseGoTab==='function')window.goTab=function(n){
    if(n==='more1077'){showMore();return;}
    const r=baseGoTab(n);setTimeout(()=>{
      if(n==='proj'){window._opsView='overview';moveOps('project');renderOps();}
      else if(n==='ls'){window._opsView='claims';moveOps('claims');renderOps();}
      else if(n==='acc'){window._opsView='cashflow';moveOps('accounting');renderOps();}
      else if(n==='vt'){window._opsView='zatca';moveOps('tax');renderOps();}
      else if(n==='proc')renderPurchases1077('list');
    },20);return r;
  };
  if(typeof baseOpenSet==='function')window.openSet=function(){const r=baseOpenSet();setTimeout(()=>{window._opsView='users';moveOps('settings');renderOps();},30);return r;};
}
function ensureHosts(){
  const specs=[['sec-proj','project','إدارة المشروع','العقد والميزانية والربحية وأوامر التغيير في مكان واحد.'],['sec-ls','claims','المستخلصات','المستخلصات والتحصيلات المرتبطة بالمشاريع.'],['sec-acc','accounting','المالية المتقدمة','التدفق النقدي والذمم والتسوية البنكية وإقفال الفترات.'],['sec-vt','tax','الفوترة الإلكترونية','جاهزية المرحلة الثانية للفوترة الإلكترونية.']];
  specs.forEach(([secid,id,title,desc])=>{const sec=document.getElementById(secid);if(!sec||document.getElementById('ops1077-'+id))return;const d=document.createElement('div');d.className='ops1077-card';d.id='ops1077-'+id;d.innerHTML='<div class="ops1077-head"><div><h3>'+title+'</h3><p>'+desc+'</p></div></div><div id="ops1077-'+id+'-body"></div>';sec.appendChild(d);});
  const set=document.querySelector('#set-mb .md');if(set&&!document.getElementById('ops1077-settings')){const d=document.createElement('div');d.className='ops1077-card';d.id='ops1077-settings';d.innerHTML='<div class="ops1077-head"><div><h3>المستخدمون والصلاحيات</h3><p>إدارة المستخدمين من داخل الإعدادات.</p></div></div><div id="ops1077-settings-body"></div>';set.appendChild(d);}
}
function moveOps(area){const body=document.getElementById('ops-body'),dest=document.getElementById('ops1077-'+area+'-body');if(body&&dest&&body.parentElement!==dest)dest.appendChild(body);}

function boot(){
  style();setVersion();ensurePurchasesTab();ensurePurchasesSection();ensureMore();ensureHosts();navigation();dashboard();
  document.querySelector('.tab[data-tab="ops"]')?.remove();
  const active=document.querySelector('.tab.active')?.dataset.tab||'db';if(active==='proj'){window._opsView='overview';moveOps('project');renderOps();}else if(active==='ls'){window._opsView='claims';moveOps('claims');renderOps();}else if(active==='proc')renderPurchases1077('list');
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(boot,80));else setTimeout(boot,80);
})();
