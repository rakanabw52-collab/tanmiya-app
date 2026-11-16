// No dependencies. Secrets remain in Supabase's server environment, never in the app bundle.
const URL_BASE = Deno.env.get('SUPABASE_URL')!;
const SECRET = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
const ANON = Deno.env.get('SUPABASE_ANON_KEY')!;
const ORIGIN = 'https://rakanabw52-collab.github.io';
const enc = new TextEncoder();
async function digest(purpose: string, value: string): Promise<string> {
 const key = await crypto.subtle.importKey('raw',enc.encode(SECRET),{name:'HMAC',hash:'SHA-256'},false,['sign']);
 return Array.from(new Uint8Array(await crypto.subtle.sign('HMAC',key,enc.encode('tanmiya-pin-v1:'+purpose+':'+value))),b=>b.toString(16).padStart(2,'0')).join('');
}
async function api(path: string, body?: unknown, token=SECRET, key=SECRET) {
 const r=await fetch(URL_BASE+path,{method:body===undefined?'GET':'POST',headers:{apikey:key,Authorization:'Bearer '+token,'Content-Type':'application/json'},...(body===undefined?{}:{body:JSON.stringify(body)})});
 let data;try{data=await r.json();}catch{data=null;}
 if(!r.ok) throw new Error('upstream');
 return data;
}
function json(req: Request, data: unknown, status=200, retry=0) {
 return new Response(JSON.stringify(data),{status,headers:{'Content-Type':'application/json','Cache-Control':'no-store','Pragma':'no-cache','Vary':'Origin',...(req.headers.get('origin')===ORIGIN?{'Access-Control-Allow-Origin':ORIGIN}:{}),...(retry?{'Retry-After':String(retry)}:{})}});
}
export async function handler(req: Request): Promise<Response> {
 const origin=req.headers.get('origin');
 if(origin && origin!==ORIGIN) return json(req,{error:'origin'},403);
 if(req.method==='OPTIONS') return new Response(null,{status:204,headers:{'Access-Control-Allow-Origin':ORIGIN,'Access-Control-Allow-Methods':'POST, OPTIONS','Access-Control-Allow-Headers':'authorization, apikey, content-type','Access-Control-Max-Age':'600','Vary':'Origin'}});
 if(req.method!=='POST') return json(req,{error:'method'},405);
 try {
  // Bounded body, no request/credential logging.
  const raw=await req.text();if(raw.length>2048)return json(req,{error:'body'},400);
  let body;try{body=JSON.parse(raw);}catch{return json(req,{error:'body'},400);}
  if(!body||typeof body.pin!=='string'||!/^\d{4}$/.test(body.pin))return json(req,{error:'pin_format'},400);
  const pinDigest=await digest('credential',body.pin);
  if(body.action==='register') {
   const token=(req.headers.get('authorization')||'').replace(/^Bearer\s+/i,'');
   if(!token||token===ANON)return json(req,{error:'auth_required'},401);
   let user;try{user=await api('/auth/v1/user',undefined,token,ANON);}catch{return json(req,{error:'auth_required'},401);}
   // getUser above validates the signature. Only a recent password login can set/reset a PIN.
   let claims;try{claims=JSON.parse(atob(token.split('.')[1].replace(/-/g,'+').replace(/_/g,'/')));}catch{return json(req,{error:'auth_required'},401);}
   const recent=Array.isArray(claims.amr)&&claims.amr.some((a: {method:string,timestamp:number})=>a.method==='password'&&Number(a.timestamp)<=Date.now()/1000+30&&Number(a.timestamp)>Date.now()/1000-300);
   if(!recent)return json(req,{error:'password_required'},403);
   const retry=await api('/rest/v1/rpc/hd_pin_register_guard',{p_uid:user.id});
   if(retry>0)return json(req,{error:'rate_limited',retry_after:retry},429,retry);
   const saved=await api('/rest/v1/rpc/hd_pin_register',{p_uid:user.id,p_digest:pinDigest});
   return saved===true?json(req,{ok:true}):json(req,{error:'pin_unavailable'},409);
  }
  if(body.action!=='login')return json(req,{error:'action'},400);
  // Proxy headers are only an additional bucket. Global limits still apply if a client changes IP/headers.
  const ip=req.headers.get('x-forwarded-for')?.split(',')[0]?.trim()||'unknown';
  const client=await digest('client',ip);
  const claim=await api('/rest/v1/rpc/hd_pin_claim',{p_digest:pinDigest,p_client:client});
  if(claim.retry_after>0)return json(req,{error:'rate_limited',retry_after:claim.retry_after},429,claim.retry_after);
  if(!claim.user_id)return json(req,{error:'invalid_pin'},401);
  const accountResponse=await api('/auth/v1/admin/users/'+encodeURIComponent(claim.user_id));
  const account=accountResponse.user||accountResponse;
  if(!account.email||account.deleted_at||(account.banned_until&&new Date(account.banned_until).getTime()>Date.now()))return json(req,{error:'invalid_pin'},401);
  // No email is sent and no user is created: the ID came from the existing authorized registry.
  const link=await api('/auth/v1/admin/generate_link',{type:'magiclink',email:account.email});
  if(link.id!==claim.user_id||!link.hashed_token)throw new Error('account mismatch');
  const session=await api('/auth/v1/verify',{type:'email',token_hash:link.hashed_token},ANON,ANON);
  if(session.user?.id!==claim.user_id||!session.access_token||!session.refresh_token)throw new Error('session mismatch');
  await api('/rest/v1/rpc/hd_pin_success',{p_client:client});
  return json(req,{access_token:session.access_token,refresh_token:session.refresh_token});
 } catch {
  return json(req,{error:'unavailable'},503);
 }
}
Deno.serve(handler);
