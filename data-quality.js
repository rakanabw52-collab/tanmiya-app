/* Data review: report uncertain legacy facts; never invent dates, receipts or totals. */
(function(){
'use strict';
const money=x=>toNum(x).toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2}),active=x=>x&&x.status!=='cancelled';
// ====== تظليل الخانة المعنية بالملاحظة بالأحمر عند فتح السجل ======
// لكل نوع ملاحظة: الخانات التي يجب تعبئتها/تصحيحها في النموذج المفتوح
const DQ_FIELDS={
 amount:['f-sub','f-v','f-tot'], vatrate:['f-vr','f-v'], empty:['f-sub','f-tot'],
 precision:['f-sub','f-v','f-tot'], future:['f-dt'], revenue:['f-proj'],
 posting:['of-date','of-cat'], overpaid:['of-paid']
};
function _dqInjectStyle(){
 if(document.getElementById('dq-focus-style'))return;
 const s=document.createElement('style');s.id='dq-focus-style';
 s.textContent='.dq-focus{border:2px solid #B91C1C!important;background:#FEF2F2!important;box-shadow:0 0 0 3px rgba(185,28,28,.15)!important;border-radius:8px!important}'
  +'.dq-focus-note{color:#B91C1C;font-weight:700;font-size:12px;margin:4px 0;display:block}';
 document.head.append(s);
}
function _dqClearFocus(){document.querySelectorAll('.dq-focus').forEach(e=>e.classList.remove('dq-focus'));document.querySelectorAll('.dq-focus-note').forEach(e=>e.remove());}
// يطبّق التظليل بعد أن يُبنى النموذج (ينتظر ظهور الخانات حتى 1.5 ثانية)
window._dqApplyFocus=function(fields,msg){
 if(!fields||!fields.length)return; _dqInjectStyle();
 let tries=0; const t=setInterval(()=>{
  tries++; const found=fields.map(id=>document.getElementById(id)).filter(Boolean);
  if(found.length||tries>15){
   clearInterval(t); _dqClearFocus();
   found.forEach((el,n)=>{const box=el.closest('.field,.ops-f,.fld,div')||el;el.classList.add('dq-focus');
    if(n===0){const p=document.createElement('span');p.className='dq-focus-note';p.textContent='⚠️ '+(msg||'عبّئ/صحّح هذه الخانة');(box.parentNode||box).insertBefore(p,box);
     el.scrollIntoView({behavior:'smooth',block:'center'});}});
  }
 },100);
};
function dqFocusAfter(kind,run){const f=DQ_FIELDS[kind]||[];run();if(f.length)window._dqApplyFocus(f,'هذه الخانة سبب الملاحظة — عبّئها أو صحّحها');}
const norm=s=>String(s||'').replace(/[أإآ]/g,'ا').replace(/ة/g,'ه').replace(/مشروع/g,'').replace(/\s+/g,'').trim();
window.getDataQualityIssues=function(){
 const issues=[],add=(kind,title,detail,ref)=>issues.push({kind,title,detail,...ref});
 const invoices=invs.filter(active),orders=(window.opsData?.purchaseOrders||[]).filter(active);
 const orphanGroups=new Map();
 invoices.forEach(i=>{
  if(i.projectId&&!hasKnownProject(i)){if(!orphanGroups.has(i.projectId))orphanGroups.set(i.projectId,[]);orphanGroups.get(i.projectId).push(i);}
  if(invoiceMoneyIssue(i))add('amount','مبالغ فاتورة تحتاج مراجعة','رقم '+i.number+': الإجمالي '+money(i.total)+'، الصافي '+money(i.subtotal)+'، الضريبة '+money(i.vat),{invoiceId:i.id});
  if(i.date>_todayStr())add('future','تاريخ فاتورة مستقبلي','رقم '+i.number+' بتاريخ '+i.date+'؛ تحقق من المستند.',{invoiceId:i.id});
  if(i.type==='revenue'&&!hasKnownProject(i)&&projs.some(p=>norm(p.name).length>3&&norm(i.notes).includes(norm(p.name))))add('revenue','إيراد عام يشير إلى مشروع','رقم '+i.number+' بمبلغ '+money(i.total)+'؛ راجع هل هو إيراد إضافي أم دفعة من عقد قائم قبل احتسابه مرتين.',{invoiceId:i.id});
  // فحوص إضافية
  if(toNum(i.subtotal)===0&&toNum(i.total)===0)add('empty','فاتورة فارغة بقيمة صفر','رقم '+i.number+'؛ سجل بلا مبلغ، راجعه أو احذفه.',{invoiceId:i.id});
  else if(!invoiceMoneyIssue(i)){const r=toNum(i.vatRate),ex=Math.round(toNum(i.subtotal)*r/100*100),gv=Math.round(toNum(i.vat)*100);if(r>0&&Math.abs(ex-gv)>2)add('vatrate','ضريبة لا تطابق النسبة','رقم '+i.number+': صافي '+money(i.subtotal)+' بنسبة '+r+'٪ تتوقع ضريبة '+money(toNum(i.subtotal)*r/100)+'، والمسجّل '+money(i.vat)+'؛ حدّد الضريبة أو اجعل النسبة صفرًا.',{invoiceId:i.id});}
  if(['subtotal','vat','total'].some(f=>Math.abs(Math.round(toNum(i[f])*100)-toNum(i[f])*100)>1e-6))add('precision','رقم يتجاوز منزلتين عشريتين','رقم '+i.number+': صافي '+i.subtotal+'، ضريبة '+i.vat+'، إجمالي '+i.total+'؛ يجب التقريب للهللة.',{invoiceId:i.id});
 });
 const unlinked=invoices.filter(i=>!i.projectId&&(i.type==='purchase'||i.type==='expense'));
 if(unlinked.length)add('unlinked','فواتير بلا مشروع للمراجعة',unlinked.length+' فاتورة بإجمالي '+money(unlinked.reduce((s,i)=>s+toNum(i.total),0))+' ر.س؛ تأكّد أنها مصروفات عامة لا تخص مشروعًا بعينه.',{});
 for(const [id,rows] of orphanGroups)add('orphan','فواتير مرتبطة بمشروع غير موجود',rows.length+' فاتورة، إجمالي '+money(rows.reduce((s,i)=>s+toNum(i.total),0))+' ر.س. مصروفاتها مدرجة في الرئيسية ضمن غير الموزع حتى تصحيح الربط.',{orphanId:id});
 findDupInvoices().forEach(g=>add('duplicate','فواتير متشابهة تحتاج مراجعة','رقم '+g[0].number+' — '+g.length+' نسخ بمبلغ '+money(g[0].total)+' للنسخة. لا تُحذف تلقائيًا.',{}));
 orders.forEach(o=>{
  const label=o.number||o.supplierName||'شراء بدون رقم';
  if(toNum(o.paid)>toNum(o.total)+.005)add('overpaid','سداد يتجاوز إجمالي الشراء',label+': المسدد '+money(o.paid)+'، الإجمالي '+money(o.total)+'، الفرق '+money(toNum(o.paid)-toNum(o.total))+'. لم يُعدّل المبلغ تلقائيًا.',{purchaseId:o.id});
  if(o.directPurchase&&!journals.some(j=>(j.source==='purchase'&&j.sourceId===o.id)||(o.invoiceId&&j.source==='inv'&&j.sourceId===o.invoiceId)))add('posting','شراء لم يُرحّل محاسبيًا',label+' — '+money(o.total)+' ر.س. راجع قيد أصل الشراء قبل توثيق السداد.',{purchaseId:o.id,accounting:true});
  const opening=toNum(o.paid)-(o.payments||[]).reduce((s,p)=>s+toNum(p.amount),0);
  if(opening>0&&(!o.openingPayment||Math.abs(toNum(o.openingPayment.amount)-opening)>.01))add('payment','سداد سابق يحتاج تاريخًا وحساب دفع',label+' — '+money(opening)+' ر.س. أدخل بيانات المستند دون إضافة دفعة جديدة.',{purchaseId:o.id,payment:true});
 });
 projs.forEach(p=>{
  const approved=p.approvedExpenseReconciliation;
  if(approved&&Number.isFinite(Number(approved.expectedProjectCostGross))){const actual=projPL(p.id).cost,expected=Number(approved.expectedProjectCostGross);if(Math.abs(actual-expected)>.02)add('approvedExpense','مصروفات تغيرت بعد الاعتماد',p.name+': المعتمد على المشروع '+money(expected)+'، المسجل الآن '+money(actual)+' ر.س. راجع الإضافات أو حدّث الاعتماد من المستندات.',{projectId:p.id});}
  const design=p.approvedDesignReconciliation;
  if(design&&Number.isFinite(Number(design.approvedTotalGross))){const actual=toNum(projPL(p.id).byCat.design),expected=Number(design.approvedTotalGross);if(Math.abs(actual-expected)>.02)add('approvedDesign','التصميم يختلف عن الإجمالي المعتمد',p.name+': التصميم المعتمد '+money(expected)+'، المسجل الآن '+money(actual)+' ر.س.',{projectId:p.id});}
  if(toNum(p.siteExpensesTotal)>0&&!p.siteExpensesDate)add('costdate','مصروفات مجمّعة دون تاريخ',p.name+' — '+money(p.siteExpensesTotal)+' ر.س. التقارير السنوية أولية حتى توثيق التاريخ.',{projectId:p.id});
  if(p.status==='done'&&!p.actualEndDate)add('delivery','مشروع مكتمل دون تاريخ تسليم فعلي',p.name,{projectId:p.id});
 });
 (window.opsData?.budgets||[]).forEach(b=>{
  const sum=['materials','labor','equipment','subcontracts','overhead'].reduce((s,k)=>s+toNum(b[k]),0),gap=toNum(b.total)-sum;
  if(Math.abs(gap)>.01)add('budget','ميزانية تحتاج توزيع البنود',(projName(b.projectId)||'مشروع')+': الإجمالي '+money(b.total)+'، البنود '+money(sum)+'، الفرق '+money(gap)+' ر.س.',{budgetId:b.id,projectId:b.projectId});
 });
 const names=new Map();projs.forEach(p=>{const key=norm(p.code||p.name);if(!key)return;if(!names.has(key))names.set(key,[]);names.get(key).push(p);});
 for(const group of names.values())if(group.length>1)add('projectDuplicate','مشاريع متشابهة','راجع السجلات: '+group.map(p=>p.name).join('، ')+' قبل إنشاء مشروع آخر.',{});
 return issues;
};
window.getDataQualitySummary=function(issues=getDataQualityIssues()){
 const groups=[
  {id:'financial',title:'المبالغ والربط والفترات المالية',issues:[]},
  {id:'accounting',title:'الترحيل وتوثيق السداد',issues:[]},
  {id:'project',title:'استكمال بيانات المشاريع',issues:[]}
 ];
 for(const issue of issues){
  const group=['posting','payment'].includes(issue.kind)?groups[1]:['delivery','budget'].includes(issue.kind)?groups[2]:groups[0];
  group.issues.push(issue);
 }
 return {total:issues.length,groups:groups.filter(g=>g.issues.length)};
};
window.renderDataQualityStatus=function(){
 const hero=document.getElementById('hero-profit');if(!hero)return;
 let box=document.getElementById('data-quality-status');
 if(!box){box=document.createElement('button');box.type='button';box.id='data-quality-status';box.style.cssText='width:100%;text-align:right;direction:rtl;background:#fff7ed;border:1px solid #fdba74;border-radius:12px;padding:12px;margin-bottom:12px;color:#9a3412;font:inherit;cursor:pointer;line-height:1.8';box.onclick=()=>openDataQualityReview();hero.before(box);}
 const summary=getDataQualitySummary();box.hidden=!summary.total;
 box.textContent='⚠️ '+summary.total+' ملاحظة للمراجعة: '+summary.groups.map(g=>g.issues.length+' — '+g.title).join('؛ ')+'. اضغط للتفاصيل.';
};
window.openDataQualityReview=function(){
 document.getElementById('data-quality-review')?.remove();
 const overlay=document.createElement('div');overlay.id='data-quality-review';overlay.style.cssText='position:fixed;inset:0;z-index:100250;background:#0f172a99;display:flex;align-items:center;justify-content:center;padding:12px';
 const panel=document.createElement('div');panel.style.cssText='background:white;color:#17324f;border-radius:16px;padding:18px;width:min(800px,100%);max-height:88vh;overflow:auto;direction:rtl;font-family:inherit';
 const heading=document.createElement('h3');heading.textContent='مراجعة البيانات والمستندات';panel.append(heading);
 const note=document.createElement('p');note.textContent='العدد يحسب كل ملاحظة على حدة؛ قد يظهر الشراء الواحد في مراجعة الترحيل وتوثيق السداد معًا. راجع المستند قبل تغيير المبالغ أو التواريخ.';panel.append(note);
 const close=()=>overlay.remove();
 const button=(label,action)=>{const b=document.createElement('button');b.type='button';b.className='h1077-btn';b.style.margin='5px';b.textContent=label;b.onclick=action;return b;};
 panel.append(button('إغلاق',close));
 const summary=getDataQualitySummary();if(!summary.total){const p=document.createElement('p');p.textContent='لم تظهر ملاحظات ضمن الفحوص الحالية.';panel.append(p);}
 summary.groups.forEach(group=>{
 const heading=document.createElement('h4');heading.textContent=group.title+' ('+group.issues.length+')';panel.append(heading);
 if(group.id==='accounting'){
  const purchases=new Set(group.issues.filter(i=>i.purchaseId).map(i=>i.purchaseId));
  const note=document.createElement('p');note.textContent=group.issues.length+' ملاحظة تخص '+purchases.size+' عملية شراء. افتح السجل الحالي لكل شراء لتوثيق السداد أو مراجعة الترحيل.';panel.append(note);
 }
 group.issues.forEach(issue=>{
  const row=document.createElement('article');row.style.cssText='border:1px solid #dbe8f3;border-radius:10px;padding:12px;margin:10px 0;overflow-wrap:anywhere';
  const title=document.createElement('strong');title.textContent=issue.title;
  const detail=document.createElement('p');detail.style.cssText='font-size:13px;line-height:1.8';detail.textContent=issue.detail;row.append(title,detail);
  if(issue.invoiceId)row.append(button('مراجعة الفاتورة',()=>{close();goTab('add');dqFocusAfter(issue.kind,()=>revInv(issue.invoiceId));}));
  if(issue.kind==='duplicate')row.append(button('مقارنة النسخ',()=>{close();openDupCheck();}));
  if(issue.orphanId)row.append(button('تصحيح ربط المجموعة',()=>openOrphanAssignment(issue.orphanId)));
  if(issue.accounting)row.append(button('مراجعة الترحيل',()=>{close();goTab('acc');}));
  if(issue.purchaseId)row.append(button(issue.payment?'توثيق السداد السابق':'مراجعة الشراء',()=>{close();if(issue.payment)openBuyPayment(issue.purchaseId);else dqFocusAfter(issue.kind,()=>opsOpen('purchase',issue.purchaseId));}));
  if(issue.budgetId)row.append(button('توزيع الميزانية',()=>{close();opsOpen('budget',issue.budgetId,issue.projectId);}));
  else if(issue.projectId)row.append(button('مراجعة المشروع',()=>{close();curProjId=issue.projectId;editProj();}));
  panel.append(row);
 });
 });
 overlay.append(panel);document.body.append(overlay);
};
let assigning=false;
window.openOrphanAssignment=function(projectId){
 if(window.HD_ROLE!=='owner')return toast('تصحيح ربط المجموعة متاح للمالك','er');
 const rows=invs.filter(i=>i.projectId===projectId);if(!rows.length)return;
 const panel=document.querySelector('#data-quality-review>div');if(!panel)return;
 panel.replaceChildren();
 const title=document.createElement('h3');title.textContent='تصحيح ربط '+rows.length+' فاتورة';panel.append(title);
 const note=document.createElement('p');note.textContent='اختر المشروع الصحيح حسب المستندات، أو صنّفها كمصروفات عامة. ستُحفظ نسخة استعادة قبل تغيير الربط دون تغيير المبالغ.';panel.append(note);
 const select=document.createElement('select');select.id='orphan-project-choice';select.style.cssText='width:100%;padding:12px;font:inherit';
 [['','— اختر —'],['__general__','بدون مشروع / مصروفات عامة'],...projs.map(p=>[p.id,p.name])].forEach(([value,label])=>{const o=document.createElement('option');o.value=value;o.textContent=label;select.append(o);});panel.append(select);
 const save=document.createElement('button');save.className='h1077-btn';save.style.marginTop='12px';save.textContent='حفظ الربط';
 save.onclick=async()=>{
  if(assigning||!select.value)return;
  const chosen=select.value,target=chosen==='__general__'?'':chosen;
  const current=invs.filter(i=>i.projectId===projectId);
  if(!current.length||target&&!projs.some(p=>p.id===target))return;
  if(current.some(i=>!_canEditInvoice(i,i.date)))return;
  const fingerprint=JSON.stringify(current);
  if(!await confirm2({title:'تأكيد تصحيح الربط',msg:'سيتم تغيير ربط '+current.length+' فاتورة إلى '+esc(target?projName(target):'بدون مشروع')+' دون تغيير مبالغها.',ok:'حفظ الربط'}))return;
  assigning=true;save.disabled=true;const before=invs.slice();
  try{
   await _stInit();if(ST.mode==='memory')throw Error('تعذر ضمان حفظ نسخة استعادة على الجهاز');
   if(!await saveReviewArchive('hd-review-backup:'+Date.now(),JSON.stringify({kind:'projectAssignment',at:new Date().toISOString(),invoices:current})))throw Error('تعذر حفظ نسخة الاستعادة');
   if(JSON.stringify(invs.filter(i=>i.projectId===projectId))!==fingerprint)throw Error('تغيرت المجموعة أثناء المراجعة؛ أعد المحاولة');
   invs=invs.map(i=>i.projectId===projectId?{...i,projectId:target}:i);
   const result=await svDetailed();if(!result?.ok){invs=before;throw Error('تعذر حفظ الربط؛ بقيت الفواتير كما هي');}
   logEvent('تصحيح ربط فواتير',current.length+' فاتورة');renderDB();renderList();openDataQualityReview();toast('تم تصحيح الربط دون تغيير المبالغ','ok');
  }catch(e){toast(e.message,'er');}finally{assigning=false;save.disabled=false;}
 };
 panel.append(save);
 const back=document.createElement('button');back.className='h1077-btn';back.style.margin='10px';back.textContent='رجوع';back.onclick=()=>openDataQualityReview();panel.append(back);
};
window.refreshInvoiceNumberStatus=function(){
 const field=document.getElementById('f-no');if(!field)return;
 let status=document.getElementById('invoice-number-status');
 if(!status){status=document.createElement('div');status.id='invoice-number-status';status.setAttribute('role','status');status.setAttribute('aria-live','polite');status.style.cssText='color:#b91c1c;font-size:12px;line-height:1.7;margin:5px 0';field.after(status);}
 status.replaceChildren();
 const key=normalizeInvoiceNumber(field.value);
 const existing=key&&invs.find(i=>i.id!==editId&&invoiceDuplicateKey(i)===key);if(!existing)return;
 const text=document.createElement('span');text.textContent='الفاتورة مسجلة مسبقًا برقم '+existing.number+'. ';status.append(text);
 const open=document.createElement('button');open.type='button';open.className='h1077-btn';open.textContent='فتح الفاتورة الحالية';open.onclick=()=>{goTab('add');revInv(existing.id);};status.append(open);
};
document.getElementById('f-no')?.addEventListener('input',()=>refreshInvoiceNumberStatus());
document.addEventListener('DOMContentLoaded',()=>renderDataQualityStatus());
})();
