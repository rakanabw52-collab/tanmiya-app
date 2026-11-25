/* Owner-reviewed input VAT: retain the original posting and add one linked adjustment. */
(function(root){
'use strict';
const clone=value=>JSON.parse(JSON.stringify(value));
const entries=()=>typeof journals!=='undefined'&&Array.isArray(journals)?journals:(Array.isArray(root.journals)?root.journals:[]);
const accounts=()=>typeof coa!=='undefined'&&Array.isArray(coa)?coa:(Array.isArray(root.coa)?root.coa:[]);
const cents=value=>{const n=Number(value);return Number.isFinite(n)?Math.round(n*100):NaN;};
const amount=value=>cents(value)/100;
const day=()=>typeof _todayStr==='function'?_todayStr():new Date().toISOString().slice(0,10);
const validDate=value=>typeof value==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(value)&&!Number.isNaN(Date.parse(value+'T00:00:00Z'))&&new Date(value+'T00:00:00Z').toISOString().slice(0,10)===value;
const closed=value=>typeof _isClosedDate==='function'?_isClosedDate(value):typeof root.hdIsPeriodClosed==='function'&&root.hdIsPeriodClosed(value);
const account=(id,type)=>accounts().some(a=>a.id===id&&(!type||a.type===type));
const expenseAccount=invoice=>{
 if(invoice.classificationAccount&&account(invoice.classificationAccount,'expense'))return invoice.classificationAccount;
 return typeof _expAccFor==='function'?_expAccFor(invoice):'';
};
const normalDigits=value=>String(value||'').normalize('NFKC').replace(/[٠-٩]/g,d=>String('٠١٢٣٤٥٦٧٨٩'.indexOf(d))).replace(/[۰-۹]/g,d=>String('۰۱۲۳۴۵۶۷۸۹'.indexOf(d))).replace(/[\s-]/g,'');
const fail=reason=>({ok:false,reason});
const lineSignature=lines=>Array.isArray(lines)&&lines.every(l=>l&&typeof l==='object')?JSON.stringify(lines.map(l=>[String(l.acc),cents(l.debit),cents(l.credit)])):null;
function money(invoice){
 const base=cents(invoice.subtotal??invoice.amount),vat=cents(invoice.vat),total=cents(invoice.total);
 return {base,vat,total,valid:[base,vat,total].every(Number.isFinite)&&base>=0&&vat>=0&&total>0&&vat<=total&&Math.abs(base+vat-total)<=2};
}
function balanced(lines){
 if(!Array.isArray(lines)||!lines.length)return false;
 let debit=0,credit=0;
 for(const line of lines){
  if(!line||typeof line!=='object')return false;
  const d=cents(line.debit),c=cents(line.credit);
  if(!account(line.acc)||!Number.isFinite(d)||!Number.isFinite(c)||d<0||c<0||(d&&c))return false;
  debit+=d;credit+=c;
 }
 return debit>0&&debit===credit;
}
const reversed=journal=>!!journal?.reverses||entries().some(j=>j.reverses===journal?.id);
function baseShape(journal,invoice){
 if(!journal||journal.source!=='inv'||journal.sourceId!==invoice.id||
    (journal.sourceLinkPendingReview&&journal.vatRecoverySourceProtected!==true)||reversed(journal)||!balanced(journal.lines))return null;
 const debit=(journal.lines||[]).filter(l=>cents(l.debit)>0);
 const expenses=debit.filter(l=>account(l.acc,'expense'));
 const tax=debit.filter(l=>l.acc==='1030');
 if(expenses.length!==1||debit.some(l=>l!==expenses[0]&&l.acc!=='1030')||tax.length>1)return null;
 const credits=journal.lines.filter(l=>cents(l.credit)>0);
 if(credits.some(l=>l.acc==='1030'||account(l.acc,'expense')))return null;
 const gross=credits.reduce((sum,l)=>sum+cents(l.credit),0),values=money(invoice);
 if(!values.valid||Math.abs(gross-values.total)>2||Math.abs(gross-values.base-values.vat)>2)return null;
 return {expenseAccount:expenses[0].acc,expense:cents(expenses[0].debit),tax:tax.reduce((sum,l)=>sum+cents(l.debit),0),gross};
}
root.invoiceVATFinancialSignature=function(invoice){
 const values=money(invoice||{});
 if(!values.valid)return null;
 return JSON.stringify({type:invoice.type,date:invoice.date,subtotal:values.base,vat:values.vat,total:values.total,expenseAccount:expenseAccount(invoice)});
};
root.reviewFuelVATCandidate=function(invoice,options={}){
 if(!invoice||invoice.status==='cancelled'||!['purchase','expense'].includes(invoice.type))return fail('السجل ليس شراءً أو مصروفًا فعليًا متاحًا.');
 if(!validDate(invoice.date)||invoice.date>day())return fail('تاريخ الفاتورة غير صالح أو مستقبلي؛ راجع المستند قبل الاسترجاع.');
 if(closed(invoice.date))return fail('فترة الفاتورة مقفلة؛ يلزم اعتماد معالجة الفترة الضريبية قبل الاسترجاع.');
 const values=money(invoice);
 if(!values.valid||(typeof invoiceMoneyIssue==='function'&&invoiceMoneyIssue(invoice)))return fail('راجع تطابق الصافي والضريبة والإجمالي قبل الاسترجاع.');
 if(!(values.vat>0))return fail('لا توجد ضريبة موجبة مسجلة في الفاتورة؛ لا تُحسب ضريبة جديدة من التصنيف.');
 if(!String(invoice.number||'').trim())return fail('رقم الفاتورة مطلوب لإثبات الضريبة.');
 if(!/^\d{15}$/.test(normalDigits(invoice.vendorVAT)))return fail('الرقم الضريبي للمورد يحتاج مراجعة من الفاتورة الأصلية.');
 if(typeof root.analyzePurchaseClassification!=='function')return fail('تحليل وصف المحروقات غير متاح.');
 const analysis=root.analyzePurchaseClassification(invoice);
 const fuelCategory=['fuel','محروقات'].includes(String(invoice.category||'').trim());
 const clear=analysis.isFuel===true&&analysis.confidence==='high'&&!analysis.ambiguous;
 const explicitlyConfirmed=fuelCategory&&(invoice.classificationConfirmed===true||options.ownerConfirmedFuel===true);
 // A legacy fuel label may be confirmed by the owner; an explicit contrary/mixed description may not.
 const contrary=analysis.category!=='fuel'&&(analysis.confidence==='high'||analysis.ambiguous);
 if(!clear&&(!explicitlyConfirmed||contrary))return fail('وصف الوقود غير مؤكد أو يتعارض مع التصنيف؛ راجع بنود الفاتورة أولًا.');
 return {ok:true,vat:values.vat/100,analysis,reason:'ضريبة مدخلات مسجلة ومؤيدة باختيار المالك؛ لا يحدد هذا الاختيار فترة الإقرار أو إرساله.'};
};
root.hasValidVATRecoveryAdjustment=function(invoice,baseJournal){
 const meta=invoice?.vatRecoveryAdjustment;
 if(!meta||invoice.status==='cancelled'||invoice.vatRecoverable!==true||meta.financialSignature!==root.invoiceVATFinancialSignature(invoice)||cents(meta.amount)!==cents(invoice.vat)||!(cents(meta.amount)>0))return false;
 const list=entries(),bases=list.filter(j=>j.source==='inv'&&j.sourceId===invoice.id);
 if(bases.length!==1)return false;
 const base=bases[0];
 if(baseJournal&&baseJournal.id!==base.id)return false;
 if(base.id!==meta.baseJournalId||base.id!==bases[0].id||base.date!==meta.baseDate||lineSignature(base.lines)!==meta.baseLinesSignature)return false;
 const shape=baseShape(base,invoice);
 if(!shape||shape.tax!==0||shape.expenseAccount!==meta.expenseAccount)return false;
 const adjustments=list.filter(j=>j.source==='vatRecoveryAdjustment'&&j.sourceId===invoice.id);
 if(adjustments.length!==1)return false;
 const adjustment=adjustments[0];
 if(adjustment.id!==meta.journalId||adjustment.sourceJournalId!==base.id||reversed(adjustment)||!validDate(adjustment.date)||adjustment.date!==meta.reviewDate||adjustment.date>day())return false;
 if(!balanced(adjustment.lines)||adjustment.lines.length!==2)return false;
 const tax=adjustment.lines.find(l=>l.acc==='1030'),expense=adjustment.lines.find(l=>l.acc===shape.expenseAccount);
 return !!tax&&!!expense&&cents(tax.debit)===cents(meta.amount)&&cents(tax.credit)===0&&cents(expense.credit)===cents(meta.amount)&&cents(expense.debit)===0;
};
root.vatAdjustedBasePostings=function(invoice){
 const base=entries().find(j=>j.id===invoice?.vatRecoveryAdjustment?.baseJournalId);
 return root.hasValidVATRecoveryAdjustment(invoice,base)?clone(base.lines):null;
};
root.planInvoiceVATRecovery=function(invoice,options={}){
 if(invoice?.vatRecoveryAdjustment){
  if(root.hasValidVATRecoveryAdjustment(invoice))return {ok:true,invoice:clone(invoice),adjustment:null,alreadyApplied:true,reason:'تسوية الاسترجاع مسجلة بالفعل؛ لم تنشأ تسوية أخرى.'};
  return fail('تسوية الضريبة السابقة أو بيانات مصدرها تغيرت؛ راجع القيد قبل تكرار الاسترجاع.');
 }
 const reviewed=root.reviewFuelVATCandidate(invoice,options);
 if(!reviewed.ok)return reviewed;
 const today=options.nowDate||day();
 if(!validDate(today)||today!==day())return fail('تاريخ التسوية يجب أن يكون يوم المراجعة الفعلي.');
 if(closed(today))return fail('فترة يوم المراجعة مقفلة؛ لم تنشأ تسوية ضريبية.');
 const list=entries(),bases=list.filter(j=>j.source==='inv'&&j.sourceId===invoice.id);
 if(list.some(j=>j.source==='vatRecoveryAdjustment'&&j.sourceId===invoice.id))return fail('يوجد قيد تسوية ضريبية بلا رابط صالح؛ راجعه قبل المتابعة.');
 const next=clone(invoice),at=Date.now(),beforeRecoverable=invoice.vatRecoverable===true;
 next.vatRecoverable=true;
 if(!bases.length)return {ok:true,invoice:next,adjustment:null,alreadyApplied:beforeRecoverable,reason:'يُثبت الاسترجاع عند ترحيل قيد الشراء لأول مرة.'};
 if(bases.length!==1)return fail('للفاتورة أكثر من قيد أصل؛ يلزم مراجعتها أولًا.');
 const base=bases[0],shape=baseShape(base,invoice),vat=cents(invoice.vat);
 if(!shape)return fail('قيد أصل الفاتورة يحتاج مطابقة؛ لم يُعدّل القيد ولم تنشأ تسوية.');
 if(base.date!==invoice.date)return fail('تاريخ قيد الأصل لا يطابق الفاتورة؛ راجعه قبل التسوية.');
 next.classificationAccount=shape.expenseAccount;
 next.classificationAccountSource=next.classificationAccountSource||{journalId:base.id,account:shape.expenseAccount,originalCategory:invoice.category||'',at};
 if(shape.tax===vat&&shape.expense+vat===shape.gross)return {ok:true,invoice:next,adjustment:null,alreadyApplied:true,reason:'الضريبة مثبتة بالفعل في قيد الأصل؛ تم الحفاظ على تقسيمه.'};
 if(shape.tax!==0)return fail('قيد الأصل يتضمن ضريبة جزئية مختلفة؛ يلزم مراجعته دون إضافة استرجاع آخر.');
 if(shape.expense!==shape.gross||shape.expense<vat||!account('1030','asset'))return fail('لا يمكن مطابقة حساب المصروف وضريبة المدخلات للتسوية.');
 const journalId='vat_adjustment_'+invoice.id;
 if(list.some(j=>j.id===journalId))return fail('معرّف تسوية الضريبة موجود؛ راجع الربط قبل المتابعة.');
 const adjustment={id:journalId,date:today,source:'vatRecoveryAdjustment',sourceId:invoice.id,sourceJournalId:base.id,
  desc:'إثبات ضريبة مدخلات حسب مراجعة المالك — فاتورة '+invoice.number,
  lines:[{acc:'1030',debit:amount(invoice.vat),credit:0},{acc:shape.expenseAccount,debit:0,credit:amount(invoice.vat)}],
  t:at,u:root.HD_USER||'owner-authorized-review'};
 next.vatRecoveryAdjustment={journalId,baseJournalId:base.id,amount:amount(invoice.vat),at,reviewDate:today,baseDate:base.date,
  expenseAccount:shape.expenseAccount,baseLinesSignature:lineSignature(base.lines),
  financialSignature:root.invoiceVATFinancialSignature(next),beforeRecoverable,
  roundingDifferenceCents:shape.gross-cents(invoice.total)};
 return {ok:true,invoice:next,adjustment,alreadyApplied:false,reason:'تسوية مستقلة لضريبة مدخلات مسجلة؛ قيد الشراء الأصلي محفوظ دون تعديل.'};
};
})(typeof window!=='undefined'?window:globalThis);
