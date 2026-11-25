/* Conservative purchase suggestions. Historical categories are changed only by explicit review. */
(function(root){
'use strict';
const fallback=[['infra','مواد البنية التحتية'],['equipment','إيجار ومعدات'],['wages','أجور ورواتب'],['transport','نقل وترحيل'],['fuel','محروقات'],['housing','إيجار سكن'],['food','إعاشة وطعام'],['safety','أمن وسلامة'],['design','تصميم وهندسة'],['comms','اتصالات'],['services','خدمات مهنية'],['banking','مصاريف بنكية'],['loans','سلف وعهد'],['site','مصاريف موقع'],['subcontractor','مقاولو الباطن'],['other','أخرى']];
const categories=()=>typeof UCATS!=='undefined'?UCATS:fallback.map(([id,name])=>({id,name}));
const normalize=v=>String(v||'').normalize('NFKC').toLowerCase().replace(/[\u064B-\u065F\u0670ـ]/g,'').replace(/[أإآ]/g,'ا').replace(/ة/g,'ه').replace(/ى/g,'ي').replace(/\s+/g,' ').trim();
const categoryId=value=>categories().find(c=>c.id===value||normalize(c.name)===normalize(value))?.id||null;
const number=v=>typeof toNum==='function'?toNum(v):(Number(v)||0);
const confirmed=r=>r?.classificationConfirmed===true;
const fuel=/بنزين|ديزل|سولار|محروقات|وقود|\b(?:petrol|gasoline|diesel|fuel|octane)\b/u;
const negative=/(?:^|\s)(?:ليس|ليست|غير|بدون|لا|مو|not|no)(?:\s+.{0,28})?(?:بنزين|ديزل|وقود|محروقات|petrol|gasoline|diesel|fuel)/u;
const cooking=/زيت\s*(?:طبخ|طعام|زيتون|ذره|دوار)|(?:cooking|edible|olive|sunflower)\s+oil/u;
const filter=/فلتر\s*(?:ال)?(?:ديزل|بنزين|وقود)|فلاتر\s*(?:ال)?(?:ديزل|بنزين|وقود)|مرشح\s*(?:ال)?(?:ديزل|بنزين|وقود)|\b(?:diesel|fuel|petrol)\s+filter\b|\bfilter\s+(?:diesel|fuel|petrol)\b/u;
const fuelMachine=/(?:منشار|مولد|مضخه|ماكينه)\s*(?:ال)?(?:بنزين|ديزل|وقود)|\b(?:petrol|gasoline)\s+(?:chainsaw|saw)\b|\b(?:diesel|fuel)\s+(?:generator|pump)\b/u;
const refilling=/تعبئه|تموين|تزويد|\brefuelling\b|\brefueling\b|\brefill\b/u;
const maintenance=/صيانه|تصليح|اصلاح|\b(?:repair|maintenance)\b/u;
const joined=/[+،,]|\sو(?!قود)(?=\p{L})/u;
const mixed=/مختلط|متنوع|\bmixed\b/u;
const equipment=/معدات|ايجار|فلتر|فلاتر|مرشح|منشار|مولد|مضخه|ماكينه|زيت\s*محرك|\b(?:equipment|rental|filter|generator|chainsaw|pump)\b|engine\s+oil/u;
const rules=[
 ['infra',/مواسير|خرسانه|اسمنت|حديد|بلوك|رمل|اسفلت|كيبل|كابل|\b(?:pipe|concrete|cement|rebar)\b/u],
 ['wages',/رواتب|راتب|اجور|عماله|يوميات\s*عامل|\b(?:salary|wages|payroll)\b/u],
 ['transport',/ترحيل|نقل|سطحه|لوبد|تاكسي|شحن|\b(?:freight|shipping|transport)\b/u],
 ['housing',/سكن|ايجار\s*(?:غرفه|شقه)|\baccommodation\b/u],
 ['food',/طعام|وجبه|مطعم|اعاشه|غداء|غدا|فطور|طبخ|مياه|ماء|عصير|سناك|\b(?:food|meal|restaurant|water|juice|snack)\b/u],
 ['safety',/خوذه|قفاز|ستره|سلامه|\b(?:safety|helmet)\b/u],
 ['design',/تصميم|مخططات|رسم\s*هندسي|\bdesign\b/u],
 ['comms',/باقه|انترنت|اتصالات|هاتف|\b(?:telecom|internet)\b/u],
 ['services',/اتعاب|استشاره|محامي|غسيل|غسل\s*سياره|تغيير\s*(?:ال)?زيت|oil\s*change|car\s*wash|\b(?:consulting|professional)\b/u],
 ['banking',/رسوم\s*بنكيه|عموله\s*تحويل|\bbank\s+(?:fee|charge)/u],
 ['loans',/سلفه|عهده|مسحوبات|\badvance\b/u],
 ['subcontractor',/مقاول\s*باطن|مقاوله\s*الباطن|\bsubcontract/u]
];
function readDescription(value){
 const text=normalize(value);if(!text)return {category:null,isFuel:false,ambiguous:false};
 const hasFuel=fuel.test(text);
 if(hasFuel&&negative.test(text))return {category:null,isFuel:false,ambiguous:true,reason:'الوصف ينفي شراء الوقود؛ يلزم مراجعة البند.'};
 if(cooking.test(text))return hasFuel?{category:null,isFuel:false,ambiguous:true,reason:'الوصف يجمع طعامًا ووقودًا؛ لا يُعتمد تصنيف موحد تلقائيًا.'}:{category:'food',isFuel:false,ambiguous:false};
 const partOrMachine=filter.test(text)||(hasFuel&&/فلتر|فلاتر|مرشح|زيت\s*(?:محرك|ديزل)|engine\s+oil/u.test(text))||fuelMachine.test(text);
 const simpleMachineRefill=fuelMachine.test(text)&&refilling.test(text)&&!joined.test(text)&&!filter.test(text);
 if(hasFuel&&(partOrMachine||maintenance.test(text))&&(refilling.test(text)||joined.test(text))&&!simpleMachineRefill)return {category:null,isFuel:false,ambiguous:true,reason:'الوصف يجمع قطعة أو صيانة مع وقود؛ راجع البنود ولا تنقلها للعامة تلقائيًا.'};
 if(hasFuel&&maintenance.test(text)&&!refilling.test(text))return {category:'services',isFuel:false,ambiguous:false,reason:'الوصف خدمة صيانة لمعدة وقود، وليس شراء وقود.'};
 if(partOrMachine&&!simpleMachineRefill)return {category:'equipment',isFuel:false,ambiguous:false,reason:'الوصف يشير إلى قطعة أو معدة تعمل بالوقود، وليس شراء الوقود نفسه.'};
 const hits=rules.filter(([,pattern])=>pattern.test(text)).map(([id])=>id);
 if(hasFuel){
  if(hits.length||mixed.test(text)||(equipment.test(text)&&joined.test(text)))return {category:null,isFuel:false,ambiguous:true,reason:'توجد بنود وقود وبنود أخرى في الوصف؛ راجعها قبل التصنيف.'};
  return {category:'fuel',isFuel:true,ambiguous:false};
 }
 if(equipment.test(text))hits.push('equipment');
 if(!hits.length&&/مصاريف\s*موقع|تنظيف|نظافه/u.test(text))hits.push('site');
 const unique=[...new Set(hits)];
 return {category:unique.length===1?unique[0]:null,isFuel:false,ambiguous:unique.length>1,reason:unique.length>1?'توجد دلالات لأكثر من بند؛ يلزم اختيار البند المناسب.':''};
}
root.analyzePurchaseClassification=function(record){
 const r=record||{},items=(Array.isArray(r.items)?r.items:[]).map(i=>String(i?.desc||i?.description||'').trim()).filter(Boolean);
 const notes=String(r.notes||'').trim(),ocrText=String(r.classificationText||'').trim(),body=[...items,...(notes?[notes]:[]),...(ocrText?[ocrText]:[])];
 const results=body.map(readDescription),identified=results.filter(x=>x.category),ids=[...new Set(identified.map(x=>x.category))];
 const unknownItem=items.some(text=>!readDescription(text).category);
 const ambiguous=results.some(x=>x.ambiguous)||ids.length>1||(ids.includes('fuel')&&unknownItem);
 if(ambiguous)return {category:ids.length===1?ids[0]:'other',confidence:'low',reason:results.find(x=>x.ambiguous)?.reason||'الوصف أو البنود مختلطة أو غير مكتملة؛ راجع المستند واختر البند.',isFuel:false,ambiguous:true};
 if(ids.length===1)return {category:ids[0],confidence:'high',reason:identified.find(x=>x.reason)?.reason||(ids[0]==='fuel'?'وصف البند يذكر شراء وقود بوضوح؛ اسم المورد ليس أساس القرار.':'اقتراح من وصف البنود والملاحظات، ويحتاج اعتمادك قبل تعديل التصنيف التاريخي.'),isFuel:ids[0]==='fuel',ambiguous:false};
 const categoryIds=new Set(categories().map(c=>c.id)),currentCategory=categoryId(r.category);
 if(confirmed(r)&&currentCategory)return {category:currentCategory,confidence:'high',reason:'هذا البند معتمد صراحة في مراجعة سابقة.',isFuel:currentCategory==='fuel',ambiguous:false};
 const labelResult=readDescription(r.categoryLabel||(!categoryIds.has(r.category)?r.category:''));
 if(currentCategory==='fuel'||labelResult.category==='fuel')return {category:'fuel',confidence:'low',reason:'التصنيف الحالي أو اسمه يشير إلى محروقات، لكن لا يوجد وصف كافٍ لتأكيد الوقود؛ راجع المستند.',isFuel:false,ambiguous:true};
 if(labelResult.category)return {category:labelResult.category,confidence:'medium',reason:'اقتراح من اسم البند فقط؛ تحقق من وصف المستند قبل الاعتماد.',isFuel:false,ambiguous:true};
 const vendor=normalize(r.vendor||r.vendorName||r.supplierName);
 if(/الدريس|محطه|محطة|petrol|petroly|octan|fuel/u.test(vendor))return {category:'fuel',confidence:'low',reason:'اسم المورد قرينة محتملة فقط؛ قد يبيع سلعًا غير الوقود. راجع البنود.',isFuel:false,ambiguous:true};
 return {category:currentCategory||'other',confidence:'low',reason:'الوصف لا يكفي لاقتراح بند موثوق؛ اختر التصنيف من المستند.',isFuel:false,ambiguous:true};
};
root.enforceFuelGeneral=function(record,{existing=null,manualCategory=false}={}){
 const candidate={...(record||{})},analysis=root.analyzePurchaseClassification(candidate);
 if(['revenue','sale'].includes(candidate.type))return {record:candidate,pending:false,changed:false,reason:'السجل إيراد؛ لا يطبق عليه توزيع المشتريات.'};
 if(candidate.fuelProjectException?.projectId&&candidate.fuelProjectException.projectId===candidate.projectId)return {record:candidate,pending:false,changed:false,reason:'محروقات خاصة بالمشروع حسب اعتماد المالك؛ يبقى ربطها بالمشروع.'};
 const selectedFuel=categoryId(candidate.category)==='fuel'&&(manualCategory===true||(confirmed(candidate)&&analysis.isFuel&&!analysis.ambiguous));
 const clearFuel=analysis.isFuel&&analysis.confidence==='high'&&!analysis.ambiguous;
 if(!selectedFuel&&!clearFuel)return {record:candidate,pending:false,changed:false,reason:analysis.reason};
 const projects=typeof projs!=='undefined'&&Array.isArray(projs)?projs:(Array.isArray(root.projs)?root.projs:[]);
 const previous=existing?.projectId||candidate.projectId||'';
 const oldScope=[existing?.projectId,...(existing?.projectAllocations||[]).map(a=>a.projectId)].filter(Boolean);
 const oldProject=projects.find(p=>oldScope.includes(p.id)&&(p.status==='study'||number(p.siteExpensesTotal)>0))||projects.find(p=>p.id===existing?.projectId);
 if(oldProject?.status==='study')return {record:candidate,pending:true,changed:false,reason:'المشروع السابق تحت الدراسة ومُستبعد من إجماليات الرئيسية؛ راجع انتقال تكلفته للعامة قبل تغيير الربط.'};
 if(oldProject&&number(oldProject.siteExpensesTotal)>0)return {record:candidate,pending:true,changed:false,reason:'المشروع السابق يستخدم مصروفات مجمعة يدويًا؛ راجع المبلغ المجمع قبل نقل هذا السجل للعامة حتى لا تتكرر التكلفة.'};
 if(candidate.projectAllocations?.length){candidate.previousProjectAllocations=candidate.projectAllocations;candidate.projectAllocations=[];candidate.projectId='';candidate.projectClassificationReason='محروقات عامة حسب سياسة المالك؛ أُلغي توزيعها على المشاريع.';return {record:candidate,pending:false,changed:true,reason:candidate.projectClassificationReason};}
 if(!candidate.projectId)return {record:candidate,pending:false,changed:false,reason:'السجل محروقات عامة بالفعل.'};
 candidate.projectId='';candidate.previousProjectId=previous;candidate.projectClassificationReason=selectedFuel?'محروقات اختيرت يدويًا؛ تُسجل مشتريات عامة.':'وصف وقود واضح؛ يُسجل مشتريات عامة.';
 return {record:candidate,pending:false,changed:true,reason:candidate.projectClassificationReason};
};
if(typeof document==='undefined')return;
const el=(tag,text)=>{const node=document.createElement(tag);if(text!==undefined)node.textContent=text;return node;};
const money=v=>number(v).toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2});
const categoryName=id=>categories().find(c=>c.id===id)?.name||String(id||'غير محدد');
const projectName=id=>{const ps=typeof projs!=='undefined'?projs:[];return !id?'مشتريات عامة / بدون مشروع':ps.find(p=>p.id===id)?.name||'مشروع غير موجود — يحتاج مراجعة';};
function recordsForReview(){
 const invoices=typeof invs!=='undefined'&&Array.isArray(invs)?invs:[];
 const orders=Array.isArray(root.opsData?.purchaseOrders)?root.opsData.purchaseOrders:[];
 return [...invoices.filter(r=>r&&r.status!=='cancelled'&&['purchase','expense'].includes(r.type)).map(record=>({source:'inv',record})),...orders.filter(r=>r&&r.status!=='cancelled'&&!(r.invoiceId&&invoices.some(i=>i.id===r.invoiceId&&i.status!=='cancelled'))).map(record=>({source:'purchase',record}))].filter(({record})=>{
  const analysis=root.analyzePurchaseClassification(record),descriptions=[record.notes,record.classificationText,record.categoryLabel,...(record.items||[]).map(i=>i?.desc||i?.description||'')];
  const allocated=typeof root.hasInvoiceProjectAllocations==='function'&&root.hasInvoiceProjectAllocations(record);
  return (!record.projectId&&!allocated)||analysis.isFuel||analysis.category==='fuel'||categoryId(record.category)==='fuel'||descriptions.some(text=>fuel.test(normalize(text)));
 });
}
root.openGeneralPurchaseReview=function(){
 document.getElementById('general-purchase-review')?.remove();
 const overlay=el('div');overlay.id='general-purchase-review';overlay.setAttribute('role','dialog');overlay.setAttribute('aria-modal','true');overlay.setAttribute('aria-label','مراجعة المشتريات العامة وتصنيف المحروقات');
 overlay.style.cssText='position:fixed;inset:0;z-index:100260;background:#0f172a99;display:flex;align-items:center;justify-content:center;padding:12px;direction:rtl';
 const panel=el('div');panel.style.cssText='background:white;color:#17324f;border-radius:16px;padding:18px;width:min(820px,100%);max-height:88vh;overflow:auto;font-family:inherit';
 panel.append(el('h3','مراجعة المشتريات العامة والمحروقات'),el('p','الاقتراح لا يغيّر السجلات تلقائيًا. اعتمد البند من المستند؛ المحروقات المؤكدة تُسجل عامة، وتبقى الضريبة حسب اختيارك.'));
 const close=el('button','إغلاق');close.type='button';close.className='h1077-btn';close.onclick=()=>overlay.remove();panel.append(close);
 const rows=recordsForReview();if(!rows.length)panel.append(el('p','لا توجد مشتريات عامة أو مرشحات محروقات مرتبطة تحتاج عرضًا.'));
 rows.forEach(({source,record})=>{
  const analysis=root.analyzePurchaseClassification(record),snapshot=JSON.stringify(record),card=el('article');
  card.style.cssText='border:1px solid #dbe8f3;border-radius:12px;padding:12px;margin-top:12px;line-height:1.8;overflow-wrap:anywhere';
  card.append(el('strong',(record.number||'بدون رقم')+' — '+(record.vendor||record.supplierName||'بدون مورد')),
   el('p',projectName(record.projectId)+' | '+money(record.total)+' ر.س | '+(record.date||'دون تاريخ')),
   el('p','البند الحالي: '+categoryName(record.category)+' — الاقتراح: '+categoryName(analysis.category)),el('p',analysis.reason));
  const descriptions=(record.items||[]).map(i=>i.desc||'').filter(Boolean).join('، ');if(descriptions||record.notes)card.append(el('p',descriptions+(descriptions&&record.notes?' — ':'')+(record.notes||'')));
  const label=el('label','التصنيف المعتمد '),select=el('select');select.style.cssText='width:100%;padding:10px;font:inherit';select.setAttribute('aria-label','التصنيف المعتمد للفاتورة '+(record.number||''));
  const placeholder=el('option','— اختر من المستند —');placeholder.value='';select.append(placeholder);
  categories().forEach(c=>{const option=el('option',c.name);option.value=c.id;select.append(option);});
  select.value=analysis.ambiguous?'':analysis.category;label.append(select);card.append(label);
  const move=el('input');move.type='checkbox';const moveLabel=el('label',' نقل إلى المشتريات العامة / بدون مشروع');moveLabel.prepend(move);moveLabel.style.display=record.projectId?'block':'none';card.append(moveLabel);
  const preview=el('p'),status=el('p');status.setAttribute('role','status');status.setAttribute('aria-live','polite');
  const showPreview=()=>{
   const candidate={...record,category:select.value||record.category,classificationConfirmed:!!select.value,...(move.checked?{projectId:''}:{})};
   const result=root.enforceFuelGeneral(candidate,{existing:record,manualCategory:!!select.value});
   preview.textContent=result.pending?result.reason:(result.changed||move.checked?'سيُسجل كمشتريات عامة، دون تحميله على ربح مشروع. المبالغ والضريبة لا تتغير.':'سيُعتمد البند المختار دون تغيير مبالغ السجل.');
  };select.onchange=showPreview;move.onchange=showPreview;showPreview();card.append(preview,status);
  const save=el('button','اعتماد التصنيف');save.type='button';save.className='h1077-btn';
  save.onclick=async()=>{
   if(!select.value){status.textContent='اختر التصنيف الصحيح من المستند أولًا.';return;}
   if(typeof root.savePurchaseClassificationChange!=='function'){status.textContent='خدمة حفظ التصنيف غير متاحة حاليًا. أعد فتح النسخة المحدثة.';return;}
   const changes={category:select.value,classificationConfirmed:true,...(move.checked?{projectId:''}:{})};
   const route=root.enforceFuelGeneral({...record,...changes},{existing:record,manualCategory:true});
   if(route.pending){status.textContent=route.reason;return;}
   if(route.changed)changes.projectId='';
   save.disabled=true;select.disabled=true;move.disabled=true;status.textContent='جاري الحفظ...';
   try{
    const result=await root.savePurchaseClassificationChange({source,id:record.id,expectedSnapshot:snapshot,changes,reason:analysis.reason});
    if(!result?.ok){status.textContent=result?.error||result?.reason||'تعذر الحفظ؛ لم يُعتمد التصنيف.';return;}
    root.openGeneralPurchaseReview();
   }catch(error){status.textContent=error?.message||'تعذر الحفظ؛ أعد المحاولة.';}
   finally{save.disabled=false;select.disabled=false;move.disabled=false;}
  };card.append(save);
  const edit=el('button','مراجعة المستند');edit.type='button';edit.className='h1077-btn alt';edit.style.margin='6px';edit.onclick=()=>{overlay.remove();if(source==='inv'&&typeof revInv==='function'){if(typeof goTab==='function')goTab('add');revInv(record.id);}else if(typeof root.opsOpen==='function')root.opsOpen('purchase',record.id);};card.append(edit);panel.append(card);
 });
 overlay.append(panel);document.body.append(overlay);close.focus();
};
function addReviewButton(){
 const container=document.getElementById('h1077-buy');if(!container||container.querySelector('#general-purchase-review-button'))return;
 const button=el('button','مراجعة المشتريات العامة والمحروقات');button.id='general-purchase-review-button';button.type='button';button.className='h1077-btn alt';button.style.marginBottom='10px';button.onclick=()=>root.openGeneralPurchaseReview();container.prepend(button);
}
function init(){addReviewButton();if(typeof MutationObserver!=='undefined')new MutationObserver(addReviewButton).observe(document.body,{childList:true,subtree:true});}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})(typeof window!=='undefined'?window:globalThis);
