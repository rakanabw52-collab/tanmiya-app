// Service Worker - نظام هدف التنمية (إصدار 1059) - اسم الكاش يطابق رقم الإصدار
const CACHE_NAME = 'hadaf-1059';
const ASSETS = [
  './','./index.html','./manifest.json',
  './icon-192.png','./icon-512.png','./apple-touch-icon.png',
  './apple-touch-icon-120.png','./apple-touch-icon-152.png','./apple-touch-icon-167.png'
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME)
      .then(c => Promise.allSettled(ASSETS.map(u => c.add(u).catch(()=>null))))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k!==CACHE_NAME).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  if (e.request.method !== 'GET') return;
  const url = e.request.url;
  if (!url.startsWith('http')) return;
  // طلبات API ومزامنة Supabase: مباشرة للشبكة دائماً (بدون كاش)
  if (url.includes('api.anthropic.com') || url.includes('supabase.co') || url.includes('supabase.in')) {
    return; // اترك المتصفح يتعامل معها مباشرة
  }
  const isHTML = e.request.headers.get('accept')?.includes('text/html');
  if (isHTML) {
    e.respondWith(
      fetch(e.request, {cache:'no-store'})
        .then(r => {
          if (r && r.status===200) {
            const cl=r.clone();
            caches.open(CACHE_NAME).then(c=>c.put(e.request,cl).catch(()=>{}));
          }
          return r;
        })
        .catch(() => caches.match(e.request).then(r=>r||caches.match('./index.html')))
    );
  } else {
    e.respondWith(
      caches.match(e.request).then(cached => {
        if (cached) {
          fetch(e.request).then(fr=>{
            if(fr&&fr.status===200)caches.open(CACHE_NAME).then(c=>c.put(e.request,fr.clone()).catch(()=>{}));
          }).catch(()=>{});
          return cached;
        }
        return fetch(e.request).then(r=>{
          if(r&&r.status===200){const cl=r.clone();caches.open(CACHE_NAME).then(c=>c.put(e.request,cl).catch(()=>{}));}
          return r;
        });
      })
    );
  }
});

self.addEventListener('message', (e) => {
  if (e.data?.type==='SKIP_WAITING') self.skipWaiting();
});
console.log('✓ هدف التنمية إصدار 1059 (cloud sync ready)');
