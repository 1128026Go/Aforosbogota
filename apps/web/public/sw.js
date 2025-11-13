// Minimal no-op service worker to avoid stale caches between deployments
self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    (async () => {
      const keys = await caches.keys();
      await Promise.all(keys.map((k) => caches.delete(k)));
      await self.clients.claim();
    })()
  );
});

self.addEventListener('fetch', (event) => {
  // Default to network-first; no caching to avoid serving outdated assets
  event.respondWith(fetch(event.request));
});
