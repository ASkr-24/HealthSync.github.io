const CACHE_NAME = 'healthsync-v3';
const PRECACHE = [
  '/',
  '/index.html',
  '/styles.css',
  '/app.js',
  '/manifest.json',
  '/icon-192.png',
  '/icon-512.png',
  '/offline.html'
];

self.addEventListener('install', evt => {
  evt.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(PRECACHE)));
  self.skipWaiting();
});

self.addEventListener('activate', evt => {
  evt.waitUntil(caches.keys().then(keys => Promise.all(keys.map(k => { if (k !== CACHE_NAME) return caches.delete(k); }))));
  self.clients.claim();
});

self.addEventListener('fetch', evt => {
  const req = evt.request;
  if (req.method !== 'GET') return;
  if (req.mode === 'navigate') {
    evt.respondWith(fetch(req).then(res => { caches.open(CACHE_NAME).then(c => c.put(req, res.clone())); return res; }).catch(()=> caches.match('/offline.html')));
    return;
  }
  evt.respondWith(caches.match(req).then(cached => cached || fetch(req).then(net => { caches.open(CACHE_NAME).then(c=>c.put(req, net.clone())); return net; }).catch(()=> caches.match('/offline.html'))));
});
