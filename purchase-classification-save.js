/* Administrative purchase allocation; monetary values and posted accounts stay intact. */
(function(){
'use strict';
const copy=x=>JSON.parse(JSON.stringify(x));
const active=x=>x&&x.status!=='cancelled';
let saving=false;
window.scanPurchaseCategory=function(data){
 const analysis=analyzePurchaseClassification({notes:data.notes||'',classificationText:data.category||'',items:data.items||[]});
 if(analysis.confidence==='high'&&!analysis.ambiguous)return analysis.category;
 // Supplier names cannot establish fuel; uncertain fuel is left for review.
 const legacy=classify((data.category||'')+' '+(data.notes||''));
 return legacy==='fuel'?'other':legacy;
};
function pinPosting(candidate,old,source){
 if(!old||(old.projectId===candidate.projectId&&old.category===candidate.category))return candidate;
 const posted=journals.filter(j=>j.source===source&&j.sourceId===old.id);
 if(!posted.length)return candidate;
 // A pending source link already protects its journal; don't change its category here.
 if(posted.some(j=>j.sourceLinkPendingReview)){
  if(candidate.category!==old.category)throw Error('ربط قيد هذه الفاتورة معلّق للمراجعة؛ راجع القيد قبل تغيير البند.');
  return candidate;
 }
 if(posted.length!==1||journals.some(j=>j.reverses===posted[0].id))throw Error('للفاتورة قيود متعددة أو عكسية؛ يلزم مراجعتها محاسبيًا أولًا.');
 const j=posted[0],expense=(j.lines||[]).filter(l=>Number(l.debit)>0&&coa.some(a=>a.id===l.acc&&a.type==='expense'));
 if(expense.length!==1)throw Error('قيد هذه الفاتورة موزع على حسابات؛ يلزم مراجعته قبل تغيير التصنيف.');
 const fixed={...candidate,classificationAccount:expense[0].acc,
  classificationAccountSource:old.classificationAccountSource||{journalId:j.id,account:expense[0].acc,originalCategory:old.category||'',at:Date.now()}};
 const financial=source==='purchase'?{...fixed,type:'purchase',subtotal:fixed.amount}:fixed;
 if(j.date!==fixed.date||JSON.stringify(_invPostings(financial))!==JSON.stringify(j.lines))throw Error('القيد الحالي يحتاج مطابقة المبالغ والضريبة قبل تغيير التصنيف؛ بقي كما هو.');
 return fixed;
}
window.preparePurchaseForSave=function(record,existing,options){
 if(record.type==='revenue')return {record,pending:false,changed:false};
 if(existing?.vatRecoveryAdjustment&&!hasValidVATRecoveryAdjustment(record))return {record,pending:true,changed:false,reason:'لهذه الفاتورة تسوية ضريبية؛ راجع التسوية قبل تغيير المبالغ أو الضريبة أو التاريخ.'};
 if(record.projectAllocations?.length&&(!hasInvoiceProjectAllocations(record)||record.projectId))return {record,pending:true,changed:false,reason:'هذه الفاتورة موزعة على مشاريع؛ راجع توزيعها أو ألغِه قبل تغيير المبلغ أو الربط.'};
 const result=enforceFuelGeneral(record,{existing,manualCategory:options?.manualCategory===true});
 if(result.pending)return result;
 try{
  if(!existing){
   const financial={...result.record,type:result.record.type||'purchase',subtotal:result.record.subtotal??result.record.amount};
   if(!financial.vendorVAT&&options?.source==='purchase')financial.vendorVAT=(window.opsData?.suppliers||[]).find(s=>s.id===record.supplierId)?.vat||'';
   if(reviewFuelVATCandidate(financial,{ownerConfirmedFuel:options?.manualCategory===true}).ok){result.record.vatRecoverable=true;result.record.taxDecl=true;result.record.vatRecoveryPolicy='owner-general-fuel';}
  }
  result.record=pinPosting(result.record,existing,options?.source||'inv');
  return result;
 }catch(error){return {record,pending:true,changed:false,reason:error.message};}
};
window.savePurchaseClassificationChange=async function(request){
 if(saving)return {ok:false,error:'جارٍ حفظ مراجعة أخرى.'};
 if(window.HD_ROLE!=='owner')return {ok:false,error:'مراجعة التصنيف متاحة للمالك.'};
 const source=request.source==='purchase'?'purchase':'inv';
 const list=source==='inv'?invs:(window.opsData?.purchaseOrders||[]);
 const current=list.find(x=>x.id===request.id);
 if(!active(current)||current.type==='revenue')return {ok:false,error:'لم يعد سجل الشراء متاحًا.'};
 if(JSON.stringify(current)!==request.expectedSnapshot)return {ok:false,error:'تغير السجل من جهاز أو شاشة أخرى؛ افتح المراجعة من جديد.'};
 const changes=request.changes||{};
 if(Object.keys(changes).some(k=>!['category','projectId','classificationConfirmed'].includes(k)))return {ok:false,error:'هذه المراجعة مخصصة للتصنيف والربط فقط.'};
 if(Object.hasOwn(changes,'category')&&(typeof changes.category!=='string'||!UCAT_BY_ID[changes.category]))return {ok:false,error:'اختر بندًا من القائمة.'};
 if(Object.hasOwn(changes,'projectId')&&changes.projectId!=='')return {ok:false,error:'استخدم تعديل الفاتورة لتغيير المشروع.'};
 if(Object.hasOwn(changes,'classificationConfirmed')&&changes.classificationConfirmed!==true)return {ok:false,error:'يلزم اعتماد التصنيف للمراجعة.'};
 const linked=source==='inv'?(window.opsData?.purchaseOrders||[]).filter(p=>p.invoiceId===current.id&&active(p)):
   (current.invoiceId?invs.filter(i=>i.id===current.invoiceId&&active(i)):[]);
 const rows=[{source,old:copy(current)},...linked.map(old=>({source:source==='inv'?'purchase':'inv',old:copy(old)}))];
 if(rows.length>1&&rows.some(r=>r.source==='inv'&&journals.some(j=>j.source===r.source&&j.sourceId===r.old.id))&&
    rows.some(r=>r.source==='purchase'&&journals.some(j=>j.source===r.source&&j.sourceId===r.old.id)))return {ok:false,error:'للفاتورة والشراء المرتبط قيود أصل منفصلة؛ راجع الترحيل قبل تغيير التصنيف حتى لا يتكرر أو يُحذف قيد.'};
 const at=Date.now();
 try{
  for(const row of rows){
   if(!_canEditInvoice(row.old,row.old.date))throw Error('الفترة أو المشروع مقفل؛ لم يتغير التصنيف.');
   const old=row.old,p=projs.find(p=>p.id===old.projectId);
   const approvedFuelProject=old.fuelProjectException?.projectId===old.projectId&&changes.projectId!=='';
   if(old.projectId&&(changes.projectId===''||(changes.category==='fuel'&&!approvedFuelProject))&&p&&
      ((row.source==='inv'&&Number(p.siteExpensesTotal)>0)||p.status==='study'))throw Error('هذه الفاتورة مرتبطة بمبلغ مشروع مجمّع أو مشروع قيد الدراسة؛ يلزم مراجعة تغطيتها قبل نقلها للعامة حتى لا تتكرر التكلفة.');
   let next={...old,...changes,classificationConfirmed:true};
   const prepared=preparePurchaseForSave(next,old,{manualCategory:true,source:row.source});
   if(prepared.pending)throw Error(prepared.reason);
   next=prepared.record;
   if(old.projectId!==next.projectId&&p&&((row.source==='inv'&&Number(p.siteExpensesTotal)>0)||p.status==='study'))throw Error('يلزم مراجعة المبلغ المجمّع أو حالة الدراسة قبل تغيير توزيع هذه الفاتورة.');
   if(next.projectId!==old.projectId&&old.projectId)next.previousProjectId=old.projectId;
   next.classificationHistory=[...(old.classificationHistory||[]),{at,by:window.HD_USER||'owner',reason:String(request.reason||'مراجعة المشتريات'),before:{category:old.category||'',projectId:old.projectId||''},after:{category:next.category||'',projectId:next.projectId||''}}];
   next.updatedAt=at;row.next=next;
  }
 }catch(error){return {ok:false,error:error.message};}
 saving=true;
 const originalJournal=JSON.stringify(journals);
 const needsInv=rows.some(r=>r.source==='inv'),needsOps=rows.some(r=>r.source==='purchase');
 const beforeValues=[];
 try{
  await _stInit();if(ST.mode==='memory')throw Error('تعذر ضمان الحفظ الدائم على الجهاز.');
  const backup={kind:'purchaseClassification',at,reason:request.reason,records:rows.map(r=>({source:r.source,data:copy(r.old)})),journals:copy(journals.filter(j=>rows.some(r=>r.source===j.source&&r.old.id===j.sourceId)))};
  if(!await saveReviewArchive('hd-purchase-review:'+at,JSON.stringify(backup)))throw Error('تعذر حفظ نسخة الاستعادة؛ لم يتغير التصنيف.');
  for(const row of rows){
   const live=(row.source==='inv'?invs:(window.opsData?.purchaseOrders||[])).find(x=>x.id===row.old.id);
   if(JSON.stringify(live)!==JSON.stringify(row.old))throw Error('تغير السجل أثناء الحفظ؛ أعد المراجعة.');
  }
  if(JSON.stringify(journals)!==originalJournal)throw Error('تغير القيد أثناء المراجعة؛ أعد المحاولة.');
  const nextInvs=invs.map(i=>rows.find(r=>r.source==='inv'&&r.old.id===i.id)?.next||i);
  const nextOps=needsOps?{...window.opsData,purchaseOrders:(window.opsData.purchaseOrders||[]).map(p=>rows.find(r=>r.source==='purchase'&&r.old.id===p.id)?.next||p)}:window.opsData;
  const stateBefore=JSON.stringify([invs,window.opsData,journals]);
  const writes=[];
  if(needsInv)writes.push({key:SK,value:JSON.stringify(nextInvs),before:JSON.stringify(invs)});
  if(needsOps)writes.push({key:window.SOPS,value:JSON.stringify(nextOps),before:JSON.stringify(window.opsData)});
  for(const write of writes){
   if(JSON.stringify([invs,window.opsData,journals])!==stateBefore)throw Error('تغيرت البيانات أثناء الحفظ؛ أعد المراجعة.');
   beforeValues.push(write);
   if(!await saveReviewArchive(write.key,write.value))throw Error('تعذر حفظ المراجعة؛ تمت استعادة البيانات السابقة.');
  }
  if(JSON.stringify([invs,window.opsData,journals])!==stateBefore)throw Error('تغيرت البيانات أثناء الحفظ؛ أعد المراجعة.');
  invs=nextInvs;window.opsData=nextOps;
  try{
   if(typeof cloudPushDebounced==='function')cloudPushDebounced();
   if(typeof logEvent==='function')logEvent('مراجعة تصنيف مشتريات',current.number||current.id);
   if(typeof renderDB==='function')renderDB();
   if(typeof renderList==='function')renderList();
   if(typeof renderBuy1077==='function')renderBuy1077('list');
  }catch(error){console.warn('Purchase review display refresh',error);}
  return {ok:true};
 }catch(error){
  let restored=true;
  // Globals are assigned only after all writes succeed. Preserve any incoming edits.
  for(const write of beforeValues.reverse()){
   const live=write.key===SK?JSON.stringify(invs):JSON.stringify(window.opsData);
   if(!await saveReviewArchive(write.key,live))restored=false;
  }
  return {ok:false,error:error.message+(restored?'':' تعذر تأكيد الاستعادة المحلية؛ نسخة الاستعادة محفوظة. أوقف التعديل وأعد فتح المراجعة.')};
 }finally{saving=false;}
};
})();
