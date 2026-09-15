// Service Worker - نظام هدف التنمية (إصدار 1078 - تحديث إجباري)
const CACHE_NAME = 'hadaf-1078-r2';
const ASSETS = [
  './','./index.html','./manifest.json',
  './icon-192.png','./icon-512.png','./apple-touch-icon.png','./brand-logo.png',
  './apple-touch-icon-120.png','./apple-touch-icon-152.png','./apple-touch-icon-167.png',
  './ops-1075.css','./ops-1075.js','./integrate-1076.js','./settings-1078.js'
];

self.addEventListener('install',e=>e.waitUntil(
  caches.open(CACHE_NAME)
    .then(c=>Promise.allSettled(ASSETS.map(u=>c.add(u).catch(()=>null))))
    .then(()=>self.skipWaiting())
));

self.addEventListener('activate',e=>e.waitUntil((async()=>{
  const keys=await caches.keys();
  await Promise.all(keys.filter(k=>k!==CACHE_NAME).map(k=>caches.delete(k)));
  await self.clients.claim();
  const cs=await self.clients.matchAll({type:'window',includeUncontrolled:true});
  for(const c of cs){
    try{
      const u=new URL(c.url);
      if(u.origin===self.location.origin){
        u.searchParams.set('v','1078');
        await c.navigate(u.href);
      }
    }catch(_){ }
  }
})()));

function upgradeHtml(text){
  let t=text||'';
  t=t.replace(/name="app-build"\s+content="[^"]+"/,'name="app-build" content="2026-09-15-1078"');
  t=t.replace(/manifest\.json\?v=\d+/g,'manifest.json?v=1078');
  t=t.replace(/sw\.js\?v=\d+/g,'sw.js?v=1078');
  t=t.replace(/إصدار التطبيق\s*<bdi>\d+<\/bdi>/g,'إصدار التطبيق <bdi>1078</bdi>');
  const tag='<script src="settings-1078.js?v=1078"></script>';
  if(!t.includes('settings-1078.js')) t=t.replace('</body>',tag+'\n</body>');
  return t;
}

async function htmlResponse(r){
  if(!r)return r;
  try{
    const txt=upgradeHtml(await r.text());
    const h=new Headers(r.headers);
    h.set('content-type','text/html; charset=utf-8');
    h.set('cache-control','no-store, max-age=0, must-revalidate');
    h.delete('content-length');
    return new Response(txt,{status:r.status,statusText:r.statusText,headers:h});
  }catch(_){return r;}
}

self.addEventListener('fetch',e=>{
  if(e.request.method!=='GET')return;
  const url=e.request.url;
  if(!url.startsWith('http'))return;
  if(url.includes('api.anthropic.com')||url.includes('supabase.co')||url.includes('supabase.in'))return;
  const isHTML=e.request.headers.get('accept')?.includes('text/html');
  if(isHTML){
    e.respondWith((async()=>{
      try{
        const r=await fetch(e.request,{cache:'no-store'});
        const out=await htmlResponse(r);
        if(out&&out.ok)caches.open(CACHE_NAME).then(c=>c.put(e.request,out.clone()).catch(()=>{}));
        return out;
      }catch(_){
        const cached=await caches.match(e.request)||await caches.match('./index.html');
        return htmlResponse(cached);
      }
    })());
    return;
  }
  e.respondWith(fetch(e.request,{cache:'no-store'}).then(r=>{
    if(r&&r.ok)caches.open(CACHE_NAME).then(c=>c.put(e.request,r.clone()).catch(()=>{}));
    return r;
  }).catch(()=>caches.match(e.request)));
});

self.addEventListener('message',e=>{if(e.data?.type==='SKIP_WAITING')self.skipWaiting();});
console.log('✓ هدف التنمية إصدار 1078 — تحديث إجباري + إعدادات مرتبة');
