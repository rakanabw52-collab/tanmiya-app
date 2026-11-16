import assert from 'node:assert/strict';
const origin='https://rakanabw52-collab.github.io';
globalThis.Deno={env:{get:k=>({SUPABASE_URL:'https://test.supabase.co',SUPABASE_SERVICE_ROLE_KEY:'server-secret-test-only',SUPABASE_ANON_KEY:'anon-test'})[k]},serve:()=>{}};
const {handler}=await import('../supabase/functions/pin-auth/index.ts');
let calls=[],mode='valid';
const uid='11111111-1111-4111-8111-111111111111';
globalThis.fetch=async(url,opt)=>{
 const path=new URL(url).pathname,body=opt.body?JSON.parse(opt.body):null;calls.push({path,body,headers:opt.headers});
 const result=path.endsWith('/hd_pin_claim')?(mode==='limited'?{retry_after:900}:{retry_after:0,user_id:mode==='invalid'?null:uid}):
 path.endsWith('/hd_pin_register_guard')?0:
 path.endsWith('/hd_pin_register')?mode!=='collision':
 path.endsWith('/hd_pin_success')?null:
 path==='/auth/v1/user'?{id:uid}:
 path.startsWith('/auth/v1/admin/users/')?{id:uid,email:'test@example.invalid',banned_until:mode==='banned'?'2099-01-01':null}:
 path==='/auth/v1/admin/generate_link'?{id:mode==='mismatch'?'another':uid,hashed_token:'server-one-use'}:
 path==='/auth/v1/verify'?{access_token:'test-access',refresh_token:'test-refresh',user:{id:uid}}:undefined;
 assert.notEqual(result,undefined,path);
 return new Response(JSON.stringify(result),{status:200});
};
const request=(body,token,requestOrigin=origin)=>new Request('https://test.supabase.co/functions/v1/pin-auth',{method:'POST',headers:{origin:requestOrigin,'content-type':'application/json',...(token?{authorization:'Bearer '+token}:{})},body:JSON.stringify(body)});
const jwt=amr=>'header.'+Buffer.from(JSON.stringify({amr})).toString('base64url')+'.signature';
let r=await handler(request({action:'login',pin:'1234'}));assert.equal(r.status,200);assert.deepEqual(await r.json(),{access_token:'test-access',refresh_token:'test-refresh'});assert.equal(r.headers.get('cache-control'),'no-store');assert(!JSON.stringify(calls).includes('1234'));assert.equal(calls.at(-1).path,'/rest/v1/rpc/hd_pin_success');
for(const [m,status] of [['invalid',401],['limited',429],['mismatch',503],['banned',401]]){mode=m;calls=[];r=await handler(request({action:'login',pin:'1234'}));assert.equal(r.status,status,m);if(m!=='mismatch')assert(!calls.some(c=>c.path.includes('generate_link')));}
mode='valid';calls=[];r=await handler(request({action:'register',pin:'1234'}));assert.equal(r.status,401);assert.equal(calls.length,0);
r=await handler(request({action:'register',pin:'1234'},jwt([{method:'otp',timestamp:Date.now()/1000}])));assert.equal(r.status,403);
r=await handler(request({action:'register',pin:'1234'},jwt([{method:'password',timestamp:Date.now()/1000-400}])));assert.equal(r.status,403);
const recent=jwt([{method:'password',timestamp:Math.floor(Date.now()/1000)}]);
r=await handler(request({action:'register',pin:'1234'},recent));assert.equal(r.status,200);
mode='collision';r=await handler(request({action:'register',pin:'1234'},recent));assert.equal(r.status,409);
calls=[];for(const pin of ['123','12345','12ab',1234,'١٢٣٤']){r=await handler(request({action:'login',pin}));assert.equal(r.status,400);}assert.equal(calls.length,0);
r=await handler(request({action:'login',pin:'1234'},null,'https://evil.example'));assert.equal(r.status,403);
r=await handler(new Request('https://test.supabase.co',{method:'OPTIONS',headers:{origin}}));assert.equal(r.status,204);
console.log('PASS: PIN server sessions, role-bound lookup, rate limits, recent-password registration, collisions, validation, CORS, no plaintext PIN upstream.');
