/* هدف التنمية — 1078 — تنظيم الإعدادات */
(function(){
'use strict';
if(window.__HD_SETTINGS_1078__)return;window.__HD_SETTINGS_1078__=1;

function addStyle(){
 if(document.getElementById('hdset1078css'))return;
 const s=document.createElement('style');s.id='hdset1078css';s.textContent=`
 #set-mb .md{max-width:620px}
 .set1078-home{padding:2px 0 4px}
 .set1078-intro{background:linear-gradient(135deg,#eef6fc,#f8fbfe);border:1px solid #d9e9f5;border-radius:12px;padding:11px 12px;margin-bottom:10px;color:#31516f;font-size:11.5px;line-height:1.7}
 .set1078-grid{display:grid;grid-template-columns:1fr 1fr;gap:9px}
 .set1078-card{border:1px solid #dce8f2;background:#fff;border-radius:13px;padding:14px 12px;text-align:right;cursor:pointer;font-family:Tajawal,sans-serif;min-height:96px;transition:.15s;box-shadow:0 2px 8px rgba(27,72,108,.04)}
 .set1078-card:hover{border-color:#8bb8d8;transform:translateY(-1px);box-shadow:0 5px 15px rgba(27,72,108,.08)}
 .set1078-ic{font-size:24px;display:block;margin-bottom:6px}.set1078-card b{display:block;color:#17496f;font-family:Cairo,sans-serif;font-size:13px}.set1078-card small{display:block;color:#64748b;margin-top:3px;font-size:10.8px;line-height:1.5}
 .set1078-panel{display:none}.set1078-panel.on{display:block}.set1078-panel-head{display:flex;gap:8px;align-items:center;margin-bottom:10px;padding-bottom:9px;border-bottom:1px solid #edf2f7}.set1078-back{border:0;background:#edf5fb;color:#1d5e8e;border-radius:9px;padding:8px 11px;font-family:Tajawal,sans-serif;font-weight:800;cursor:pointer}.set1078-panel-title{font-family:Cairo,sans-serif;font-weight:900;color:#17496f;font-size:14px}
 .set1078-panel>.card,.set1078-panel>button,.set1078-panel>div:not(.set1078-panel-head){margin-bottom:9px!important}
 .set1078-link{width:100%;margin-top:10px;border:1px dashed #9ec3dd;background:#f8fbfe;color:#1e5d8d;border-radius:10px;padding:10px;font-family:Tajawal,sans-serif;font-weight:800;cursor:pointer}
 #tools1078{position:fixed;inset:0;z-index:10020;background:rgba(15,23,42,.48);display:none;align-items:flex-end;justify-content:center;padding-top:30px}.tools1078-box{background:#f8fafc;width:min(620px,100%);max-height:90vh;overflow:auto;border-radius:22px 22px 0 0;padding:15px}.tools1078-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:10px}.tools1078-head h3{font-family:Cairo,sans-serif;color:#17496f;font-size:15px}.tools1078-close{border:0;background:#eaf1f6;border-radius:50%;width:34px;height:34px;cursor:pointer;font-size:16px}.tools1078-nav{display:flex;gap:7px;margin-bottom:11px;overflow:auto}.tools1078-nav button{border:1px solid #d4e2ed;background:#fff;color:#31516f;border-radius:999px;padding:8px 11px;font-family:Tajawal,sans-serif;font-weight:800;white-space:nowrap;cursor:pointer}.tools1078-nav button.on{background:#2771ab;color:#fff;border-color:#2771ab}.tools1078-pane{display:none}.tools1078-pane.on{display:block}.tools1078-pane>.card,.tools1078-pane>button{margin-bottom:9px!important}
 @media(max-width:520px){.set1078-grid{grid-template-columns:1fr 1fr}.set1078-card{min-height:92px;padding:12px 10px}.set1078-card small{font-size:10px}}
 `;document.head.appendChild(s);
}

function panelHead(title){return '<div class="set1078-panel-head"><button class="set1078-back" onclick="set1078Home()">‹ رجوع</button><div class="set1078-panel-title">'+title+'</div></div>';}
function isReport(el){const t=(el.innerText||'').trim();return /المدقق الداخلي|تقارير التدقيق|المدير المالي|تقييم المنشأة|راتب المالك|تقرير شهري|اسأل بالعربي/.test(t)}
function isDocs(el){return /الوثائق الرسمية/.test((el.innerText||''))}
function isGeneral(el){const t=el.innerText||'';return !!el.querySelector?.('#set-nm,#set-vn,#set-cr')||/بيانات المؤسسة/.test(t)}
function isUsers(el){const t=el.innerText||'';return el.id==='h1077-set'||/المستخدمون والصلاحيات/.test(t)}
function isLink(el){const t=el.innerText||'';return !!el.querySelector?.('#set-apikey,#apikey-status,#sync-info,#backup-status,#set-cloud-on')||/مفتاح.*API|مفتاح.*الذكاء|المزامنة السحابية|النسخ الاحتياطي والمزامنة|نسخ احتياطي تلقائي/.test(t)}
function isFooter(el){return /جميع حقوق الطبع|إصدار التطبيق/.test(el.innerText||'')}

function ensureTools(){
 if(document.getElementById('tools1078'))return;
 const m=document.createElement('div');m.id='tools1078';m.onclick=e=>{if(e.target===m)closeTools1078()};
 m.innerHTML='<div class="tools1078-box"><div class="tools1078-head"><h3>الأدوات والتقارير</h3><button class="tools1078-close" onclick="closeTools1078()">✕</button></div><div class="tools1078-nav"><button id="tools1078-rb" onclick="tools1078Tab(\'reports\')">التقارير والتحليلات</button><button id="tools1078-db" onclick="tools1078Tab(\'docs\')">المستندات الرسمية</button></div><div id="tools1078-reports" class="tools1078-pane"></div><div id="tools1078-docs" class="tools1078-pane"></div></div>';
 document.body.appendChild(m);
}
window.tools1078Tab=function(k){document.querySelectorAll('.tools1078-pane').forEach(x=>x.classList.remove('on'));document.querySelectorAll('.tools1078-nav button').forEach(x=>x.classList.remove('on'));document.getElementById('tools1078-'+k)?.classList.add('on');document.getElementById(k==='reports'?'tools1078-rb':'tools1078-db')?.classList.add('on');if(k==='docs'&&typeof renderDocs==='function')try{renderDocs()}catch(e){}};
window.openTools1078=function(k){ensureTools();document.getElementById('tools1078').style.display='flex';tools1078Tab(k||'reports')};
window.closeTools1078=function(){const m=document.getElementById('tools1078');if(m)m.style.display='none'};

function addToMore(){
 const grid=document.querySelector('#h1077more .h1077-grid');if(!grid||document.getElementById('more-reports-1078'))return;
 const r=document.createElement('button');r.id='more-reports-1078';r.textContent='التقارير والتحليلات';r.onclick=()=>{if(typeof close1077==='function')close1077();openTools1078('reports')};
 const d=document.createElement('button');d.id='more-docs-1078';d.textContent='المستندات الرسمية';d.onclick=()=>{if(typeof close1077==='function')close1077();openTools1078('docs')};
 grid.insertBefore(r,grid.firstChild);grid.insertBefore(d,r.nextSibling);
}

function organize(){
 addStyle();ensureTools();addToMore();
 const md=document.querySelector('#set-mb .md');if(!md)return;
 if(document.getElementById('set1078-home'))return;
 const hdr=md.querySelector('.md-hdr');
 const items=[...md.children].filter(x=>x!==hdr&&!x.classList.contains('set1078-home')&&!x.classList.contains('set1078-panel'));
 const home=document.createElement('div');home.id='set1078-home';home.className='set1078-home';home.innerHTML='<div class="set1078-intro"><b>إعدادات النظام</b><br>رتّبنا الخيارات إلى أربع مجموعات فقط. الأدوات والتقارير والمستندات أصبحت في «المزيد» حتى تبقى الإعدادات خفيفة وواضحة.</div><div class="set1078-grid"><button class="set1078-card" onclick="set1078Open(\'general\')"><span class="set1078-ic">🏢</span><b>عام</b><small>بيانات المؤسسة والإعدادات الأساسية</small></button><button class="set1078-card" onclick="set1078Open(\'users\')"><span class="set1078-ic">👥</span><b>المستخدمون</b><small>المستخدمون والصلاحيات وسجل الدخول</small></button><button class="set1078-card" onclick="set1078Open(\'link\')"><span class="set1078-ic">☁️</span><b>الربط والنسخ</b><small>السحابة والنسخ الاحتياطي والذكاء الاصطناعي</small></button><button class="set1078-card" onclick="set1078Open(\'advanced\')"><span class="set1078-ic">🛠️</span><b>متقدم</b><small>التصحيح والفحص والتنظيف والإجراءات الحساسة</small></button></div><button class="set1078-link" onclick="closeSet();openTools1078(\'reports\')">فتح التقارير والمستندات من قسم «المزيد»</button>';
 md.insertBefore(home,hdr?.nextSibling||md.firstChild);
 const defs=[['general','عام'],['users','المستخدمون والصلاحيات'],['link','الربط والنسخ'],['advanced','متقدم']];
 const panels={};defs.forEach(([k,t])=>{const p=document.createElement('div');p.id='set1078-'+k;p.className='set1078-panel';p.innerHTML=panelHead(t);md.appendChild(p);panels[k]=p});
 const rep=document.getElementById('tools1078-reports'),docs=document.getElementById('tools1078-docs');
 items.forEach(el=>{
   if(isFooter(el)){el.style.display='none';md.appendChild(el);return}
   if(isReport(el)){rep.appendChild(el);return}
   if(isDocs(el)){docs.appendChild(el);return}
   if(isGeneral(el)){panels.general.appendChild(el);return}
   if(isUsers(el)){panels.users.appendChild(el);return}
   if(isLink(el)){panels.link.appendChild(el);return}
   panels.advanced.appendChild(el);
 });
 // إن لم توجد عناصر مستخدمين لحظة الترتيب، سيتم التقاطها لاحقاً عند فتح الصفحة.
 set1078Home();
}
window.set1078Home=function(){document.querySelectorAll('.set1078-panel').forEach(x=>x.classList.remove('on'));const h=document.getElementById('set1078-home');if(h)h.style.display='block'};
window.set1078Open=function(k){organize();const h=document.getElementById('set1078-home');if(h)h.style.display='none';document.querySelectorAll('.set1078-panel').forEach(x=>x.classList.remove('on'));document.getElementById('set1078-'+k)?.classList.add('on');if(k==='users'&&typeof renderOps==='function'){try{window._opsView='users';const body=document.getElementById('ops-body'),dest=document.getElementById('h1077-set-body')||document.getElementById('ops-users-settings');if(body&&dest)dest.appendChild(body);renderOps()}catch(e){}}};

function sweepLate(){
 const md=document.querySelector('#set-mb .md');if(!md||!document.getElementById('set1078-home'))return;
 const known=[...md.children].filter(x=>x!==md.querySelector('.md-hdr')&&x.id!=='set1078-home'&&!x.classList.contains('set1078-panel')&&!isFooter(x));
 known.forEach(el=>{if(isReport(el))document.getElementById('tools1078-reports')?.appendChild(el);else if(isDocs(el))document.getElementById('tools1078-docs')?.appendChild(el);else if(isUsers(el))document.getElementById('set1078-users')?.appendChild(el);else if(isGeneral(el))document.getElementById('set1078-general')?.appendChild(el);else if(isLink(el))document.getElementById('set1078-link')?.appendChild(el);else document.getElementById('set1078-advanced')?.appendChild(el)});
}

const baseOpen=window.openSet;
if(typeof baseOpen==='function')window.openSet=function(){const r=baseOpen.apply(this,arguments);setTimeout(()=>{organize();sweepLate();set1078Home()},20);return r};

function version(){try{const m=document.querySelector('meta[name="app-build"]');if(m)m.content='2026-09-15-1078';document.querySelectorAll('bdi').forEach(x=>{if(/^107\d$/.test((x.textContent||'').trim()))x.textContent='1078'})}catch(e){}}
function boot(){addStyle();ensureTools();setTimeout(()=>{organize();sweepLate();addToMore();version()},120)}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();
