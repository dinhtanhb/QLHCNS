/* Cache static assets only. Portal HTML and all business data stay network-only. */
const STATIC_CACHE = "ihrms-static-v28-dashboard-visual-20261015";
const PRECACHE_URLS = [
    "/static/manifest.json",
    "/static/css/tailwind.css",
    "/static/css/ihrms.css",
    "/static/css/design_tokens.css",
    "/static/css/ui_tokens.css",
    "/static/css/app_shell.css",
    "/static/css/ui_controls.css",
    "/static/css/shared_components.css",
    "/static/js/shared_components.js",
    "/static/js/ui_numbers.js",
    "/static/js/app_shell.js",
    "/static/css/theme.css",
    "/static/js/theme.js",
    "/static/img/ihrms-pwa-192.png",
    "/static/img/ihrms-pwa-512.png"
];

self.addEventListener("install", (event) => {
    event.waitUntil(
        caches.open(STATIC_CACHE).then((cache) => cache.addAll(PRECACHE_URLS))
    );
    self.skipWaiting();
});

self.addEventListener("activate", (event) => {
    event.waitUntil(
        caches.keys().then((keys) => Promise.all(
            keys.filter((key) => key.startsWith("ihrms-static-") && key !== STATIC_CACHE)
                .map((key) => caches.delete(key))
        )).then(() => self.clients.claim())
    );
});

self.addEventListener("fetch", (event) => {
    const request = event.request;
    const url = new URL(request.url);

    if (request.method !== "GET" || url.origin !== self.location.origin || !url.pathname.startsWith("/static/")) {
        return;
    }

    event.respondWith(
        caches.open(STATIC_CACHE).then(async (cache) => {
            const cached = await cache.match(request);
            if (cached) return cached;

            const response = await fetch(request);
            if (response.ok && (response.type === "basic" || response.type === "default")) {
                await cache.put(request, response.clone());
            }
            return response;
        })
    );
});
