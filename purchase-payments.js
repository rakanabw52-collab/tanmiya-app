/* ربط السداد المثبت للمشتريات المباشرة بالقيود، دون اختراع بيانات سداد تاريخية. */
(function(){
'use strict';
const amount=v=>{const n=typeof toNum==='function'?toNum(v):Number(v||0);return Number.isFinite(n)?n:NaN;};
const cents=v=>Math.round(amount(v)*100);
const validMoney=v=>Number.isFinite(amount(v))&&Math.abs(amount(v)*100-cents(v))<.000001;
const key=(purchaseId,paymentId)=>encodeURIComponent(String(purchaseId))+':'+encodeURIComponent(String(paymentId));
const validDate=d=>{if(!/^\d{4}-\d{2}-\d{2}$/.test(String(d||'')))return false;const t=new Date(d+'T00:00:00Z');return Number.isFinite(+t)&&t.toISOString().slice(0,10)===d;};
const closed=d=>typeof _isClosedDate==='function'&&_isClosedDate(d);
const reversed=j=>journals.some(r=>r.reverses===j.id);
const issue=s=>{if(!_journalSyncIssues.includes(s))_journalSyncIssues.push(s);};
window._purchasePaymentSourceId=key;
window._isPurchaseCashAccount=function(id){
 return typeof coa!=='undefined'&&coa.some(a=>a.id===id&&a.type==='asset'&&!['1020','1030','1040'].includes(String(a.id)));
};
window._purchasePaymentEditIssue=function(purchaseId,paymentId,date){
 const j=journals.find(j=>j.source==='purchase-payment'&&j.sourceId===key(purchaseId,paymentId));
 if(closed(date)||j&&closed(j.date))return 'الفترة المحاسبية للسداد مقفلة؛ يلزم إعادة فتحها أو تسجيل قيد تسوية';
 if(j&&reversed(j))return 'قيد السداد له قيد عكسي؛ يلزم تسجيل تسوية محاسبية بدل إعادة كتابته';
 return '';
};
window._syncPurchasePaymentJournals=function(){
 if(typeof journals==='undefined'||typeof coa==='undefined'||typeof _journalSyncIssues==='undefined')return 0;
 const purchases=(window.opsData?.purchaseOrders||[]).filter(p=>p.directPurchase);
 const expected=new Map(),blockedPurchases=new Set(),blockedKeys=new Set();
 for(const p of purchases){
  if(p.status==='cancelled')continue;
  const label=p.number||p.supplierName||p.id;
  const payments=Array.isArray(p.payments)?p.payments:[];
  const paid=cents(p.paid),total=cents(p.total),sum=payments.reduce((s,pay)=>s+cents(pay?.amount),0);
  if(!Number.isFinite(paid)||!Number.isFinite(total)||!Number.isFinite(sum)||paid<0||paid>total||sum>paid||!validMoney(p.paid)||!validMoney(p.total)||payments.some(pay=>!pay||!validMoney(pay.amount)||cents(pay.amount)<=0)){
   blockedPurchases.add(String(p.id));issue('سداد الشراء '+label+' غير مطابق لإجماليه أو مجموع دفعاته؛ لم تُغيّر قيوده');continue;
  }
  const ids=payments.map(pay=>String(pay.id||''));
  if(ids.some(id=>!id||id==='opening')||new Set(ids).size!==ids.length){
   blockedPurchases.add(String(p.id));issue('دفعات الشراء '+label+' لها معرفات مفقودة أو مكررة؛ يلزم مراجعتها');continue;
  }
  const opening=paid-sum;
  const list=payments.map(pay=>({...pay,id:String(pay.id)}));
  if(opening>0){
   if(p.openingPayment&&cents(p.openingPayment.amount)===opening)list.push({...p.openingPayment,id:'opening'});
   else{
    blockedKeys.add(key(p.id,'opening'));
    issue('الشراء '+label+' لديه سداد سابق '+(opening/100).toFixed(2)+' ر.س يحتاج تاريخًا وحساب دفع موثقين');
   }
  }else if(p.openingPayment&&cents(p.openingPayment.amount)!==0){
   blockedKeys.add(key(p.id,'opening'));issue('توثيق السداد السابق للشراء '+label+' لا يطابق رصيده الحالي');
  }
  const originals=journals.filter(j=>(j.source==='purchase'&&String(j.sourceId)===String(p.id))||(p.invoiceId&&j.source==='inv'&&String(j.sourceId)===String(p.invoiceId)));
  const original=originals.length===1?originals[0]:null;
  // السداد يخفض التزامًا مرحّلًا فقط؛ لا ينشئ قيد شراء ضمنيًا.
  if(!original){
   blockedPurchases.add(String(p.id));
   if(paid>0)issue(originals.length?'الشراء '+label+' له أكثر من قيد أصل؛ يلزم تسوية التكرار قبل ربط السداد':'سداد الشراء '+label+' ينتظر ترحيل قيد فاتورة الشراء الأصلي');continue;
  }
  const liability=(original.lines||[]).filter(l=>l.acc==='2010').reduce((s,l)=>s+cents(l.credit)-cents(l.debit),0);
  if(liability!==total||reversed(original)){
   blockedPurchases.add(String(p.id));issue('قيد أصل الشراء '+label+' غير مطابق أو معكوس؛ يلزم تسويته قبل ربط السداد');continue;
  }
  for(const pay of list){
   const sourceId=key(p.id,pay.id),cash=_isPurchaseCashAccount(pay.cashAccount);
   if(!validDate(pay.date)||!cash||cents(pay.amount)<=0){
    blockedKeys.add(sourceId);issue('دفعة الشراء '+label+' تحتاج تاريخ سداد صحيحًا وحساب نقدية أو بنك صحيح');continue;
   }
   const value=cents(pay.amount)/100;
   const sourceHash=JSON.stringify([String(p.id),pay.id,pay.date,value,pay.cashAccount,total/100]);
   expected.set(sourceId,{id:'purchase-payment:'+sourceId,source:'purchase-payment',sourceId,purchaseId:String(p.id),paymentId:pay.id,
    sourceHash,date:pay.date,desc:'سداد شراء '+label+(pay.id==='opening'?' — توثيق السداد السابق':''),
    lines:[{acc:'2010',debit:value,credit:0},{acc:pay.cashAccount,debit:0,credit:value}]});
  }
 }
 let changed=0;
 const seen=new Set(),next=[];
 for(const j of journals){
  if(j.source!=='purchase-payment'){next.push(j);continue;}
  const purchaseId=String(j.purchaseId||''),target=expected.get(j.sourceId);
  if(seen.has(j.sourceId)){
   issue('قيد سداد مكرر للشراء '+purchaseId+' يحتاج مراجعة؛ لم يُحذف تلقائيًا');next.push(j);continue;
  }
  seen.add(j.sourceId);
  if(reversed(j)){
   issue('قيد السداد '+(j.desc||j.id)+' معكوس؛ لم يُعد ترحيله أو تغييره');next.push(j);continue;
  }
  if(blockedPurchases.has(purchaseId)||blockedKeys.has(j.sourceId)){
   next.push(j);continue;
  }
  if(!target){
   if(closed(j.date)){issue('قيد السداد '+(j.desc||j.id)+' في فترة مقفلة ويحتاج قيد تسوية');next.push(j);}
   else changed++;
   continue;
  }
  const same=j.sourceHash===target.sourceHash&&j.date===target.date&&JSON.stringify(j.lines)===JSON.stringify(target.lines);
  if(same){next.push(j);continue;}
  if(closed(j.date)||closed(target.date)){
   issue('تغير سداد الشراء '+purchaseId+' في فترة مقفلة؛ لم يُعد كتابة قيده');next.push(j);continue;
  }
  next.push({...j,...target,id:j.id,updatedAt:Date.now()});changed++;
 }
 for(const [sourceId,target] of expected){
  if(seen.has(sourceId))continue;
  if(closed(target.date)){issue('دفعة شراء بتاريخ '+target.date+' في فترة مقفلة تحتاج قيد تسوية؛ لم تُرحّل تلقائيًا');continue;}
  next.push({...target,t:Date.now(),u:typeof _hdWho==='function'?_hdWho():''});changed++;
 }
 if(changed){journals=next;try{if(typeof svJRN==='function')svJRN();}catch(e){issue('تعذر حفظ قيود سداد المشتريات: '+e.message);}}
 return changed;
};
})();
