const CACHE_NAME = 'luzcam-web-development';
const APP_SHELL = ['./index.html', './app.css', './app.js', './manifest.webmanifest'];

self.addEventListener('install', (event) => {
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE_NAME);
    await cache.addAll(APP_SHELL);
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter((key) => key.startsWith('luzcam-web-') && key !== CACHE_NAME).map((key) => caches.delete(key)));
    await self.clients.claim();
  })());
});

self.addEventListener('message', (event) => {
  if (event.data?.type !== 'CACHE_URLS' || !Array.isArray(event.data.urls)) return;
  const scope = new URL(self.registration.scope);
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE_NAME);
    let cached = 0;
    await Promise.all(event.data.urls.map(async (path) => {
      try {
        const url = new URL(path, scope);
        if (url.origin !== scope.origin || !url.pathname.startsWith(scope.pathname)) return;
        const response = await fetch(new Request(url.href, { cache: 'no-store' }));
        if (!response.ok || response.status !== 200) return;
        await cache.put(url.href, response.clone());
        cached++;
      } catch {}
    }));
    event.source?.postMessage({ type: 'CACHE_RESULT', cached });
  })());
});

self.addEventListener('fetch', (event) => {
  const request = event.request;
  if (request.method !== 'GET') return;
  const url = new URL(request.url);
  const scope = new URL(self.registration.scope);
  if (url.origin !== scope.origin || !url.pathname.startsWith(scope.pathname)) return;
  event.respondWith((async () => {
    const cache = await caches.open(CACHE_NAME);
    const cached = await cache.match(request, { ignoreSearch: true });
    if (cached) return cached;
    const response = await fetch(request);
    if (response.ok && response.status === 200 && !request.headers.has('range')) {
      await cache.put(request, response.clone());
    }
    return response;
  })());
});
