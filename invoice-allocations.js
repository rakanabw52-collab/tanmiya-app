/* Project allocation is a view of one original cost invoice, not another invoice or tax entry. */
(function(root){
'use strict';
function projects(){try{if(typeof projs!=='undefined'&&Array.isArray(projs))return projs;}catch(_){}return Array.isArray(root.projs)?root.projs:[];}
function invoices(){try{if(typeof invs!=='undefined'&&Array.isArray(invs))return invs;}catch(_){}return Array.isArray(root.invs)?root.invs:[];}
function cents(value){
 if(value===null||value===undefined||value===''||typeof value==='boolean')return null;
 const n=Number(value);return Number.isFinite(n)&&n>=0?Math.round((n+Number.EPSILON)*100):null;
}
const storedCents=value=>{const n=cents(value);return n!==null&&Math.abs(Number(value)*100-n)<.000001?n:null;};
const validType=r=>r&&['purchase','expense'].includes(r.type);
root.validInvoiceAllocations=function(record){
 if(!validType(record)||record.projectId||!Array.isArray(record.projectAllocations)||!record.projectAllocations.length)return [];
 const base=cents(record.subtotal),vat=cents(record.vat),total=cents(record.total);
 if([base,vat,total].some(n=>n===null)||total<=0||base+vat!==total)return [];
 const known=new Set(projects().filter(p=>p&&typeof p.id==='string'&&p.id).map(p=>p.id)),seen=new Set(),out=[];
 let sumBase=0,sumVAT=0,sumTotal=0;
 for(const a of record.projectAllocations){
  if(!a||typeof a.projectId!=='string'||!known.has(a.projectId)||seen.has(a.projectId))return [];
  const b=storedCents(a.subtotal),v=storedCents(a.vat),t=storedCents(a.total);
  if([b,v,t].some(n=>n===null)||b+v!==t)return [];
  seen.add(a.projectId);sumBase+=b;sumVAT+=v;sumTotal+=t;
  out.push({projectId:a.projectId,subtotal:b/100,vat:v/100,total:t/100});
 }
 return sumBase===base&&sumVAT===vat&&sumTotal===total?out:[];
};
root.hasInvoiceProjectAllocations=record=>root.validInvoiceAllocations(record).length>0;
root.invoiceProjectRows=function(pid,rows){
 const source=rows===undefined?invoices():rows;if(!Array.isArray(source))return [];
 return source.flatMap(record=>{
  const allocations=root.validInvoiceAllocations(record);
  if(!allocations.length)return record?.projectId===pid?[record]:[];
  const part=allocations.find(a=>a.projectId===pid);if(!part)return [];
  return [{...record,...part,id:record.id,allocationSourceId:record.id,_invoiceProjectAllocation:true}];
 });
};
const money=value=>Number(value||0).toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2});
root.invoiceAllocationLabel=function(record){
 return root.validInvoiceAllocations(record).map(a=>(projects().find(p=>p.id===a.projectId)?.name||a.projectId)+': '+money(a.total)+' ر.س').join(' — ');
};
function build(record,pids,percentages){
 const percentageCents=percentages.map(storedCents);
 if(percentageCents.some(n=>n===null||n<=0)||percentageCents[0]+percentageCents[1]!==10000)return {error:'يجب أن تكون الحصتان موجبتين ومجموعهما 100% تمامًا.'};
 if(!pids[0]||!pids[1]||pids[0]===pids[1])return {error:'اختر مشروعين مختلفين.'};
 const b=cents(record.subtotal),v=cents(record.vat),t=cents(record.total);
 if([b,v,t].some(n=>n===null)||b+v!==t)return {error:'مبالغ الفاتورة غير متطابقة؛ راجع الصافي والضريبة والإجمالي أولًا.'};
 const firstBase=Math.round(b*percentageCents[0]/10000),firstVAT=Math.round(v*percentageCents[0]/10000);
 const allocations=[{projectId:pids[0],subtotal:firstBase/100,vat:firstVAT/100,total:(firstBase+firstVAT)/100},
  {projectId:pids[1],subtotal:(b-firstBase)/100,vat:(v-firstVAT)/100,total:(t-firstBase-firstVAT)/100}];
 if(!root.validInvoiceAllocations({...record,projectId:'',projectAllocations:allocations}).length)return {error:'تعذر اعتماد التوزيع؛ تحقق من المشاريع ومجموع المبالغ.'};
 return {allocations};
}
if(typeof document==='undefined')return;
const el=(tag,text)=>{const node=document.createElement(tag);if(text!==undefined)node.textContent=text;return node;};
root.renderInvoiceAllocationHint=function(record,selectId){
 const select=document.getElementById(selectId);if(!select)return;
 document.getElementById(selectId+'-allocation-hint')?.remove();
 if(!validType(record)||!record.id)return;
 const hint=el('div');hint.id=selectId+'-allocation-hint';hint.style.cssText='font-size:12px;line-height:1.8;padding:8px;background:#eff6ff;border-radius:8px;margin-top:6px';
 const label=root.invoiceAllocationLabel(record),hasRaw=Array.isArray(record.projectAllocations)&&record.projectAllocations.length;
 if(label)hint.append(el('div','فاتورة موزعة: '+label));
 else if(hasRaw)hint.append(el('div','توزيع الفاتورة يحتاج مراجعة؛ لا تعدّل المبالغ قبل تصحيحه أو إلغائه.'));
 const button=el('button',hasRaw?'مراجعة أو إلغاء توزيع الفاتورة':'توزيع الفاتورة على مشروعين');button.type='button';button.className='h1077-btn alt';button.onclick=()=>root.openInvoiceAllocationReview(record.id);hint.append(button);select.after(hint);
};
root.openInvoiceAllocationReview=function(id){
 const record=invoices().find(i=>i.id===id);
 if(!validType(record)||record.status==='cancelled'){if(typeof root.toast==='function')root.toast('اختر فاتورة مشتريات أو مصروف متاحة للتوزيع','er');return;}
 document.getElementById('invoice-allocation-review')?.remove();
 const snapshot=JSON.stringify(record),existing=root.validInvoiceAllocations(record);
 const overlay=el('div');overlay.id='invoice-allocation-review';overlay.setAttribute('role','dialog');overlay.setAttribute('aria-modal','true');overlay.setAttribute('aria-label','توزيع فاتورة على مشروعين');
 overlay.style.cssText='position:fixed;inset:0;z-index:100270;background:#0f172a99;display:flex;align-items:center;justify-content:center;padding:12px;direction:rtl';
 const panel=el('div');panel.style.cssText='width:min(740px,100%);max-height:88vh;overflow:auto;background:#fff;color:#17324f;border-radius:14px;padding:18px;font-family:inherit';
 panel.append(el('h3','توزيع فاتورة '+(record.number||'بدون رقم')+' على مشروعين'),el('p','تظل فاتورة واحدة بمبالغها وتاريخها وضريبتها الأصلية. يظهر لكل مشروع نصيبه فقط، وتبقى أهلية استرجاع الضريبة حسب اختيارك الحالي.'));
 const close=el('button','إغلاق');close.type='button';close.className='h1077-btn alt';close.onclick=()=>overlay.remove();panel.append(close);
 const form=el('div');form.style.cssText='display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin:12px 0';
 const picks=[],shares=[];
 for(let index=0;index<2;index++){
  const box=el('div'),projectLabel=el('label','المشروع '+(index+1)),select=el('select');select.id='allocation-project-'+index;select.style.cssText='width:100%;padding:10px;font:inherit';select.setAttribute('aria-label','المشروع '+(index+1));
  const placeholder=el('option','— اختر المشروع —');placeholder.value='';select.append(placeholder);
  projects().forEach(p=>{const option=el('option',p.name);option.value=p.id;select.append(option);});
  select.value=existing[index]?.projectId||(index===0?record.projectId||'':'');
  const percentLabel=el('label','الحصة %'),percent=el('input');percent.id='allocation-percent-'+index;percent.type='number';percent.min='0.01';percent.max='99.99';percent.step='0.01';percent.style.cssText='width:100%;box-sizing:border-box;padding:10px;font:inherit';percent.value=existing.length===2&&Number(record.total)>0?(Number(existing[index].total)*100/Number(record.total)).toFixed(2):'50';percent.setAttribute('aria-label','الحصة المئوية للمشروع '+(index+1));
  projectLabel.append(select);percentLabel.append(percent);box.append(projectLabel,percentLabel);form.append(box);picks.push(select);shares.push(percent);
 }
 panel.append(form);
 const preview=el('div'),status=el('p');status.id='allocation-status';status.setAttribute('role','status');status.setAttribute('aria-live','polite');panel.append(preview,status);
 const hasRaw=Array.isArray(record.projectAllocations)&&record.projectAllocations.length>0;
 const save=el('button','حفظ التوزيع');save.id='save-invoice-allocation';save.type='button';save.className='h1077-btn';panel.append(save);
 let working=false,currentPlan=null;
 const update=()=>{
  preview.replaceChildren();if(existing.length>2){currentPlan=null;save.disabled=true;preview.append(el('p','التوزيع الحالي يشمل أكثر من مشروعين؛ يمكنك إلغاء التوزيع أولًا ثم إنشاء توزيع جديد.'));return;}
  const plan=build(record,picks.map(s=>s.value),shares.map(s=>s.value));currentPlan=plan.allocations||null;
  save.disabled=working||!currentPlan;
  if(plan.error){preview.append(el('p',plan.error));return;}
  const table=el('table');table.style.cssText='width:100%;border-collapse:collapse;font-size:12px';
  const header=el('tr');['المشروع','الصافي','الضريبة المسجلة','الإجمالي'].forEach(text=>header.append(el('th',text)));table.append(header);
  plan.allocations.forEach(a=>{const row=el('tr');[projects().find(p=>p.id===a.projectId)?.name||a.projectId,money(a.subtotal),money(a.vat),money(a.total)].forEach(text=>{const cell=el('td',text);cell.style.cssText='padding:8px 3px;border-bottom:1px solid #ddd;overflow-wrap:anywhere';row.append(cell);});table.append(row);});
  preview.append(table,el('p','الإجمالي محفوظ: '+money(record.total)+' ر.س — الضريبة: '+money(record.vat)+' ر.س. فروق التقريب موزعة بالهللة دون تكرار الفاتورة.'));
 };
 picks.forEach(s=>s.onchange=update);shares.forEach(s=>s.oninput=update);
 save.onclick=async()=>{
  if(working||!currentPlan)return;
  if(typeof root.saveInvoiceProjectAllocations!=='function'){status.textContent='خدمة حفظ التوزيع غير متاحة حاليًا؛ أعد فتح النسخة المحدثة.';return;}
  working=true;save.disabled=true;picks.forEach(s=>s.disabled=true);shares.forEach(s=>s.disabled=true);status.textContent='جاري حفظ التوزيع...';
  try{
   const result=await root.saveInvoiceProjectAllocations({id,expectedSnapshot:snapshot,allocations:currentPlan});
   if(!result?.ok){status.textContent=result?.error||result?.reason||'تعذر الحفظ؛ لم يُعتمد التوزيع.';return;}
   overlay.remove();if(typeof root.toast==='function')root.toast('حُفظ توزيع الفاتورة دون تغيير مبالغها أو ضريبتها','ok');
  }catch(error){status.textContent=error?.message||'تعذر حفظ التوزيع.';}
  finally{working=false;picks.forEach(s=>s.disabled=false);shares.forEach(s=>s.disabled=false);update();}
 };
 if(hasRaw){
  const cancel=el('button','إلغاء التوزيع وجعل الفاتورة عامة');cancel.id='cancel-invoice-allocation';cancel.type='button';cancel.className='h1077-btn alt';cancel.style.margin='8px';
  cancel.onclick=async()=>{
   if(working)return;
   if(typeof root.saveInvoiceProjectAllocations!=='function'){status.textContent='خدمة حفظ التوزيع غير متاحة حاليًا.';return;}
   if(typeof root.confirm2==='function'&&!await root.confirm2({title:'إلغاء توزيع الفاتورة',msg:'ستعود الفاتورة إلى المشتريات العامة دون تغيير مبلغها أو ضريبتها أو تاريخها. لن تُحمّل على أي مشروع حتى إعادة ربطها.',ok:'إلغاء التوزيع',danger:true}))return;
   working=true;cancel.disabled=true;save.disabled=true;status.textContent='جاري إلغاء التوزيع...';
   try{
    const result=await root.saveInvoiceProjectAllocations({id,expectedSnapshot:snapshot,allocations:[]});
    if(!result?.ok){status.textContent=result?.error||result?.reason||'تعذر إلغاء التوزيع؛ بقي كما هو.';return;}
    overlay.remove();if(typeof root.toast==='function')root.toast('أُلغي التوزيع وأصبحت الفاتورة عامة بمبالغها الأصلية','ok');
   }catch(error){status.textContent=error?.message||'تعذر إلغاء التوزيع.';}
   finally{working=false;cancel.disabled=false;update();}
  };panel.append(cancel);
 }
 if(existing.length>2){picks.forEach(s=>s.disabled=true);shares.forEach(s=>s.disabled=true);}update();
 overlay.append(panel);document.body.append(overlay);close.focus();
};
})(typeof window!=='undefined'?window:globalThis);
