/* Service worker: la interfaz y las lecciones visitadas quedan disponibles sin conexión (RNF09).
   Estrategia: red primero y respaldo en caché, tanto para los archivos de la interfaz como para
   las peticiones GET a la API. Así, cuando se publica una versión nueva, el navegador siempre la
   recibe completa (nunca mezcla un archivo nuevo con otro viejo) y la caché solo se usa sin internet. */
const VERSION = "aprendo-v31";
const ESTATICOS = ["/", "/index.html", "/css/estilos.css", "/js/api.js", "/js/app.js",
                   "/manifest.json", "/img/icono.svg"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(VERSION)
    .then(c => c.addAll(ESTATICOS.map(u => new Request(u, { cache: "reload" }))))
    .then(() => self.skipWaiting()));
});

self.addEventListener("activate", e => {
  e.waitUntil(caches.keys()
    .then(ks => Promise.all(ks.filter(k => k !== VERSION).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== location.origin) return;

  if (url.pathname.startsWith("/api/")) {
    if (url.pathname.startsWith("/api/certificados") || url.pathname.includes("/reportes/")) return;
    e.respondWith(
      fetch(req).then(r => {
        if (r.ok) { const copia = r.clone(); caches.open(VERSION).then(c => c.put(req, copia)); }
        return r;
      }).catch(() => caches.match(req).then(r => r || new Response(
        JSON.stringify({ detail: "Sin conexión. Esta página no se ha guardado todavía." }),
        { status: 503, headers: { "Content-Type": "application/json" } })))
    );
    return;
  }
  e.respondWith(
    fetch(req, { cache: "no-cache" }).then(r => {
      if (r.ok) { const copia = r.clone(); caches.open(VERSION).then(c => c.put(req, copia)); }
      return r;
    }).catch(() => caches.match(req, { ignoreSearch: true }).then(r => r || caches.match("/index.html")))
  );
});
