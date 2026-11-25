"""Input VAT is recognized once while the original purchase posting remains immutable."""
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
script=r'''
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const context={console,Date,projs:[],HD_USER:'owner-test',_todayStr:()=> '2026-11-24',
 _isClosedDate:()=> false,_expAccFor:invoice=>invoice.classificationAccount||'5040',
 coa:[{id:'1030',type:'asset'},{id:'2010',type:'liability'},
      {id:'5010',type:'expense'},{id:'5040',type:'expense'}],journals:[]};
context.window=context;vm.createContext(context);
for(const file of ['purchase-classification.js','invoice-vat-adjustments.js'])
 vm.runInContext(fs.readFileSync(file,'utf8'),context);
const local=x=>JSON.parse(JSON.stringify(x));
const plan=(invoice,options={})=>context.planInvoiceVATRecovery(invoice,{nowDate:'2026-11-24',...options});
const review=(invoice,options={})=>context.reviewFuelVATCandidate(invoice,options);
const valid=invoice=>context.hasValidVATRecoveryAdjustment(invoice);
function reset(options={}){
 context._isClosedDate=()=>false;
 const invoice={id:'fuel-1',type:'purchase',number:'FUEL-1',date:'2026-11-01',
  vendor:'مورد اختبار',vendorVAT:'300000000000003',category:'fuel',notes:'بنزين 91 — 20 لتر',
  projectId:'',subtotal:100,vat:15,total:115,...options.invoice};
 const account=options.account||'5040';
 const base={id:'base-fuel-1',source:'inv',sourceId:invoice.id,date:invoice.date,
  desc:'قيد أصل محفوظ',lines:[{acc:account,debit:115,credit:0},{acc:'2010',debit:0,credit:115}]};
 context.journals=options.unposted?[]:[base];
 return invoice;
}
function apply(invoice,options={}){
 const outcome=plan(invoice,options);assert.equal(outcome.ok,true,outcome.reason);
 if(outcome.adjustment)context.journals.push(local(outcome.adjustment));
 return outcome;
}
function balance(account){return context.journals.reduce((sum,j)=>sum+j.lines.filter(l=>l.acc===account).reduce((n,l)=>n+Math.round(l.debit*100)-Math.round(l.credit*100),0),0)/100;}
// A new adjustment changes only the VAT/expense split; purchase, payable and source stay intact.
let invoice=reset(),originalInvoice=JSON.stringify(invoice),originalJournal=JSON.stringify(context.journals[0]);
assert.equal(review(invoice).ok,true);
let result=plan(invoice);
assert.equal(result.ok,true,result.reason);assert.equal(JSON.stringify(invoice),originalInvoice);
assert.equal(JSON.stringify(context.journals[0]),originalJournal);
assert.equal(result.invoice.vatRecoverable,true);assert.equal(result.adjustment.date,'2026-11-24');
assert.equal(result.adjustment.source,'vatRecoveryAdjustment');assert.equal(result.adjustment.sourceId,invoice.id);
assert.deepEqual(local(result.adjustment.lines),[{acc:'1030',debit:15,credit:0},{acc:'5040',debit:0,credit:15}]);
context.journals.push(local(result.adjustment));invoice=result.invoice;
assert.equal(valid(invoice),true);assert.equal(balance('5040'),100);assert.equal(balance('1030'),15);assert.equal(balance('2010'),-115);
assert.deepEqual(local(context.vatAdjustedBasePostings(invoice)),JSON.parse(originalJournal).lines);
assert.equal(JSON.stringify(context.journals[0]),originalJournal);
// Older clients preserve the source through their existing pending-link guard.
// The explicit VAT protection marker distinguishes this from an unresolved duplicate link.
const sourceLines=JSON.stringify(context.journals[0].lines),sourceDate=context.journals[0].date;
context.journals[0].sourceLinkPendingReview=true;
context.journals[0].vatRecoverySourceProtected=true;
assert.equal(valid(invoice),true);
assert.deepEqual(local(context.vatAdjustedBasePostings(invoice)),JSON.parse(sourceLines));
assert.equal(JSON.stringify(context.journals[0].lines),sourceLines);assert.equal(context.journals[0].date,sourceDate);
delete context.journals[0].vatRecoverySourceProtected;
assert.equal(valid(invoice),false);assert.equal(plan(invoice).ok,false);
context.journals[0].vatRecoverySourceProtected=true;
// Retrying does not create another adjustment, including after the posting period closes.
const before=JSON.stringify(context.journals),retry=plan(invoice);
assert.equal(retry.ok,true);assert.equal(retry.alreadyApplied,true);assert.equal(retry.adjustment,null);
assert.equal(JSON.stringify(context.journals),before);
context._isClosedDate=()=>true;assert.equal(valid(invoice),true);assert.equal(plan(invoice).adjustment,null);
context._isClosedDate=()=>false;
// JSON object property order and a project allocation do not change financial identity.
context.journals[0].lines=context.journals[0].lines.map(l=>({credit:l.credit,acc:l.acc,debit:l.debit}));
assert.equal(valid(invoice),true);
assert.equal(valid({...invoice,projectId:'another-project',projectAllocations:[{projectId:'another-project',total:115}]}),true);
for(const edits of [{vat:16,total:116},{subtotal:101,total:116},{date:'2026-11-02'},
 {classificationAccount:'5010'},{status:'cancelled'},{vatRecoverable:false},{id:'other-id'}]){
 const changed={...invoice,...edits};assert.equal(valid(changed),false,JSON.stringify(edits));
 assert.equal(context.vatAdjustedBasePostings(changed),null);assert.equal(plan(changed).ok,false);
}
const adjustment=context.journals[1];
adjustment.lines[0].debit=16;assert.equal(valid(invoice),false);adjustment.lines[0].debit=15;
context.journals.push({...adjustment,id:'second-adjustment'});assert.equal(valid(invoice),false);context.journals.pop();
context.journals.push({id:'reverse-adjustment',reverses:adjustment.id,lines:[]});assert.equal(valid(invoice),false);context.journals.pop();
context.journals[0].lines[0].debit=116;assert.equal(valid(invoice),false);
const oldClone=JSON.parse(originalJournal);
assert.equal(context.hasValidVATRecoveryAdjustment(invoice,oldClone),false);
for(const lines of [null,{},[null],[{acc:'5040',debit:'bad',credit:0}]]){
 context.journals[0].lines=lines;assert.equal(valid(invoice),false);
}
// The actual posted expense account is preserved even when the classifier would choose another.
invoice=reset({account:'5010'});result=apply(invoice);
assert.equal(result.invoice.classificationAccount,'5010');assert.equal(result.adjustment.lines[1].acc,'5010');
assert.equal(balance('5010'),100);assert.equal(balance('5040'),0);assert.equal(valid(result.invoice),true);
// Existing recognition is retained without a second VAT debit.
invoice=reset();context.journals[0].lines=[{acc:'5040',debit:100,credit:0},{acc:'1030',debit:15,credit:0},{acc:'2010',debit:0,credit:115}];
originalJournal=JSON.stringify(context.journals[0]);result=plan(invoice);
assert.equal(result.ok,true);assert.equal(result.adjustment,null);assert.equal(result.invoice.vatRecoverable,true);
assert.equal(JSON.stringify(context.journals[0]),originalJournal);
// A first posting can use the tax flag directly; zero VAT is never invented.
invoice=reset({unposted:true});result=plan(invoice);assert.equal(result.ok,true);assert.equal(result.adjustment,null);
assert.equal(result.invoice.vatRecoverable,true);assert.equal(context.journals.length,0);
invoice=reset({invoice:{subtotal:115,vat:0,total:115}});assert.equal(plan(invoice).ok,false);assert.equal(invoice.vat,0);
// Reclassification needs clean document identity and credible fuel evidence.
for(const edits of [{vendorVAT:'123'},{number:''},{date:'2099-01-01'},{date:'2026-02-30'},
 {vat:16},{total:118},{status:'cancelled'},{type:'revenue'},
 {notes:'زيت طبخ'},{notes:'غسيل سيارة'},{notes:'بنزين ومياه'}]){
 invoice=reset({invoice:edits});assert.equal(plan(invoice,{ownerConfirmedFuel:true}).ok,false,JSON.stringify(edits));
}
invoice=reset({invoice:{notes:'',category:'fuel'}});assert.equal(plan(invoice).ok,false);
assert.equal(plan(invoice,{ownerConfirmedFuel:true}).ok,true);
invoice=reset({invoice:{notes:'',category:'fuel',classificationConfirmed:true}});assert.equal(plan(invoice).ok,true);
invoice=reset({invoice:{notes:'شراء ديزل',category:'other'}});assert.equal(plan(invoice).ok,true);
// Respect the open review day; a later review is not backdated to the purchase.
invoice=reset();assert.equal(plan(invoice,{nowDate:'2026-11-01'}).ok,false);
context._isClosedDate=date=>date==='2026-11-24';assert.equal(plan(invoice).ok,false);
context._isClosedDate=date=>date==='2026-11-01';assert.equal(plan(invoice).ok,false);
// Ambiguous, reversed, duplicate and mismatched original postings stay unmodified.
for(const mutate of [
 j=>{j.sourceLinkPendingReview=true;},
 j=>{j.reverses='another-journal';},
 j=>{context.journals.push({id:'reversal',reverses:j.id,lines:[]});},
 j=>{context.journals.push({...j,id:'duplicate-base'});},
 j=>{j.lines=[{acc:'5040',debit:110,credit:0},{acc:'1030',debit:5,credit:0},{acc:'2010',debit:0,credit:115}];},
 j=>{j.lines[0].debit=120;j.lines[1].credit=120;},
 j=>{j.date='2026-10-31';},
 j=>{j.lines[0].acc='unknown';},
]){
 invoice=reset();mutate(context.journals[0]);const prior=JSON.stringify(context.journals);
 assert.equal(plan(invoice).ok,false);assert.equal(JSON.stringify(context.journals),prior);
}
// Recorded cent-level legacy differences are retained, not repaired by fabricating an amount.
invoice=reset({invoice:{subtotal:100,vat:15,total:114.99}});result=apply(invoice);
assert.equal(result.invoice.total,114.99);assert.equal(result.invoice.vat,15);
assert.equal(result.invoice.vatRecoveryAdjustment.roundingDifferenceCents,1);assert.equal(valid(result.invoice),true);
console.log('PASS VAT adjustment planning: source journals preserved, one balanced adjustment, idempotence, original account, signature/reversal protection, explicit fuel evidence, document/period checks, no invented VAT, retained rounding facts');
'''
subprocess.run(['node','-e',script],cwd=ROOT,check=True)
