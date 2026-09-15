// Service Worker - نظام هدف التنمية (إصدار 1078)
const CACHE_NAME = 'hadaf-1078';
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

self.addEventListener('activate',e=>e.waitUntil(
  caches.keys()
    .then(keys=>Promise.all(keys.filter(k=>k!==CACHE_NAME).map(k=>caches.delete(k))))
    .then(()=>self.clients.claim())
));

async function inject1078(response){
  if(!response)return response;
  try{
    const text=await response.text();
    const tag='<script src="settings-1078.js?v=1078"></script>';
    const out=text.includes('settings-1078.js')?text:text.replace('</body>',tag+'\n</body>');
    const h=new Headers(response.headers);h.set('content-type','text/html; charset=utf-8');
    h.delete('content-length');
    return new Response(out,{status:response.status,statusText:response.statusText,headers:h});
  }catch(e){return response;}
}

self.addEventListener('fetch',e=>{
  if(e.request.method!=='GET')return;
  const url=e.request.url;if(!url.startsWith('http'))return;
  if(url.includes('api.anthropic.com')||url.includes('supabase.co')||url.includes('supabase.in'))return;
  const html=e.request.headers.get('accept')?.includes('text/html');
  if(html){
    e.respondWith((async()=>{
      try{
        const r=await fetch(e.request,{cache:'no-store'});
        if(r&&r.status===200)caches.open(CACHE_NAME).then(c=>c.put(e.request,r.clone()).catch(()=>{}));
        return inject1078(r);
      }catch(err){
        const cached=await caches.match(e.request)||await caches.match('./index.html');
        return inject1078(cached);
      }
    })());
  }else{
    e.respondWith(caches.match(e.request).then(cached=>{
      const net=fetch(e.request,{cache:'no-store'}).then(r=>{
        if(r&&r.status===200)caches.open(CACHE_NAME).then(c=>c.put(e.request,r.clone()).catch(()=>{}));
        return r;
      }).catch(()=>cached);
      return cached||net;
    }));
  }
});

self.addEventListener('message',e=>{if(e.data?.type==='SKIP_WAITING')self.skipWaiting();});
console.log('✓ هدف التنمية إصدار 1078 — إعدادات مرتبة ومبسطة');
