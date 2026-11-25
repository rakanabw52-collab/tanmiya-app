/* Save an administrative allocation without duplicating or rewriting its source invoice. */
(function(){
'use strict';
let saving=false;
window.saveInvoiceProjectAllocations=async function({id,expectedSnapshot,allocations}){
 if(saving)return {ok:false,error:'جارٍ حفظ توزيع آخر.'};
 if(window.HD_ROLE!=='owner')return {ok:false,error:'توزيع الفاتورة متاح للمالك.'};
 const current=invs.find(i=>i.id===id);
 if(!current||current.status==='cancelled'||!['purchase','expense'].includes(current.type))return {ok:false,error:'فاتورة الشراء غير متاحة.'};
 if(JSON.stringify(current)!==expectedSnapshot)return {ok:false,error:'تغيرت الفاتورة؛ افتح التوزيع من جديد.'};
 if(!Array.isArray(allocations)||!_canEditInvoice(current,current.date))return {ok:false,error:'تعذر تعديل الفاتورة أو فترتها مقفلة.'};
 const next={...current,projectId:'',projectAllocations:allocations.map(a=>({...a}))};
 if(allocations.length&&!hasInvoiceProjectAllocations(next))return {ok:false,error:'تحقق من المشاريع ومطابقة مجموع الصافي والضريبة والإجمالي لأصل الفاتورة.'};
 const scope=[current.projectId,...validInvoiceAllocations(current).map(a=>a.projectId),...allocations.map(a=>a.projectId)].filter(Boolean);
 for(const pid of scope){
  const p=projs.find(p=>p.id===pid);
  if(!p||p.status==='study'||Number(p.siteExpensesTotal)>0)return {ok:false,error:'المشروع قيد الدراسة أو يستخدم مصروفات مجمّعة؛ راجع تغطية الفاتورة قبل توزيعها.'};
  if(typeof projectCloseAllows==='function'&&!projectCloseAllows(pid))return {ok:false,error:'المشروع مقفل ماليًا.'};
 }
 const at=Date.now();next.updatedAt=at;
 next.projectAllocationHistory=[...(current.projectAllocationHistory||[]),{at,by:window.HD_USER||'owner',before:{projectId:current.projectId||'',allocations:current.projectAllocations||[]},after:{projectId:'',allocations:next.projectAllocations}}];
 saving=true;let wrote=false;
 try{
  await _stInit();if(ST.mode==='memory')throw Error('تعذر الحفظ الدائم على الجهاز.');
  if(!await saveReviewArchive('hd-invoice-allocation:'+at,JSON.stringify({at,invoice:current,journals:journals.filter(j=>j.source==='inv'&&j.sourceId===id)})))throw Error('تعذر حفظ نسخة الاستعادة.');
  if(JSON.stringify(invs.find(i=>i.id===id))!==expectedSnapshot)throw Error('تغيرت الفاتورة أثناء الحفظ؛ أعد المراجعة.');
  const state=JSON.stringify([invs,projs,journals]),nextInvoices=invs.map(i=>i.id===id?next:i);
  wrote=true;
  if(!await saveReviewArchive(SK,JSON.stringify(nextInvoices)))throw Error('تعذر حفظ التوزيع.');
  if(JSON.stringify([invs,projs,journals])!==state)throw Error('تغيرت البيانات أثناء الحفظ؛ أعد المراجعة.');
  invs=nextInvoices;
  try{cloudPushDebounced();logEvent('توزيع فاتورة على مشاريع',current.number||id);renderDB();renderList();renderProjList();}catch(error){console.warn(error);}
  return {ok:true};
 }catch(error){
  let restored=true;if(wrote)restored=await saveReviewArchive(SK,JSON.stringify(invs));
  return {ok:false,error:error.message+(restored?'':' تعذر تأكيد الاستعادة المحلية؛ نسخة الاستعادة محفوظة.')};
 }finally{saving=false;}
};
})();
