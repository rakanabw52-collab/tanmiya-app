"""Pure classification rules: evidence, false positives, immutability and protected transfers."""
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
script=r'''
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const context={console,projs:[{id:'active',status:'active',siteExpensesTotal:0},
 {id:'manual',status:'active',siteExpensesTotal:1000},{id:'study',status:'study',siteExpensesTotal:0}]};
context.window=context;vm.createContext(context);
vm.runInContext(fs.readFileSync('purchase-classification.js','utf8'),context);
const analyze=context.analyzePurchaseClassification,enforce=context.enforceFuelGeneral;
const local=value=>JSON.parse(JSON.stringify(value));
function fuel(record){const a=analyze(record);assert.equal(a.category,'fuel');assert.equal(a.isFuel,true);assert.equal(a.confidence,'high');assert.equal(a.ambiguous,false);}
function notFuel(record,category){const a=analyze(record);assert.equal(a.isFuel,false,JSON.stringify(a));if(category)assert.equal(a.category,category);}
function ambiguous(record){const a=analyze(record);assert.equal(a.isFuel,false,JSON.stringify(a));assert.equal(a.ambiguous,true,JSON.stringify(a));}
for(const record of [
 {items:[{desc:'شراء بنزين 91 مقدار 20 لتر'}]},
 {notes:'تعبئة ديزل للمولد'},
 {notes:'Diesel 20 liters'},
 {notes:'تعبئة مولد ديزل'},
 {classificationText:'محروقات'},
 {category:'fuel',classificationConfirmed:true},
])fuel(record);
for(const record of [
 {vendor:'شركة الدريس للخدمات البترولية'},
 {supplierName:'PETROLY fuel station'},
 {category:'fuel'},
 {categoryLabel:'محروقات'},
])ambiguous(record);
for(const [notes,category] of [
 ['زيت طبخ','food'],['زيت دوار الشمس','food'],['cooking oil','food'],
 ['فلتر ديزل','equipment'],['فلتر وقود','equipment'],['diesel filter','equipment'],
 ['منشار بنزين','equipment'],['مولد وقود','equipment'],['مضخة وقود','equipment'],
 ['صيانة مضخة وقود','services'],['fuel pump maintenance','services'],
 ['غسيل السيارة','services'],['car wash','services'],['تغيير زيت','services'],['oil change','services'],
])notFuel({notes,category:'fuel',vendor:'محطة وقود'},category);
for(const record of [
 {notes:'ليست فاتورة وقود',category:'fuel'},
 {notes:'لا يشمل الوقود',category:'fuel',classificationConfirmed:true},
 {notes:'بنزين ومياه'},
 {notes:'بنزين + عصير'},
 {notes:'فلتر ديزل + تعبئة ديزل 20 لتر'},
 {notes:'فلتر ديزل وتعبئة ديزل 20 لتر'},
 {notes:'بنزين وزيت طبخ'},
 {items:[{desc:'بنزين 91'},{desc:'مواسير بلاستيك'}]},
 {items:[{desc:'بنزين 91'},{desc:'سلعة غير واضحة'}]},
 {classificationText:'محروقات',notes:'غسيل سيارة'},
 {classificationText:'وقود',notes:'هذه ليست فاتورة وقود'},
])ambiguous(record);
notFuel({items:[{desc:'وجبة غداء'}],vendor:'الدريس',category:'fuel'},'food');
const original={id:'new-fuel',type:'purchase',projectId:'active',notes:'شراء بنزين 91',category:'other'};
const originalJSON=JSON.stringify(original),r=enforce(original,{manualCategory:false});
assert.equal(JSON.stringify(original),originalJSON);assert.equal(r.changed,true);assert.equal(r.pending,false);
assert.equal(r.record.projectId,'');assert.equal(r.record.previousProjectId,'active');assert.equal(r.record.category,'other');
assert.ok(r.record.projectClassificationReason);
assert.equal(enforce({category:'fuel',projectId:'active',vendor:'الدريس'},{manualCategory:false}).changed,false);
assert.equal(enforce({category:'fuel',projectId:'active'},{manualCategory:true}).record.projectId,'');
assert.equal(enforce({category:'محروقات',projectId:'active'},{manualCategory:true}).record.projectId,'');
assert.equal(enforce({category:'fuel',projectId:'active',classificationConfirmed:true,notes:'غسيل سيارة'},{manualCategory:false}).changed,false);
assert.equal(enforce({category:'fuel',projectId:'active',classificationConfirmed:true,notes:'بنزين + عصير'},{manualCategory:false}).changed,false);
assert.equal(enforce({category:'fuel',projectId:'active',classificationConfirmed:true,notes:'غسيل سيارة'},{manualCategory:true}).record.projectId,'');
for(const projectId of ['manual','study']){
 const rec={id:'old',projectId,category:'fuel',notes:'شراء ديزل'};
 const blocked=enforce(rec,{existing:rec,manualCategory:true});
 assert.equal(blocked.pending,true);assert.equal(blocked.changed,false);assert.equal(blocked.record.projectId,projectId);
 assert.ok(blocked.reason);
 const fresh=enforce({...rec,id:'new'},{existing:null,manualCategory:true});
 assert.equal(fresh.pending,false);assert.equal(fresh.record.projectId,'');
}
const ownerException={id:'owner-fuel-exception',category:'fuel',notes:'ديزل مشروع الفرسان',projectId:'manual',fuelProjectException:{projectId:'manual',reason:'owner decision'}};
const exception=enforce(ownerException,{existing:ownerException,manualCategory:true});
assert.equal(exception.pending,false);assert.equal(exception.changed,false);assert.equal(exception.record.projectId,'manual');
assert.equal(enforce({id:'general',projectId:'',notes:'ديزل'}).changed,false);
assert.equal(enforce({type:'revenue',projectId:'active',notes:'بيع ديزل',category:'fuel'},{manualCategory:true}).changed,false);
assert.equal(enforce({type:'sale',projectId:'active',notes:'بيع بنزين',category:'fuel'},{manualCategory:true}).changed,false);
assert.equal(enforce({projectId:'active',notes:'شراء بنزين'}).record.projectId,'');
console.log('PASS pure purchase classification: descriptions/OCR, vendor-only uncertainty, cooking oil, fuel parts/tools, negation/mixed invoices, manual Arabic fuel, no historical category rewrite, manual-total/study transfer protection');
'''
subprocess.run(['node','-e',script],cwd=ROOT,check=True)
