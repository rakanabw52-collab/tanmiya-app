/* هدف التنمية — 1076
   دمج وظائف المقاولات داخل أقسام النظام الأصلي بدون صفحة مستقلة. */
(function(){
'use strict';
if(window.__TANMIYA_1076_INTEGRATED__) return;
window.__TANMIYA_1076_INTEGRATED__=true;

const areaViews={project:'overview',invoices:'claims',procurement:'procurement',accounting:'cashflow',tax:'zatca',settings:'users'};
const areaTabs={project:'proj',invoices:'ls',procurement:'proc',accounting:'acc',tax:'vt'};
const areaBodies={project:'ops-project-body',invoices:'ops-invoices-body',procurement:'ops-proc-body',accounting:'ops-accounting-body',tax:'ops-tax-body',settings:'ops-users-settings'};

function injectStyle(){
  if(document.getElementById('integrated1076-style')) return;
  const s=document.createElement('style');s.id='integrated1076-style';s.textContent=`
  #sec-proc{max-width:1200px;margin:0 auto}
  .ops-integrated-block{margin:14px 0 0;padding:14px;background:#fff;border:1px solid #dbe8f3;border-radius:14px;box-shadow:0 3px 12px rgba(23,73,111,.06)}
  .ops-integrated-head{display:flex;align-items:flex-start;justify-content:space-between;gap:10px;margin-bottom:10px}
  .ops-integrated-head h3{font-family:'Cairo',sans-serif;font-size:14px;font-weight:900;color:#17496f;margin:0}
  .ops-integrated-head p{font-size:11.5px;color:#64748b;margin:2px 0 0;line-height:1.6}
  .ops-integrated-save{border:none;background:#eef6fc;color:#1e5d8d;padding:7px 10px;border-radius:8px;font-family:'Tajawal',sans-serif;font-size:11px;font-weight:800;cursor:pointer;white-space:nowrap}
  .ops-integrated-block .ops-nav{margin-bottom:11px}
  #sec-ops{display:none!important}
  #ops-users-settings{margin-top:8px}
  @media(max-width:680px){.ops-integrated-head{flex-direction:column}.ops-integrated-save{width:100%}.ops-integrated-block{padding:10px}}
  `;document.head.appendChild(s);
}

function nav(area,items){
  return '<div class="ops-nav ops-nav-1076" data-area="'+area+'">'+items.map(x=>'<button data-view="'+x[0]+'" onclick="opsEmbed1076(\''+area+'\',\''+x[0]+'\')">'+x[1]+'</button>').join('')+'</div>';
}
function head(title,desc,save=true){return '<div class="ops-integrated-head"><div><h3>'+title+'</h3><p>'+desc+'</p></div>'+(save?'<button class="ops-integrated-save" onclick="svOps(true)">💾 حفظ</button>':'')+'</div>';}

function ensureShell(){
  injectStyle();
  try{const m=document.querySelector('meta[name="app-build"]');if(m)m.content='2026-09-15-1076';document.querySelectorAll('#sec-db bdi').forEach(x=>{if(/^107\d$/.test((x.textContent||'').trim()))x.textContent='1076';});}catch(e){}

  const oldTab=document.querySelector('.tab[data-tab="ops"]');if(oldTab)oldTab.remove();
  const oldSec=document.getElementById('sec-ops');if(oldSec)oldSec.style.display='none';

  const lsTab=document.querySelector('.tab[data-tab="ls"]');
  if(lsTab&&!document.querySelector('.tab[data-tab="proc"]')){
    const t=document.createElement('div');t.className='tab';t.dataset.tab='proc';
    t.innerHTML='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="9" cy="20" r="1"/><circle cx="19" cy="20" r="1"/><path d="M3 4h2l2.4 10.4A2 2 0 0 0 9.35 16H18a2 2 0 0 0 1.95-1.57L21 8H6"/></svg><span>المشتريات</span>';
    lsTab.insertAdjacentElement('afterend',t);t.addEventListener('click',()=>goTab('proc'));
  }

  const secProj=document.getElementById('sec-proj');
  if(secProj&&!document.getElementById('ops-project-body')){
    const d=document.createElement('div');d.className='ops-integrated-block';d.id='ops-project-center';
    d.innerHTML=head('🏗️ إدارة المشروع','العقد والميزانية والتغييرات ومقاولو الباطن والربحية في نفس صفحة المشروع.')+nav('project',[["overview","مركز المشروع والميزانية"],["changes","أوامر التغيير"],["subs","مقاولو الباطن"]])+'<div id="ops-project-body"></div>';
    const cols=secProj.querySelector('.proj-cols');if(cols)cols.insertAdjacentElement('beforebegin',d);else secProj.appendChild(d);
  }

  const secLs=document.getElementById('sec-ls');
  if(secLs&&!document.getElementById('ops-invoices-body')){
    const d=document.createElement('div');d.className='ops-integrated-block';d.id='ops-claims-section';
    d.innerHTML=head('▤ المستخلصات والتحصيلات التعاقدية','مستخلصات العملاء ومقاولي الباطن، الاستحقاقات، المسدد والمتأخر.')+nav('invoices',[["claims","المستخلصات"]])+'<div id="ops-invoices-body"></div>';
    secLs.appendChild(d);
  }

  if(!document.getElementById('sec-proc')){
    const sec=document.createElement('section');sec.className='sec';sec.id='sec-proc';
    sec.innerHTML='<h2 class="sec-ttl">المشتريات والموردون</h2><div class="ops-integrated-block" style="margin-top:0">'+head('🛒 دورة المشتريات','طلب تسعير ← اختيار المورد ← أمر شراء ← استحقاق ودفع.')+nav('procurement',[["procurement","أوامر الشراء وطلبات التسعير"],["suppliers","الموردون"]])+'<div id="ops-proc-body"></div></div>';
    const fs=document.getElementById('sec-fs');if(fs)fs.insertAdjacentElement('beforebegin',sec);else document.querySelector('main')?.appendChild(sec);
  }

  const secAcc=document.getElementById('sec-acc');
  if(secAcc&&!document.getElementById('ops-accounting-body')){
    const d=document.createElement('div');d.className='ops-integrated-block';d.id='ops-finance-section';
    d.innerHTML=head('💹 النقد والذمم والتسويات','تدفق 30/60/90 يوم، أعمار الذمم، التسوية البنكية، وإقفال الفترات.')+nav('accounting',[["cashflow","التدفق النقدي"],["aging","الذمم والأعمار"],["bank","التسوية البنكية"],["period","الإقفال وعكس القيود"]])+'<div id="ops-accounting-body"></div>';
    secAcc.appendChild(d);
  }

  const secVt=document.getElementById('sec-vt');
  if(secVt&&!document.getElementById('ops-tax-body')){
    const d=document.createElement('div');d.className='ops-integrated-block';d.id='ops-zatca-section';
    d.innerHTML=head('🧾 الفوترة الإلكترونية — المرحلة الثانية','فحص الجاهزية وإعداد بيئة الربط والشهادة بدون تخزين أسرار داخل المستودع.',false)+nav('tax',[["zatca","جاهزية الفوترة الإلكترونية"]])+'<div id="ops-tax-body"></div>';
    secVt.appendChild(d);
  }

  const setModal=document.querySelector('#set-mb .md');
  if(setModal&&!document.getElementById('ops-users-settings')){
    const d=document.createElement('div');d.className='card';d.style.cssText='background:#fff;border:1px solid #DBEAFE';
    d.innerHTML='<div style="font-family:Cairo,sans-serif;font-weight:800;color:#17496F;font-size:14px;margin-bottom:6px">👥 المستخدمون والصلاحيات</div><div style="font-size:11.5px;color:#64748b;line-height:1.6;margin-bottom:8px">إدارة الهيكل التشغيلي والصلاحيات من داخل الإعدادات بدل صفحة مستقلة.</div><div id="ops-users-settings"></div>';
    const firstCard=setModal.querySelector('.card');if(firstCard)firstCard.insertAdjacentElement('beforebegin',d);else setModal.appendChild(d);
  }
}

function setActive(area,view){document.querySelectorAll('.ops-nav-1076[data-area="'+area+'"] button').forEach(b=>b.classList.toggle('on',b.dataset.view===view));}
function parkBody(){const body=document.getElementById('ops-body'),host=document.getElementById('sec-ops');if(body&&host&&body.parentElement!==host)host.appendChild(body);}

window.opsEmbed1076=function(area,view){
  ensureShell();areaViews[area]=view||areaViews[area];
  const dest=document.getElementById(areaBodies[area]);const body=document.getElementById('ops-body');if(!dest||!body)return;
  if(body.parentElement!==dest)dest.appendChild(body);
  setActive(area,areaViews[area]);
  if(typeof window.opsGo==='function')window.opsGo(areaViews[area]);
};
window.opsRoute1076=function(area,view){
  ensureShell();const tab=areaTabs[area];if(tab)goTab(tab);else if(area==='settings')openSet();
  setTimeout(()=>{opsEmbed1076(area,view||areaViews[area]);document.getElementById(areaBodies[area])?.scrollIntoView({behavior:'smooth',block:'start'});},50);
};

function wrapNavigation(){
  if(typeof window.goTab==='function'&&!window.goTab.__integrated1076){
    const base=window.goTab;const w=function(n){const r=base(n);setTimeout(()=>{
      if(n==='proj')opsEmbed1076('project',areaViews.project);
      else if(n==='ls')opsEmbed1076('invoices',areaViews.invoices);
      else if(n==='proc')opsEmbed1076('procurement',areaViews.procurement);
      else if(n==='acc')opsEmbed1076('accounting',areaViews.accounting);
      else if(n==='vt')opsEmbed1076('tax',areaViews.tax);
      else parkBody();
    },0);return r;};w.__integrated1076=true;window.goTab=w;
  }
  if(typeof window.openSet==='function'&&!window.openSet.__integrated1076){
    const base=window.openSet;const w=function(){const r=base();setTimeout(()=>opsEmbed1076('settings','users'),0);return r;};w.__integrated1076=true;window.openSet=w;
  }
}

function replaceDashboardStrip(){
  window.renderOpsDashboardStrip=function(){
    const w=document.getElementById('ops-db-strip');if(!w)return;
    const d=window.opsData||{},n=v=>Number(v||0)||0,m=v=>(typeof fmtI==='function'?fmtI(v):Math.round(v).toLocaleString('ar-SA'))+' ر.س';
    const projects=Array.isArray(window.projs)?window.projs:[];
    const claims=Array.isArray(d.claims)?d.claims:[],pos=Array.isArray(d.purchaseOrders)?d.purchaseOrders:[],dues=Array.isArray(d.dues)?d.dues:[],cash=Array.isArray(d.cashflow)?d.cashflow:[],changes=Array.isArray(d.changeOrders)?d.changeOrders:[],banks=Array.isArray(d.bankRecons)?d.bankRecons:[],budgets=Array.isArray(d.budgets)?d.budgets:[];
    const bal=x=>Math.max(0,n(x.total||x.amount)-n(x.paid));
    const now=new Date(),lim=new Date(now.getTime()+30*86400000);const in30=x=>x&&new Date(x)>=now&&new Date(x)<=lim;
    let alerts=projects.filter(p=>p.status==='active'&&!budgets.some(b=>b.projectId===p.id)).length;
    alerts+=claims.filter(x=>!['paid','cancelled'].includes(x.status)&&x.dueDate&&new Date(x.dueDate)<now&&bal(x)>0).length;
    alerts+=changes.filter(x=>x.status==='pending'&&x.date&&((now-new Date(x.date))/86400000)>30).length;
    alerts+=banks.filter(x=>Math.abs(n(x.bankAmount)-n(x.bookAmount))>.009).length;
    const ar=claims.filter(x=>x.partyType!=='subcontractor'&&!['paid','cancelled'].includes(x.status)).reduce((s,x)=>s+bal(x),0)+dues.filter(x=>x.side==='ar'&&x.status!=='paid').reduce((s,x)=>s+bal(x),0);
    const poOpen=pos.filter(x=>!['cancelled','paid'].includes(x.status)).reduce((s,x)=>s+bal(x),0);
    let cin=claims.filter(x=>x.partyType!=='subcontractor'&&!['paid','cancelled'].includes(x.status)&&in30(x.dueDate)).reduce((s,x)=>s+bal(x),0)+dues.filter(x=>x.side==='ar'&&x.status!=='paid'&&in30(x.dueDate)).reduce((s,x)=>s+bal(x),0)+cash.filter(x=>x.direction==='in'&&x.status!=='cancelled'&&in30(x.date)).reduce((s,x)=>s+n(x.amount),0);
    let cout=pos.filter(x=>!['cancelled','paid'].includes(x.status)&&in30(x.dueDate)).reduce((s,x)=>s+bal(x),0)+dues.filter(x=>x.side==='ap'&&x.status!=='paid'&&in30(x.dueDate)).reduce((s,x)=>s+bal(x),0)+cash.filter(x=>x.direction==='out'&&x.status!=='cancelled'&&in30(x.date)).reduce((s,x)=>s+n(x.amount),0);
    const net=cin-cout;
    const cards=[
      ['project','overview',String(alerts),'تنبيهات تنفيذية'],
      ['accounting','aging',m(ar),'ذمم مدينة مجدولة'],
      ['procurement','procurement',m(poOpen),'التزامات المشتريات'],
      ['accounting','cashflow',m(net),'صافي تدفق 30 يوم']
    ];
    w.innerHTML='<div class="ops-db-strip">'+cards.map(c=>'<div class="ops-db-mini" onclick="opsRoute1076(\''+c[0]+'\',\''+c[1]+'\')"><b>'+c[2]+'</b><span>'+c[3]+'</span></div>').join('')+'</div>';
  };
  try{window.renderOpsDashboardStrip();}catch(e){}
}

function boot(){
  ensureShell();wrapNavigation();replaceDashboardStrip();
  const active=document.querySelector('.tab.active')?.dataset.tab||'db';
  if(active==='proj')opsEmbed1076('project','overview');
  else if(active==='ls')opsEmbed1076('invoices','claims');
  else if(active==='proc')opsEmbed1076('procurement','procurement');
  else if(active==='acc')opsEmbed1076('accounting','cashflow');
  else if(active==='vt')opsEmbed1076('tax','zatca');
  else parkBody();
}

if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(boot,50));else setTimeout(boot,50);
})();
