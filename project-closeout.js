/* Project closeout: dated immutable review snapshots and financial edit guards. */
(function(){
'use strict';
const copy=x=>JSON.parse(JSON.stringify(x)),N=x=>toNum(x),E=x=>esc(String(x??'')),M=x=>fmtI(x)+' ر.س';
const PROJECT=['id','name','code','client','status','contractValue','paidAmount','siteExpensesTotal','siteExpensesDate','siteVATRecoverable','siteExpensesVAT','quantity','unit','startDate','endDate','actualEndDate','durationDays','applyApprovedExtensions','retentionPct'];
const RECORD=['id','projectId','type','number','date','status','total','subtotal','amount','value','gross','vat','vatRate','paid','payments','openingPayment','taxDecl','vatRecoverable','vendorVAT','vendor','notes','supplierId','supplierName','invoiceId','directPurchase','category','partyType','subcontractId','subcontractorId','retention','retentionPct','days','dueDate','cashAccount','qty','workType','items'];
const OPS=['purchaseOrders','claims','changeOrders','subcontracts','budgets'];
const registry=new Map(),permit=new Set();let screen=null,busy=false;
const pick=(x,keys)=>Object.fromEntries(keys.filter(k=>x?.[k]!==undefined).map(k=>[k,x[k]]));
function canonical(x){if(Array.isArray(x))return x.map(canonical);if(x&&typeof x==='object')return Object.fromEntries(Object.keys(x).filter(k=>!['updatedAt','updated_at'].includes(k)).sort().map(k=>[k,canonical(x[k])]));return x;}
const same=(a,b)=>JSON.stringify(canonical(a))===JSON.stringify(canonical(b));
const ordered=a=>a.slice().sort((a,b)=>String(a.id).localeCompare(String(b.id)));
function related(rows,id,old=[]){const ids=new Set(old.map(x=>x.id));return ordered(rows.filter(x=>x.projectId===id||ids.has(x.id)).map(x=>pick(x,RECORD)));}
function inputs(p,baseline){
 const id=p.id,od=window.opsData||{},ops={};
 OPS.forEach(k=>ops[k]=related(od[k]||[],id,baseline?.ops?.[k]));
 const supplierIds=new Set([...ops.purchaseOrders.map(x=>x.supplierId),...(baseline?.suppliers||[]).map(x=>x.id)].filter(Boolean));
 return {project:pick(p,PROJECT),invoices:related(invs,id,baseline?.invoices),ops,progress:related(progress,id,baseline?.progress),suppliers:ordered((od.suppliers||[]).filter(x=>supplierIds.has(x.id)).map(x=>pick(x,['id','name','vat','phone','email','category','active','notes'])))};
}
function currentReport(p){return p?.closeout?.reports?.find(x=>x.id===p.closeout.currentId);}
function remember(){projs.forEach(p=>{if(permit.has(p.id))return;if(p.closeout?.status==='closed'&&!registry.has(p.id)){const report=currentReport(p);if(report?.inputs)registry.set(p.id,{inputs:copy(report.inputs),meta:copy(p.closeout)});}});}
function restoreRows(rows,old,id){const ids=new Set(old.map(x=>x.id)),byId=new Map(rows.map(x=>[x.id,x]));return [...rows.filter(x=>x.projectId!==id&&!ids.has(x.id)),...old.map(x=>({...byId.get(x.id),...copy(x)}))];}
function restoreClosed(id,r,kind){
 let p=projs.find(x=>x.id===id);
 if(kind==='project'){
  if(!p){p={...copy(r.inputs.project),closeout:copy(r.meta)};projs.push(p);}else{PROJECT.filter(k=>k!=='id').forEach(k=>{delete p[k];});Object.assign(p,copy(r.inputs.project));p.closeout=copy(r.meta);}
 }
 if(kind==='invoice')invs=restoreRows(invs,r.inputs.invoices,id);
 if(kind==='progress')progress=restoreRows(progress,r.inputs.progress,id);
 if(kind==='ops'){
  OPS.forEach(k=>window.opsData[k]=restoreRows(window.opsData[k]||[],r.inputs.ops[k]||[],id));
  (r.inputs.suppliers||[]).forEach(saved=>{const s=(window.opsData.suppliers||[]).find(x=>x.id===saved.id);if(s)Object.assign(s,copy(saved));else(window.opsData.suppliers||(window.opsData.suppliers=[])).push(copy(saved));});
 }
}
function guard(kind){
 remember();let blocked=false;
 for(const [id,r] of registry){
  const lifecycleWrite=permit.has(id)&&kind==='project';
  const p=projs.find(x=>x.id===id),now=p?inputs(p,r.inputs):null;
  const changed=kind==='project'?(!p||!same(now.project,r.inputs.project)||(!lifecycleWrite&&!same(p.closeout,r.meta))):kind==='invoice'?!same(now?.invoices,r.inputs.invoices):kind==='progress'?!same(now?.progress,r.inputs.progress):!same(now?.ops,r.inputs.ops)||!same(now?.suppliers,r.inputs.suppliers);
  if(changed){restoreClosed(id,r,kind);blocked=true;}
 }
 if(blocked){toast('المشروع مقفل ماليًا؛ أعد فتحه مع تسجيل السبب قبل التعديل','er');return false;}return true;
}
window.projectCloseAllows=function(id){remember();if(!id||!registry.has(id))return true;toast('المشروع مقفل ماليًا؛ أعد فتحه من شاشة الإقفال النهائي','er');return false;};
function payable(x){return x.status==='paid'?0:Math.max(0,N(x.total)-N(x.paid));}
function reportFor(p){
 const pl=projPL(p.id),od=window.opsData||{},bills=invs.filter(i=>i.projectId===p.id&&i.status!=='cancelled'),orders=(od.purchaseOrders||[]).filter(x=>x.projectId===p.id&&x.status!=='cancelled'),claims=(od.claims||[]).filter(x=>x.projectId===p.id&&x.partyType==='subcontractor'&&x.status!=='cancelled');
 const unlinked=o=>!(o.invoiceId&&invs.some(i=>i.id===o.invoiceId&&i.status!=='cancelled'));
 const tax=projectRecoverableVAT(p.id);
 let supplierDue=orders.filter(unlinked).reduce((s,x)=>s+payable(x),0),unknownBills=0;
 bills.filter(i=>i.type==='purchase').forEach(i=>{const linked=orders.find(o=>o.invoiceId===i.id);if(linked)supplierDue+=payable(linked);else if(i.status==='paid'||i.paid!==undefined)supplierDue+=payable(i);else unknownBills++;});
 const subDue=claims.filter(x=>x.status!=='draft').reduce((s,x)=>s+payable(x),0);
 const netCost=Math.max(0,pl.cost-tax),qty=N(p.quantity),profit=pl.contract-netCost;
 const blockers=[];
 if((pl.siteTotal>0&&p.siteVATRecoverable===undefined)||bills.some(i=>(i.type==='purchase'||i.type==='expense')&&!(pl.siteTotal>0)&&i.vatRecoverable===undefined)||orders.some(o=>unlinked(o)&&o.vatRecoverable===undefined)||claims.some(c=>c.vatRecoverable===undefined))blockers.push('حدّد استرجاع الضريبة: نعم أو لا لكل مصروف محتسب قبل الإقفال.');
 if(p.status!=='done')blockers.push('يجب أن تكون حالة المشروع «منجز».');
 if(!(qty>0))blockers.push('أدخل طول / كمية المشروع قبل الاعتماد.');
 if(pl.outstanding>0.005)blockers.push('يوجد رصيد على العميل؛ يلزم تسويته حتى لو كان أقل من ريال.');
 if(supplierDue>0.005||subDue>0.005)blockers.push('توجد مستحقات مسجلة غير مسددة للموردين أو مقاولي الباطن.');
 if(claims.some(x=>x.status==='draft'))blockers.push('يوجد مستخلص باطن مسودة يحتاج مراجعة واعتمادًا أو إلغاءً.');
 return {id:uid('close'),projectId:p.id,name:p.name,code:p.code||'',client:p.client||'',status:p.status,createdAt:Date.now(),by:window.HD_USER||'المالك',build:curBuild(),contractNet:pl.contract,contractVAT:pl.contractGross-pl.contract,contractGross:pl.contractGross,costGross:pl.cost,recoverableVAT:tax,costNet:netCost,profitBeforeTaxCredit:pl.contract-pl.cost,profit,margin:pl.contract>0?profit/pl.contract*100:0,paid:pl.paid,outstanding:pl.outstanding,supplierDue,subDue,quantity:qty,unit:p.unit||'م.ط',costPerUnit:qty>0?netCost/qty:null,pricePerUnit:qty>0?pl.contract/qty:null,manualTaxUnknown:pl.siteTotal>0&&p.siteVATRecoverable===undefined,unknownBills,blockers,inputs:copy(inputs(p))};
}
window.projectCloseoutSnapshot=id=>{const p=projs.find(x=>x.id===id);return p?copy(reportFor(p)):null;};
function dateText(t){return new Date(t).toLocaleString('ar-SA-u-ca-gregory',{timeZone:'Asia/Riyadh',dateStyle:'medium',timeStyle:'short'});}
const row=(label,value)=>'<div class="pc-row"><span>'+E(label)+'</span><strong class="num">'+value+'</strong></div>';
function body(r,approved){
 return '<article class="pc-report"><div class="pc-report-head"><h2>الإقفال النهائي للمشروع</h2><strong>'+E(r.name)+'</strong><p>'+E(approved?'كشف معتمد محفوظ':'كشف مراجعة — غير معتمد')+' • '+E(dateText(r.createdAt))+'</p>'+(approved?'<small>اعتمد بواسطة: '+E(r.by)+' • '+E(r.build)+'</small>':'')+'</div><div class="pc-grid"><section><h3>تفصيل الربح والضريبة</h3>'+row('العقد بدون الضريبة',M(r.contractNet))+row('ضريبة العقد',M(r.contractVAT))+row('العقد شامل الضريبة',M(r.contractGross))+row('المصروفات قبل استبعاد ضريبتها',M(r.costGross))+row('ضريبة المشتريات المختارة للاسترجاع',M(r.recoverableVAT))+row('المصروفات بعد استبعاد الضريبة',M(r.costNet))+row('الربح قبل استبعاد ضريبة المشتريات',M(r.profitBeforeTaxCredit))+row('صافي الربح بعد استبعادها',M(r.profit))+row('هامش الربح',r.margin.toFixed(1)+'%')+'<p class="pc-note">الضريبة مستبعدة حسب اختيارك «نعم»؛ أهلية الخصم تحتاج مراجعة الفواتير ولا تعني استلام المبلغ من الهيئة.'+(r.manualTaxUnknown?' المصروفات اليدوية المجمعة باقية كما سُجّلت دون افتراض ضريبتها.':'')+'</p></section><section><h3>التحصيل والمستحقات</h3>'+row('المحصّل شامل الضريبة',M(r.paid))+row('المتبقي على العميل',M(r.outstanding))+row('مستحقات الموردين المسجلة',M(r.supplierDue))+row('مستحقات الباطن المسجلة',M(r.subDue))+(r.unknownBills?'<p class="pc-note">يوجد '+r.unknownBills+' فاتورة شراء دون حالة سداد مفصّلة؛ يجب مراجعتها ضمن تأكيد تسوية الموردين.</p>':'')+'<h3>الطول وتكلفة الوحدة</h3>'+row('طول / كمية المشروع',E(r.quantity.toLocaleString('en-US',{maximumFractionDigits:3}))+' '+E(r.unit))+row('تكلفة الوحدة بعد استبعاد الضريبة المؤهلة',r.costPerUnit===null?'أدخل الكمية':M(r.costPerUnit)+' / '+E(r.unit))+row('سعر الوحدة بدون الضريبة',r.pricePerUnit===null?'أدخل الكمية':M(r.pricePerUnit)+' / '+E(r.unit))+'</section></div>'+(approved?'<p class="pc-note">هذا الكشف محفوظ بتاريخ الاعتماد. إعادة فتح المشروع لا تغيّر هذه النسخة.</p>':'')+'</article>';
}
function vatChoices(p,readonly){
 const od=window.opsData||{},rows=[];
 invs.filter(i=>i.projectId===p.id&&i.status!=='cancelled'&&(i.type==='purchase'||i.type==='expense')).forEach(i=>rows.push({source:'invoice',record:i,label:'فاتورة مصروف / شراء'}));
 (od.purchaseOrders||[]).filter(o=>o.projectId===p.id&&o.status!=='cancelled'&&!(o.invoiceId&&invs.some(i=>i.id===o.invoiceId&&i.status!=='cancelled'))).forEach(o=>rows.push({source:'purchaseOrders',record:o,label:'شراء'}));
 (od.claims||[]).filter(c=>c.projectId===p.id&&c.partyType==='subcontractor'&&c.status!=='cancelled').forEach(c=>rows.push({source:'claims',record:c,label:'مستخلص باطن'}));
 if(!rows.length)return '';
 return '<section class="pc-checks"><h3>استرجاع ضريبة مصروفات المشروع — اختيارك يحدد الحساب</h3><div style="overflow:auto"><table style="width:100%;min-width:450px;text-align:right;font-size:12px;border-collapse:collapse"><thead><tr><th>المصدر / الرقم</th><th>المبلغ</th><th>الضريبة</th><th>استرجاع الضريبة</th></tr></thead><tbody>'+rows.map(({source,record:r,label})=>'<tr><td style="padding:9px">'+E(label)+' — '+E(r.number||r.id)+(source==='invoice'?'<br><button class="btn btn-o btn-sm" data-pc-review-id="'+E(r.id)+'">مراجعة المرفق والضريبة</button>':'')+'</td><td>'+M(r.total)+'</td><td>'+M(r.vat)+'</td><td><select data-pc-vat="'+source+'" data-pc-vat-id="'+E(r.id)+'" '+(readonly?'disabled':'')+'><option value="">غير محدد</option><option value="yes" '+(r.vatRecoverable===true?'selected':'')+'>نعم</option><option value="no" '+(r.vatRecoverable===false?'selected':'')+'>لا</option></select></td></tr>').join('')+'</tbody></table></div><p class="pc-note">تغيير الاختيار يحفظه ويعيد حساب الكشف. ضريبة المصروفات المجمعة اليدوية تُحدد من تعديل المشروع.</p></section>';
}
window.setCloseoutVATChoice=async function(source,id,value){
 if(busy||!screen||screen.approved||!['invoice','purchaseOrders','claims'].includes(source)||!['yes','no'].includes(value))return false;
 const list=source==='invoice'?invs:(window.opsData?.[source]||[]),record=list.find(x=>x.id===id&&x.projectId===screen.id);if(!record||!projectCloseAllows(record.projectId))return false;
 if(_isClosedDate(record.date)){toast('الفترة مقفلة؛ لا يمكن تغيير اختيار الضريبة','er');return false;}
 const previous=copy(record),i=list.indexOf(record);list[i]={...record,vatRecoverable:value==='yes'};
 const result=source==='invoice'?await svDetailed():await svOps(false);
 if(!result?.ok){list[i]=previous;toast('لم يُحفظ اختيار الضريبة','er');return false;}
 _syncInvJournals();logEvent('اختيار استرجاع ضريبة مصروف',source+' — '+id+' — '+value);renderDB();openProjectCloseout(screen.id);return true;
};
function owner(){return ['owner','admin','manager'].includes(window.HD_ROLE);}
function host(){let el=document.getElementById('project-closeout-modal');if(el)return el;el=document.createElement('div');el.id='project-closeout-modal';el.className='pc-modal';el.innerHTML='<div class="pc-sheet"><header class="pc-modal-head"><strong>الإقفال النهائي للمشروع</strong><button type="button" data-pc-action="close">✕</button></header><div id="project-closeout-content"></div></div>';el.addEventListener('click',e=>{if(e.target===el){el.classList.remove('show');return;}const review=e.target.closest('[data-pc-review-id]');if(review){if(typeof openInvoiceVATReview==='function')openInvoiceVATReview(review.dataset.pcReviewId);return;}const b=e.target.closest('[data-pc-action]');if(!b)return;const a=b.dataset.pcAction;if(a==='close')el.classList.remove('show');if(a==='approve')window.approveProjectCloseout();if(a==='reopen')window.reopenProjectCloseout();if(a==='print')window.printProjectCloseout();});el.addEventListener('change',e=>{const select=e.target.closest('[data-pc-vat]');if(select)window.setCloseoutVATChoice(select.dataset.pcVat,select.dataset.pcVatId,select.value);});document.body.appendChild(el);return el;}
window.openProjectCloseout=function(id,reportId){
 remember();const p=projs.find(x=>x.id===id);if(!p)return;
 const saved=reportId?p.closeout?.reports?.find(r=>r.id===reportId):p.closeout?.status==='closed'?currentReport(p):null;
 const report=saved||reportFor(p);screen={id,report:copy(report),approved:!!saved};
 let h=body(report,!!saved);if(!saved)h+=vatChoices(p,false);
 if(!owner())h+='<p class="pc-note">اعتماد الإقفال وإعادة الفتح متاحان للمالك / المدير.</p>';
 if(!saved){h+='<section class="pc-checks"><h3>المراجعة قبل الاعتماد</h3>'+['راجعت قيمة العقد والضريبة من أصل العقد','راجعت المصروفات وفواتير الضريبة وأهلية الخصم','أؤكد التحصيل الكامل من العميل','راجعت تسوية الموردين والباطن، بما فيها المشتريات بلا سجل سداد مفصّل'].map((label,i)=>'<label><input type="checkbox" data-close-check="'+i+'"> '+label+'</label>').join('')+'</section>';if(report.blockers.length)h+='<div class="pc-blockers">'+report.blockers.map(x=>'<div>• '+E(x)+'</div>').join('')+'</div>';}
 h+='<div class="pc-actions"><button class="btn btn-o" data-pc-action="print">طباعة كشف المراجعة</button>';
 if(!saved)h+='<button class="btn btn-p" data-pc-action="approve" '+(!owner()||report.blockers.length?'disabled':'')+'>اعتماد وإقفال المشروع</button>';
 if(p.closeout?.status==='closed'&&saved?.id===p.closeout.currentId&&owner())h+='<button class="btn btn-o" data-pc-action="reopen">إعادة فتح المشروع</button>';
 h+='</div>';
 if(p.closeout?.status==='closed'&&saved?.id===p.closeout.currentId&&owner())h+='<label class="pc-reason">سبب إعادة الفتح<input id="project-closeout-reason" type="text" maxlength="1000" placeholder="اكتب سبب التعديل المطلوب"></label>';
 if(p.closeout?.reports?.length){h+='<details class="pc-history"><summary>كشوف الإقفال السابقة ('+p.closeout.reports.length+')</summary>'+p.closeout.reports.map((r,i)=>'<button class="btn btn-o btn-sm" data-pc-history="'+i+'">'+'كشف '+(i+1)+' — '+E(dateText(r.createdAt))+'</button>').join('')+'</details>';}
 if(p.closeout?.events?.length)h+='<details class="pc-history"><summary>سجل الاعتماد وإعادة الفتح</summary>'+p.closeout.events.map(e=>'<p>'+E(dateText(e.at))+' — '+E(e.action)+(e.reason?' — '+E(e.reason):'')+' — '+E(e.by)+'</p>').join('')+'</details>';
 const modal=host();modal.querySelector('#project-closeout-content').innerHTML=h;
 modal.querySelectorAll('[data-pc-history]').forEach(b=>b.onclick=()=>openProjectCloseout(id,p.closeout.reports[Number(b.dataset.pcHistory)].id));modal.classList.add('show');
};
window.approveProjectCloseout=async function(){
 if(busy||!screen||screen.approved||!owner())return false;
 const p=projs.find(p=>p.id===screen.id);if(!p||p.closeout?.status==='closed')return false;
 const checks=[...host().querySelectorAll('[data-close-check]')];if(checks.length!==4||checks.some(c=>!c.checked)){toast('راجع البنود الأربعة وحدّد تأكيد المراجعة قبل الاعتماد','er');return false;}
 const fresh=reportFor(p);if(!same(fresh.inputs,screen.report.inputs)){toast('تغيّرت بيانات المشروع؛ افتح كشفًا جديدًا وراجعه قبل الاعتماد','er');return false;}
 if(fresh.blockers.length){toast(fresh.blockers[0],'er');return false;}
 const previous=p.closeout?copy(p.closeout):undefined;busy=true;permit.add(p.id);
 fresh.reviewConfirmed=true;p.closeout={status:'closed',currentId:fresh.id,reports:[...(previous?.reports||[]),fresh],events:[...(previous?.events||[]),{action:'اعتماد وإقفال',at:fresh.createdAt,by:fresh.by,reportId:fresh.id}]};
 registry.set(p.id,{inputs:copy(fresh.inputs),meta:copy(p.closeout)});
 try{const result=await svPDetailed();if(!result?.ok)throw Error(result?.err||'فشل حفظ الإقفال');registry.delete(p.id);remember();logEvent('إقفال نهائي للمشروع',p.name);openProjectCloseout(p.id);showProj(p.id);toast('تم اعتماد الإقفال وحفظ الكشف المؤرّخ','ok');return true;}
 catch(e){registry.delete(p.id);if(previous)p.closeout=previous;else delete p.closeout;toast('لم يُعتمد الإقفال: '+e.message,'er');return false;}finally{permit.delete(p.id);busy=false;}
};
window.reopenProjectCloseout=async function(){
 if(busy||!screen||!owner())return false;const p=projs.find(p=>p.id===screen.id);if(p?.closeout?.status!=='closed')return false;
 const reason=(document.getElementById('project-closeout-reason')?.value||'').trim();if(!reason){toast('اكتب سبب إعادة الفتح','er');return false;}
 const previous=copy(p.closeout);busy=true;permit.add(p.id);p.closeout={...p.closeout,status:'open',events:[...(p.closeout.events||[]),{action:'إعادة فتح',reason,at:Date.now(),by:window.HD_USER||'المالك',reportId:p.closeout.currentId}]};
 try{const result=await svPDetailed();if(!result?.ok)throw Error(result?.err||'فشل الحفظ');registry.delete(p.id);logEvent('إعادة فتح مشروع مقفل',p.name+' — '+reason);openProjectCloseout(p.id);showProj(p.id);toast('أُعيد فتح المشروع؛ الكشف السابق محفوظ','ok');return true;}
 catch(e){p.closeout=previous;toast('لم تتم إعادة الفتح: '+e.message,'er');return false;}finally{permit.delete(p.id);busy=false;}
};
window.printProjectCloseout=function(){if(!screen)return;const w=window.open('','_blank');if(!w){toast('اسمح بالنوافذ المنبثقة للطباعة','er');return;}const styles=document.getElementById('project-closeout-style').textContent;w.document.write('<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><title>إقفال المشروع — '+E(screen.report.name)+'</title><style>'+styles+'body{font-family:Arial,sans-serif;padding:20px;background:#fff}@page{size:A4;margin:12mm}.pc-report-head{break-inside:avoid}.pc-grid section{break-inside:avoid}</style></head><body>'+body(screen.report,screen.approved)+'</body></html>');w.document.close();w.focus();w.print();};
// Guards cover normal, quick, bulk and operating persistence paths.
[['sv','invoice',false],['svDetailed','invoice',true],['svP','project',false],['svPDetailed','project',true],['svPR','progress',false],['svOps','ops',true]].forEach(([name,kind,detailed])=>{const original=window[name];if(typeof original!=='function')return;window[name]=async function(...args){if(!guard(kind))return detailed?{ok:false,err:'المشروع مقفل ماليًا'}:false;return original.apply(this,args);};});
const render=window.renderDB;window.renderDB=function(...args){remember();return render.apply(this,args);};
const show=window.showProj;window.showProj=function(...args){remember();return show.apply(this,args);};
const style=document.createElement('style');style.id='project-closeout-style';style.textContent='.pc-modal{display:none;position:fixed;inset:0;background:rgba(15,23,42,.55);z-index:11000;padding:20px;overflow:auto;direction:rtl}.pc-modal.show{display:flex;align-items:flex-start;justify-content:center}.pc-sheet{width:min(100%,1050px);background:#f8fbff;border-radius:16px;padding:20px;box-sizing:border-box}.pc-modal-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:14px}.pc-modal-head button{border:0;background:#e2e8f0;border-radius:6px;padding:8px;cursor:pointer}.pc-report{color:#183b63;direction:rtl}.pc-report-head{background:linear-gradient(110deg,#3476ad,#244c77);padding:18px;border-radius:12px;color:white}.pc-report-head h2{margin:0 0 6px;font-size:22px}.pc-report-head p{font-size:12px;margin:6px 0}.pc-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:16px}.pc-grid section,.pc-checks{border:1px solid #dbe5ef;background:white;border-radius:12px;padding:16px;min-width:0}.pc-grid h3,.pc-checks h3{margin:0 0 12px;font-size:15px}.pc-row{display:flex;align-items:center;justify-content:space-between;gap:12px;border-bottom:1px dashed #dce5ef;padding:9px 0;font-size:12px}.pc-row strong{white-space:nowrap}.pc-note{font-size:11px;line-height:1.7;padding:10px;background:#edf7ff;border-radius:8px}.pc-checks{margin-top:16px}.pc-checks label{display:block;font-size:13px;margin:10px 0}.pc-actions{display:flex;gap:10px;flex-wrap:wrap;margin:16px 0}.pc-actions button[disabled]{opacity:.5;cursor:not-allowed}.pc-reason{display:block;font-size:13px}.pc-reason input{display:block;width:100%;box-sizing:border-box;padding:10px;border:1px solid #b5c9dc;border-radius:8px;margin-top:7px;font:inherit}.pc-blockers{background:#fff3d4;border:1px solid #f7cf75;border-radius:9px;padding:12px;font-size:12px;margin-top:12px;line-height:1.8}.pc-history{margin-top:12px;font-size:12px}.pc-history summary{cursor:pointer;font-weight:800}.pc-history button{margin:8px 4px}@media(max-width:650px){.pc-modal{padding:8px}.pc-sheet{padding:12px}.pc-grid{grid-template-columns:1fr}.pc-row{font-size:11.5px}.pc-report-head h2{font-size:19px}}';document.head.appendChild(style);
window.addEventListener('invoice-vat-reviewed',event=>{if(screen&&!screen.approved&&screen.id===event.detail?.projectId&&document.getElementById('project-closeout-modal')?.classList.contains('show'))openProjectCloseout(screen.id);});
remember();
})();
