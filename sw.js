// Service Worker - نظام هدف التنمية (إصدار 1077)
const CACHE_NAME = 'hadaf-1077';
const ASSETS = [
  './','./index.html','./manifest.json',
  './icon-192.png','./icon-512.png','./apple-touch-icon.png','./brand-logo.png',
  './apple-touch-icon-120.png','./apple-touch-icon-152.png','./apple-touch-icon-167.png',
  './ops-1075.css','./ops-1075.js','./integrate-1076.js'
];
self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE_NAME).then(c=>Promise.allSettled(ASSETS.map(u=>c.add(u).catch(()=>null)))).then(()=>self.skipWaiting())));
self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE_NAME).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',e=>{
  if(e.request.method!=='GET')return;
  const url=e.request.url;if(!url.startsWith('http'))return;
  if(url.includes('api.anthropic.com')||url.includes('supabase.co')||url.includes('supabase.in'))return;
  const html=e.request.headers.get('accept')?.includes('text/html');
  if(html){e.respondWith(fetch(e.request,{cache:'no-store'}).then(r=>{if(r&&r.status===200)caches.open(CACHE_NAME).then(c=>c.put(e.request,r.clone()).catch(()=>{}));return r;}).catch(()=>caches.match(e.request).then(r=>r||caches.match('./index.html'))));}
  else{e.respondWith(caches.match(e.request).then(cached=>{const net=fetch(e.request,{cache:'no-store'}).then(r=>{if(r&&r.status===200)caches.open(CACHE_NAME).then(c=>c.put(e.request,r.clone()).catch(()=>{}));return r;}).catch(()=>cached);return cached||net;}));}
});
self.addEventListener('message',e=>{if(e.data?.type==='SKIP_WAITING')self.skipWaiting();});
console.log('✓ هدف التنمية إصدار 1077 — واجهة مبسطة وشراء مباشر');
