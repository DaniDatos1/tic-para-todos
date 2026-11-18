/* TIC para Todos - aplicación de una sola página (vanilla JS, sin frameworks). */
(() => {
  const $ = s => document.querySelector(s);
  const main = $("#contenido");
  const esc = t => String(t ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  let ayudaActual = "";

  /* ---------------- Accesibilidad (RF12) ---------------- */
  const pref = (() => { try { return JSON.parse(localStorage.getItem("aprendo_pref")) || {}; } catch { return {}; } })();
  function guardarPref() { try { localStorage.setItem("aprendo_pref", JSON.stringify(pref)); } catch { /* */ } }
  function aplicarPref() {
    document.documentElement.style.setProperty("--escala", pref.escala || 1);
    document.documentElement.classList.toggle("contraste", !!pref.contraste);
    $("#btn-contraste").setAttribute("aria-pressed", String(!!pref.contraste));
    const grande = (pref.escala || 1) > 1.2;
    $("#btn-letra").textContent = grande ? "A-" : "A+";
    $("#btn-letra").setAttribute("aria-label", grande ? "A- reducir tamaño de letra" : "A+ aumentar tamaño de letra");
  }
  $("#btn-letra").onclick = () => {
    const pasos = [1, 1.15, 1.3];
    pref.escala = pasos[(pasos.indexOf(pref.escala || 1) + 1) % pasos.length];
    guardarPref(); aplicarPref();
  };
  $("#btn-contraste").onclick = () => { pref.contraste = !pref.contraste; guardarPref(); aplicarPref(); };
  aplicarPref();

  function hablar(texto) {
    if (!("speechSynthesis" in window)) { aviso("Su navegador no puede leer en voz alta."); return; }
    speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(texto);
    u.lang = "es-CO"; u.rate = 0.9;
    const voz = speechSynthesis.getVoices().find(v => v.lang.startsWith("es"));
    if (voz) u.voice = voz;
    speechSynthesis.speak(u);
  }

  /* ---------------- Utilidades de interfaz ---------------- */
  let tAviso;
  function aviso(msg) {
    const a = $("#aviso"); a.textContent = msg; a.classList.remove("oculto");
    clearTimeout(tAviso); tAviso = setTimeout(() => a.classList.add("oculto"), 3500);
  }
  /* Copia el texto de cada encabezado de tabla a sus celdas (data-label) para que,
     en pantallas pequeñas, cada fila se muestre como una tarjeta legible. */
  function etiquetarTablas() {
    main.querySelectorAll("table").forEach(t => {
      const cab = [...t.querySelectorAll("thead th")].map(th => th.textContent.trim());
      t.classList.add("tabla-responsive");
      t.querySelectorAll("tbody tr").forEach(tr =>
        [...tr.children].forEach((td, i) => {
          if (cab[i]) td.dataset.label = cab[i];
          td.innerHTML = `<div class="celda">${td.innerHTML}</div>`;
        }));
    });
  }

  /* ---------------- Navegación: menú lateral (computador) y menú ☰ (celular) ---------------- */
  const NAV = {
    inicio: '<path d="M3 11l9-7 9 7v9a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"/>',
    progreso: '<path d="M5 20V11M12 20V5M19 20v-6" stroke-width="3"/>',
    cert: '<circle cx="12" cy="9" r="5"/><path d="M9 13.5L7.5 21l4.5-2.5 4.5 2.5-1.5-7.5"/>',
    prueba: '<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M9 8h6M9 12h6M9 16h3"/>',
    guardar: '<path d="M5 3h11l3 3v15H5z"/><path d="M8 3v5h7V3M8 21v-7h8v7"/>',
    grupo: '<circle cx="9" cy="9" r="3.2"/><circle cx="17" cy="10" r="2.6"/><path d="M3 20a6 6 0 0 1 12 0M14.5 20a4.5 4.5 0 0 1 7-3.7"/>',
    admin: '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M4.9 19.1L7 17M17 7l2.1-2.1"/>',
    ayuda: '<circle cx="12" cy="12" r="9"/><path d="M9.5 9.5a2.5 2.5 0 1 1 3.5 2.3c-.6.3-1 .9-1 1.6v.6"/><circle cx="12" cy="17.2" r=".6" fill="currentColor"/>',
    salir: '<path d="M14 4h5v16h-5M10 8l-4 4 4 4M6 12h10"/>',
  };
  const icoNav = k => `<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${NAV[k]}</svg>`;
  function opcionesMenu(s) {
    const op = [["#rutas", "inicio", "Inicio"], ["#progreso", "progreso", "Mi progreso"],
                ["#certificados", "cert", "Mis certificados"], ["#diagnostico", "prueba", "Prueba inicial"]];
    if (s && s.usuario.invitado) op.push(["#registro", "guardar", "Guardar mi avance"]);
    if (s && ["facilitador", "administrador"].includes(s.usuario.rol)) op.push(["#facilitador", "grupo", "Mis grupos"]);
    if (s && s.usuario.rol === "administrador") op.push(["#admin", "admin", "Administrar"]);
    op.push(["ayuda", "ayuda", "Ayuda"], ["#salir", "salir", "Salir"]);
    return op;
  }
  const CATEDRAL = `<svg class="ilus-catedral" viewBox="0 0 200 150" aria-hidden="true">
    <rect x="0" y="128" width="200" height="22" fill="#2B5FA6"/>
    <circle cx="28" cy="112" r="20" fill="#3F8F4E"/><circle cx="176" cy="110" r="22" fill="#3F8F4E"/>
    <rect x="62" y="70" width="76" height="60" fill="#F4E9D8"/><path d="M58 72l42-22 42 22z" fill="#E7D3B5"/>
    <rect x="86" y="18" width="28" height="112" fill="#FBF3E6"/><path d="M84 20l16-14 16 14z" fill="#E7D3B5"/>
    <rect x="98" y="0" width="4" height="10" fill="#E7D3B5"/><rect x="94" y="4" width="12" height="3" fill="#E7D3B5"/>
    <rect x="94" y="34" width="12" height="16" rx="6" fill="#1F4E8C"/><rect x="94" y="62" width="12" height="16" rx="6" fill="#1F4E8C"/>
    <path d="M90 130v-22a10 10 0 0 1 20 0v22z" fill="#8A5A2B"/>
    <rect x="70" y="86" width="9" height="14" rx="4.5" fill="#1F4E8C"/><rect x="121" y="86" width="9" height="14" rx="4.5" fill="#1F4E8C"/>
  </svg>`;
  function dibujarLateral() {
    const s = API.sesion(), nav = $("#lateral");
    document.body.classList.toggle("con-sesion", !!s);
    if (!s) { nav.innerHTML = ""; $("#usuario-chip").classList.add("oculto"); return; }
    const ruta = (location.hash.slice(1) || "").split("/")[0];
    const activa = ["rutas", "modulo", "leccion", ""].includes(ruta) ? "#rutas" : "#" + ruta;
    nav.innerHTML = `<ul>${opcionesMenu(s).map(([h, ico, t]) => `<li><button data-ir="${h}" class="${h === activa ? "activa" : ""}"
      ${h === activa ? 'aria-current="page"' : ""}>${icoNav(ico)}<span>${t}</span></button></li>`).join("")}</ul>
      <div class="lateral-pie"><img class="foto-lateral" src="img/valledupar-plaza.jpg" alt="Plaza de Valledupar con la torre de la iglesia al fondo" width="399" height="501" loading="lazy"><p><strong>Valledupar</strong> se conecta con el conocimiento</p></div>`;
    nav.querySelectorAll("[data-ir]").forEach(b => b.onclick = () => irA(b.dataset.ir));
    const nombre = s.usuario.invitado ? "Invitado" : s.usuario.nombre.split(" ").slice(0, 2).join(" ");
    const chip = $("#usuario-chip");
    chip.innerHTML = `<span class="avatar" aria-hidden="true">${esc(nombre.charAt(0).toUpperCase())}</span><span class="nombre">${esc(nombre)}</span>`;
    chip.classList.remove("oculto");
  }
  function irA(destino) {
    if (destino === "ayuda") { $("#btn-ayuda").click(); return; }
    location.hash = destino;
  }

  function pantalla(titulo, html, { atras = null, ayuda = "", ancho = "normal", textoAtras = "Volver" } = {}) {
    document.body.dataset.ancho = ancho;   // estrecho | normal | ancho
    document.body.classList.remove("en-paso");
    dibujarLateral();
    if (atras && API.sesion()) html = `<button class="volver" data-volver="${esc(atras)}">${'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 5l-7 7 7 7" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></svg>'} ${esc(textoAtras)}</button>` + html;
    if ("speechSynthesis" in window) speechSynthesis.cancel();
    $("#titulo-barra").textContent = titulo;
    document.title = titulo + " · TIC para Todos";
    const b = $("#btn-atras");
    b.classList.toggle("oculto", !atras);
    b.onclick = () => { location.hash = atras; };
    $("#btn-menu").classList.toggle("oculto", !API.sesion());
    $("#menu").classList.add("oculto");
    ayudaActual = ayuda;
    main.innerHTML = html;
    const v = main.querySelector("[data-volver]");
    if (v) v.onclick = () => { location.hash = v.dataset.volver; };
    etiquetarTablas();
    main.focus({ preventScroll: true });
    window.scrollTo({ top: 0, left: 0, behavior: "instant" });
  }
  const cargando = () => { main.innerHTML = '<p class="cargando">Cargando…</p>'; };
  function barra(p) { return `<div class="barra-progreso" aria-hidden="true"><span style="width:${p}%"></span></div>`; }
  function errorEn(sel, e) { const el = $(sel); if (el) el.textContent = e.message; else aviso(e.message); }

  /* ---------------- Ayuda contextual (RF14) ---------------- */
  const dlg = $("#dlg-ayuda");
  $("#btn-ayuda").onclick = () => { $("#ayuda-texto").textContent = ayudaActual || "Toque los botones grandes para avanzar."; dlg.showModal(); };
  $("#ayuda-cerrar").onclick = () => dlg.close();
  $("#ayuda-escuchar").onclick = () => hablar($("#ayuda-texto").textContent);

  /* ---------------- Menú ---------------- */
  $("#btn-menu").onclick = () => {
    const m = $("#menu"), abierto = m.classList.toggle("oculto") === false;
    $("#btn-menu").setAttribute("aria-expanded", String(abierto));
    if (!abierto) return;
    m.innerHTML = opcionesMenu(API.sesion()).map(([h, ico, t]) => `<button data-ir="${h}">${icoNav(ico)} ${t}</button>`).join("");
    m.querySelectorAll("button").forEach(b => b.onclick = () => { m.classList.add("oculto"); irA(b.dataset.ir); });
  };

  /* ================= VISTAS ================= */

  /* RF02: inicio de sesión */
  function vLogin() {
    pantalla("TIC para Todos", `
      <div class="acceso">
      <aside class="acceso-hero">
        <p class="acceso-marca">TIC para Todos · Valledupar – Cesar</p>
        <h2>Aprenda tecnología paso a paso, a su ritmo</h2>
        <p>Lecciones cortas y con audio para usar el celular y el computador en el estudio, el trabajo y los trámites.</p>
        <ul>
          <li><span aria-hidden="true">📱</span> Practique en el celular o en el computador</li>
          <li><span aria-hidden="true">🔊</span> Escuche cada paso en voz alta</li>
          <li><span aria-hidden="true">✅</span> Preguntas que le explican sus errores</li>
          <li><span aria-hidden="true">🏅</span> Certificado al terminar cada módulo</li>
        </ul>
      </aside>
      <div class="acceso-form">
      <div class="bienvenida">
        <img class="logo-acceso" src="img/icono.svg" alt="" width="84" height="84">
        <h2>${API.invitado() ? "¡Qué bueno verlo de nuevo!" : "¡Bienvenido!"}</h2>
        <p class="suave">Aprenda a usar la tecnología paso a paso</p>
      </div>
      <button class="btn btn-grande" id="entrar-invitado">${API.invitado() ? "Seguir aprendiendo" : "Empezar ahora"} ${ICO.der}</button>
      <p class="nota-invitado">${API.invitado()
        ? "Seguirá con el avance guardado en este dispositivo."
        : "No necesita registrarse ni dar sus datos. Su avance se guarda en este dispositivo."}</p>
      <p class="error" id="err-inv" role="alert"></p>
      <details class="acceso-cuenta" id="acceso-cuenta">
        <summary>Ya tengo cuenta: entrar con mi celular</summary>
      <form id="f-login" novalidate>
        <label for="celular">Número de celular</label>
        <input id="celular" inputmode="numeric" autocomplete="tel" maxlength="10" placeholder="300 000 0000" required>
        <label for="pin">PIN de 4 números</label>
        <input id="pin" class="pin" type="password" inputmode="numeric" maxlength="4" autocomplete="current-password" placeholder="••••" required>
        <p class="error" id="err" role="alert"></p>
        <button class="btn" type="submit">Entrar</button>
      </form>
        <p class="suave">¿Olvidó su PIN? Pídale a su facilitador que se lo cambie.</p>
      </details>
      <p style="text-align:center"><button class="enlace" id="escuchar">🔊 Escuchar instrucciones</button></p>
      </div></div>`, { ayuda: "Toque Empezar ahora para entrar sin registrarse. Si ya tiene una cuenta o es facilitador, toque Ya tengo cuenta y escriba su celular y su PIN.", ancho: "acceso" });
    $("#escuchar").onclick = () => hablar("Bienvenido a TIC para Todos. Para empezar, toque el botón azul Empezar ahora. No necesita registrarse. Si ya tiene una cuenta, toque Ya tengo cuenta y escriba su celular y su PIN.");
    $("#entrar-invitado").onclick = async () => {
      const b = $("#entrar-invitado"); b.disabled = true;
      try { await API.entrarInvitado(); location.hash = "#rutas"; }
      catch (err) { errorEn("#err-inv", err); b.disabled = false; }
    };
    $("#f-login").onsubmit = async e => {
      e.preventDefault();
      try {
        const s = await API.post("/api/auth/login", { celular: $("#celular").value.replace(/\D/g, ""), pin: $("#pin").value });
        API.guardarSesion(s);
        location.hash = s.usuario.rol === "aprendiz" ? "#rutas" : (s.usuario.rol === "administrador" ? "#admin" : "#facilitador");
      } catch (err) { errorEn("#err", err); }
    };
  }

  /* RF01 + RF13: registro con consentimiento */
  function vRegistro() {
    const guardar = !!(API.sesion() && API.sesion().usuario.invitado);
    pantalla(guardar ? "Guardar mi avance" : "Registrarme", `
      <h2>${guardar ? "Guarde su avance" : "Cree su cuenta"}</h2>
      <p class="suave">${guardar
        ? "Así podrá seguir desde otro celular o computador y recibir sus certificados con su nombre. No pierde nada de lo que ya hizo."
        : "No necesita correo electrónico."}</p>
      <form id="f-reg" novalidate>
        <label for="nombre">Su nombre</label>
        <input id="nombre" autocomplete="name" maxlength="80" required>
        <label for="celular">Número de celular</label>
        <input id="celular" inputmode="numeric" autocomplete="tel" maxlength="10" placeholder="300 000 0000" required>
        <label for="pin">Invente un PIN de 4 números</label>
        <input id="pin" class="pin" type="password" inputmode="numeric" maxlength="4" autocomplete="new-password" required>
        <div class="tarjeta">
          <strong>Tratamiento de sus datos</strong>
          <p class="suave">Sus datos (nombre y celular) se usan solo para guardar su avance y entregarle certificados,
          dentro de un proyecto académico de la UNAD. No se comparten con terceros. Puede pedir que se borren en cualquier
          momento. (Ley 1581 de 2012)</p>
          <button type="button" class="enlace" id="leer-cons">🔊 Escuchar</button>
          <label class="check"><input type="checkbox" id="acepta"> Acepto el tratamiento de mis datos</label>
        </div>
        <p class="error" id="err" role="alert"></p>
        <button class="btn" type="submit">${guardar ? "Guardar mi avance" : "Crear mi cuenta"}</button>
      </form>`, { atras: guardar ? "#rutas" : "#login", ayuda: "Escriba su nombre, su celular y un PIN de 4 números fácil de recordar. Lea el aviso de datos, marque la casilla y toque Crear mi cuenta.", ancho: "estrecho" });
    $("#leer-cons").onclick = () => hablar("Sus datos, nombre y celular, se usan solo para guardar su avance y entregarle certificados. No se comparten con nadie. Puede pedir que se borren en cualquier momento.");
    $("#f-reg").onsubmit = async e => {
      e.preventDefault();
      if (!$("#acepta").checked) { $("#err").textContent = "Debe aceptar el tratamiento de datos para continuar."; return; }
      try {
        const s = await API.post(guardar ? "/api/auth/guardar-avance" : "/api/auth/registro", {
          nombre: $("#nombre").value, celular: $("#celular").value.replace(/\D/g, ""),
          pin: $("#pin").value, acepta_datos: true });
        API.guardarSesion(s);
        if (guardar) { API.guardarInvitado(null); aviso("¡Listo! Su avance quedó guardado. Desde ahora entre con su celular y su PIN."); location.hash = "#rutas"; }
        else location.hash = "#diagnostico";
      } catch (err) { errorEn("#err", err); }
    };
  }

  /* RF03: prueba diagnóstica */
  async function vDiagnostico() {
    cargando();
    const preguntas = await API.get("/api/diagnostico/preguntas");
    const opts = [[2, "✅ Sí, lo hago solo"], [1, "🤝 Con ayuda"], [0, "❌ No sé"]];
    pantalla("Prueba inicial", `
      <h2>Cuéntenos qué sabe hacer</h2>
      <p class="suave">Son 10 preguntas. Así le recomendamos por dónde empezar.</p>
      <form id="f-diag">
        <div class="rejilla-2">${preguntas.map((p, i) => `
          <fieldset class="tarjeta" style="border:2px solid var(--borde)">
            <legend><strong>${i + 1}. ${esc(p.texto)}</strong></legend>
            ${opts.map(([v, t]) => `<label class="check"><input type="radio" name="p${p.id}" value="${v}" required> ${t}</label>`).join("")}
          </fieldset>`).join("")}</div>
        <p class="error" id="err" role="alert"></p>
        <button class="btn btn-ancho-auto" type="submit">Ver mi recomendación</button>
      </form>
      <button class="enlace" onclick="location.hash='#rutas'">Saltar por ahora</button>`,
      { ayuda: "Para cada pregunta, escoja si lo hace solo, con ayuda o si no sabe. No hay respuestas malas." });
    $("#f-diag").onsubmit = async e => {
      e.preventDefault();
      const respuestas = {};
      for (const p of preguntas) {
        const m = document.querySelector(`input[name=p${p.id}]:checked`);
        if (!m) { $("#err").textContent = "Le falta responder la pregunta " + (preguntas.indexOf(p) + 1) + "."; return; }
        respuestas[p.id] = Number(m.value);
      }
      try {
        const r = await API.post("/api/diagnostico", { respuestas });
        pantalla("Su recomendación", `
          <div class="bienvenida"><div class="logo" aria-hidden="true">${esc(r.modulo_recomendado.icono)}</div>
          <h2>Le recomendamos empezar por:</h2>
          <p style="font-size:1.3rem"><strong>${esc(r.modulo_recomendado.titulo)}</strong></p>
          <p class="suave">Su resultado: ${r.puntaje} de 100</p></div>
          <button class="btn" onclick="location.hash='#modulo/${r.modulo_recomendado.id}'">Empezar</button>
          <button class="btn btn-sec" onclick="location.hash='#rutas'">Ver todas las rutas</button>`);
      } catch (err) { errorEn("#err", err); }
    };
  }

  /* RF04: inicio con banner, módulos por color y progreso */
  const BANNER = `<img class="banner-ilus banner-foto" src="img/banner-640.jpg"
    srcset="img/banner-640.jpg 640w, img/banner-1200.jpg 1200w" sizes="(min-width: 768px) 55vw, 100vw"
    alt="Una señora y un joven sonríen mientras miran un celular en una plaza de Valledupar" width="1200" height="800">`;
  const colorModulo = orden => "mod-c" + (((Number(orden) || 1) - 1) % 4 + 1);

  async function vRutas() {
    cargando();
    const r = await API.get("/api/rutas");
    const s = API.sesion();
    const inv = s.usuario.invitado;
    const nombre = inv ? "" : s.usuario.nombre.split(" ")[0];
    const hechas = r.modulos.reduce((a, m) => a + (m.avance ? m.avance.completadas : 0), 0);
    const totalL = r.modulos.reduce((a, m) => a + m.num_lecciones, 0);
    const pctG = totalL ? Math.round(100 * hechas / totalL) : 0;
    const modsHechos = r.modulos.filter(m => m.avance && m.avance.terminado).length;
    const ul = r.ultima_leccion;
    pantalla(inv ? "Inicio" : "Hola, " + nombre, `
      <section class="banner">
        <div class="banner-texto">
          <p class="banner-saludo">${inv ? "¡Hola! Bienvenido" : "¡Hola, " + esc(nombre) + "!"}</p>
          <h2>Fortaleciendo sus competencias TIC</h2>
          <p class="banner-pastilla">para una vida con más oportunidades</p>
        </div>
        ${BANNER}
      </section>
      ${inv && hechas ? `<div class="aviso-invitado"><span>Está aprendiendo como invitado. Guarde su avance para no perderlo y recibir sus certificados.</span>
        <button class="btn btn-sec" onclick="location.hash='#registro'">💾 Guardar mi avance</button></div>` : ""}
      <h2 class="titulo-seccion"><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="3" width="8" height="8" rx="2"/><rect x="13" y="3" width="8" height="8" rx="2"/><rect x="3" y="13" width="8" height="8" rx="2"/><rect x="13" y="13" width="8" height="8" rx="2"/></svg> Sus módulos</h2>
      <div class="modulos-color">${r.modulos.map(m => `
        <button class="tarjeta-color ${colorModulo(m.orden)}" onclick="location.hash='#modulo/${m.id}'">
          <span class="tc-ico" aria-hidden="true">${esc(m.icono)}</span>
          <span class="tc-texto">
            <strong>${m.orden}. ${esc(m.titulo)}</strong>
            <span>${m.num_lecciones} lecciones · ${m.avance.porcentaje}% completado</span>
            <span class="tc-barra" aria-hidden="true"><span style="width:${m.avance.porcentaje}%"></span></span>
            ${m.id === r.recomendado_id ? '<span class="tc-rec">⭐ Recomendado para usted</span>' : ""}
          </span>
          <span class="tc-flecha" aria-hidden="true">${ICO.der}</span>
        </button>`).join("")}</div>
      <div class="inicio-inferior">
        <div class="inicio-col">
          ${ul ? `<div class="tarjeta continuar ${colorModulo(ul.modulo_orden)}">
              <p class="etq-modulo">Continuar donde iba</p>
              <h3>${esc(ul.titulo)}</h3>
              <p class="suave">${esc(ul.modulo_titulo)}</p>
              <button class="btn btn-ancho-auto" onclick="location.hash='#leccion/${ul.id}'">Continuar la lección ${ICO.der}</button>
            </div>` : `<div class="tarjeta continuar mod-c1">
              <p class="etq-modulo">Para empezar</p>
              <h3>Elija un módulo y empiece por la primera lección</h3>
              <p class="suave">Cada lección tiene 5 pasos cortos, con audio, y 2 preguntas para practicar.</p>
            </div>`}
          ${!r.hizo_diagnostico ? `<button class="tarjeta tarjeta-accion" onclick="location.hash='#diagnostico'">
              <span class="ta-ico" aria-hidden="true">📝</span>
              <span><strong>Hacer la prueba inicial</strong><span class="suave">10 preguntas para saber por dónde le conviene empezar</span></span>
              <span class="tc-flecha" aria-hidden="true">${ICO.der}</span></button>` : ""}
        </div>
        <aside class="tarjeta progreso-mini" aria-label="Su progreso">
          <h3>Su progreso</h3>
          <div class="pm-fila">
            <div class="anillo pequeno" style="--p:${pctG}" role="img" aria-label="Avance total ${pctG} por ciento"><span>${pctG}%</span></div>
            <p><strong>${hechas} de ${totalL}</strong> lecciones<br><span class="suave">${modsHechos} de ${r.modulos.length} módulos completados</span></p>
          </div>
          <div class="pm-animo"><span aria-hidden="true">🏆</span><span><strong>${hechas ? "¡Vamos bien!" : "¡Usted puede!"}</strong>
            ${modsHechos ? "Ya puede descargar su certificado." : "Termine un módulo para recibir su certificado."}</span></div>
          <button class="btn btn-sec" onclick="location.hash='#progreso'">Ver mi progreso</button>
        </aside>
      </div>`,
      { ayuda: "Toque un módulo para ver sus lecciones. Con Continuar la lección vuelve a la última lección que abrió." });
  }

  /* RF08: certificados */
  async function vCertificados() {
    cargando();
    const p = await API.get("/api/progreso");
    const inv = API.sesion().usuario.invitado;
    pantalla("Mis certificados", `
      <h2>Mis certificados</h2>
      <p class="suave">Al terminar todas las lecciones de un módulo recibe un certificado en PDF con su nombre.</p>
      ${inv ? `<div class="aviso-invitado"><span>Para recibir certificados con su nombre, primero guarde su avance.</span>
        <button class="btn btn-sec" onclick="location.hash='#registro'">💾 Guardar mi avance</button></div>` : ""}
      <div class="lista-certificados">${p.modulos.map(m => `
        <div class="tarjeta certificado ${colorModulo(m.orden)} ${m.terminado ? "listo" : ""}">
          <span class="cert-ico" aria-hidden="true">${m.terminado ? "🏅" : esc(m.icono)}</span>
          <div class="cert-texto">
            <h3>${esc(m.titulo)}</h3>
            <p class="suave">${m.terminado ? "¡Módulo terminado!" : `Le faltan ${m.total - m.completadas} de ${m.total} lecciones`}</p>
            ${m.terminado ? "" : barra(m.porcentaje)}
          </div>
          ${m.terminado
            ? (inv ? `<button class="btn btn-ancho-auto" onclick="location.hash='#registro'">Guardar avance</button>`
                   : `<button class="btn btn-ancho-auto" data-cert="${m.modulo_id}">Descargar PDF</button>`)
            : `<button class="btn btn-sec btn-ancho-auto" onclick="location.hash='#modulo/${m.modulo_id}'">Ir al módulo</button>`}
        </div>`).join("")}</div>`,
      { atras: "#rutas", textoAtras: "Volver al inicio", ayuda: "Aquí están sus certificados. Cuando termine un módulo, toque Descargar PDF." });
    document.querySelectorAll("[data-cert]").forEach(b => b.onclick = async () => {
      try { await API.descargar(`/api/certificados/${b.dataset.cert}`, `certificado_modulo_${b.dataset.cert}.pdf`); aviso("Certificado descargado."); }
      catch (e) { aviso(e.message); }
    });
  }

  async function vModulo(id) {
    cargando();
    const m = await API.get("/api/modulos/" + id);
    const hechasM = m.lecciones.filter(l => l.completada).length;
    const pctM = m.lecciones.length ? Math.round(100 * hechasM / m.lecciones.length) : 0;
    const sigL = m.lecciones.find(l => !l.completada);
    pantalla(m.titulo, `
      <section class="modulo-hero ${colorModulo(m.orden)}">
        <span class="icono-circulo grande" aria-hidden="true">${esc(m.icono)}</span>
        <div class="modulo-hero-texto">
          <p class="etq-modulo">Módulo ${m.orden}</p>
          <h2>${esc(m.titulo)}</h2>
          <p>${esc(m.descripcion)}</p>
          <p class="suave">${hechasM} de ${m.lecciones.length} lecciones completadas</p>
          ${barra(pctM)}
        </div>
        ${sigL ? `<button class="btn btn-ancho-auto" onclick="location.hash='#leccion/${sigL.id}'">${hechasM ? "Seguir con la lección " + sigL.orden : "Empezar el módulo"} ${ICO.der}</button>` : ""}
      </section>
      <h2>Lecciones</h2>
      <div class="lista-lecciones ${colorModulo(m.orden)}">${m.lecciones.map(l => `
        <button class="tarjeta-leccion ${l.completada ? "hecha" : ""}" onclick="location.hash='#leccion/${l.id}'">
          <span class="num-leccion" aria-hidden="true">${l.completada ? "✓" : l.orden}</span>
          <span class="info-leccion">
            <strong>${l.orden}. ${esc(l.titulo)}</strong>
            <span class="suave">${esc(l.para_que || "")}</span>
            <span class="chips-leccion">
              <span class="chip">${l.dispositivo === "computador" ? "💻 En el computador" : "📱 En el celular"}</span>
              ${l.completada ? '<span class="chip chip-ok">Completada</span>' : ""}
            </span>
          </span>
          <span class="flecha-leccion" aria-hidden="true">${ICO.der}</span>
        </button>`).join("")}</div>`,
      { atras: "#rutas", textoAtras: "Volver al inicio", ayuda: "Toque una lección para empezarla. Las lecciones con ✔️ ya las completó." });
  }

  /* RF05 + RF06: lección con pasos, audio y actividad */
  const ICO = {
    voz: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 9v6h4l5 4V5L8 9H4z" fill="currentColor"/><path d="M16 8.5a5 5 0 0 1 0 7M18.5 6a8.5 8.5 0 0 1 0 12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
    izq: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 5l-7 7 7 7" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    der: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 5l7 7-7 7" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    ok: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    x: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 7l10 10M17 7L7 17" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"/></svg>',
    diana: '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="12" r="5" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="12" r="1.6" fill="currentColor"/></svg>',
    reloj: '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="2"/><path d="M12 7v5l3 2" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
    lista: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 6h11M9 12h11M9 18h11" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><circle cx="4.5" cy="6" r="1.5" fill="currentColor"/><circle cx="4.5" cy="12" r="1.5" fill="currentColor"/><circle cx="4.5" cy="18" r="1.5" fill="currentColor"/></svg>',
    foco: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-3.6 10.8c.6.5 1 1.2 1 2V16h5.2v-.2c0-.8.4-1.5 1-2A6 6 0 0 0 12 3z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg>',
    persona: '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="8" r="4" fill="none" stroke="currentColor" stroke-width="2"/><path d="M4 21a8 8 0 0 1 16 0" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
    libro: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2V5z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/><path d="M4 19a2 2 0 0 1 2-2h13" fill="none" stroke="currentColor" stroke-width="2"/></svg>',
    repetir: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 12a8 8 0 1 0 2.4-5.7M4 4v4h4" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  };
  const mezclar = arr => {   // orden aleatorio de las opciones (Fisher-Yates)
    const a = [...arr];
    for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; }
    return a;
  };
  const resumen = t => {
    let f = String(t).split(/(?<=\.)\s/)[0];
    if (f.length > 80) f = f.slice(0, 80).replace(/\s+\S*$/, "") + "…";
    return f;
  };

  async function vLeccion(id) {
    cargando();
    const l = await API.get("/api/lecciones/" + id);
    const total = l.pasos.length;
    const act = l.actividades[0];
    const minutos = Math.max(2, Math.round((total * 35 + l.actividades.length * 45) / 60));
    let mod = null;
    try { mod = await API.get("/api/modulos/" + l.modulo_id); } catch { /* opcional */ }
    // estado: -1 = inicio, 0..total-1 = pasos, total = práctica, total+1 = completada
    let paso = -1;
    let pregunta = 0;   // índice de la pregunta de práctica actual
    const acts = l.actividades;

    function stepper() {
      const etapas = [...l.pasos.map((_, i) => ({ n: i + 1, t: "Paso " + (i + 1) })), { n: "✓", t: "Práctica" }];
      return `<ol class="stepper" aria-label="Avance de la lección">${etapas.map((e, i) => {
        const estado = i < paso ? "hecho" : i === paso ? "actual" : "";
        return `<li class="${estado}" ${i === paso ? 'aria-current="step"' : ""}><span class="punto">${i < paso ? ICO.ok : e.n}</span><span class="etq">${e.t}</span></li>`;
      }).join("")}</ol>`;
    }

    function encabezado(conStepper = true) {
      return `<div class="lec-cab">
        <span class="chip-modulo">${esc(mod ? mod.icono : "📘")} ${esc(l.modulo_titulo)} · Lección ${l.posicion} de ${l.total}</span>
        <h2 class="lec-titulo">${esc(l.titulo)}</h2>
        ${conStepper ? `<p class="lec-subtitulo">Siga los ${total} pasos ${l.dispositivo === "computador" ? "en el computador" : "en su celular"}.</p>` + stepper() : ""}
      </div>`;
    }

    /* Paneles laterales de la lección (solo en pantallas grandes) */
    function panelIzquierdo() {
      return `<aside class="lec-panel lec-izq" aria-label="Contexto de la lección">
        ${l.situacion ? `<section class="panel-situacion">
          <span class="panel-etq">Situación real</span>
          <div class="panel-ilus" aria-hidden="true">${esc(l.pasos[0] ? l.pasos[0].icono : "📘")}</div>
          <p>${esc(l.situacion)}</p>
          <button class="btn btn-pequeno" data-leer-sit>${ICO.voz} Escuchar la historia</button>
        </section>` : ""}
        <section class="panel-objetivo">
          <h3>${ICO.diana} ¿Para qué le sirve?</h3>
          <p>${esc(l.para_que)}</p>
          <p class="panel-meta">${ICO.reloj} Duración aproximada: <strong>${minutos} min</strong></p>
        </section>
      </aside>`;
    }
    function panelDerecho() {
      const lecs = mod ? mod.lecciones : [];
      const hechas = lecs.filter(x => x.completada).length;
      const pct = lecs.length ? Math.round(100 * hechas / lecs.length) : 0;
      return `<aside class="lec-panel lec-der" aria-label="Apoyo de la lección">
        <section class="tarjeta progreso-mini">
          <h3>Su progreso</h3>
          <div class="pm-fila">
            <div class="anillo pequeno" style="--p:${pct}" role="img" aria-label="Avance del módulo ${pct} por ciento"><span>${pct}%</span></div>
            <p><strong>${hechas} de ${lecs.length}</strong> lecciones del módulo</p>
          </div>
          <div class="pm-animo"><span aria-hidden="true">🏆</span><span><strong>${hechas ? "¡Vamos bien!" : "¡Usted puede!"}</strong> Siga aprendiendo para descargar su certificado.</span></div>
        </section>
        ${l.glosario.length ? `<details class="tarjeta panel-lista" open><summary>${ICO.libro} Palabras clave</summary>
          <dl>${l.glosario.map(g => `<div><dt>${esc(g.termino)}:</dt> <dd>${esc(g.definicion)}</dd></div>`).join("")}</dl></details>` : ""}
        ${l.recuerde.length ? `<details class="tarjeta panel-lista" open><summary><span aria-hidden="true">⭐</span> Recuerde</summary>
          <ul class="panel-recuerde">${l.recuerde.map(r => `<li>${ICO.ok}<span>${esc(r)}</span></li>`).join("")}</ul></details>` : ""}
      </aside>`;
    }

    function vistaInicio() {
      return `${encabezado(false)}
        <div class="lec-inicio">
          <div class="lec-hero" aria-hidden="true"><span>${esc(l.pasos[0] ? l.pasos[0].icono : "📘")}</span></div>
          <div>
            ${l.situacion ? `<div class="lec-situacion"><span class="ico-circ ico-azul">${ICO.persona}</span>
              <div><strong>Una situación de la vida real</strong><p>${esc(l.situacion)}</p></div>
              <button class="btn-icono" id="leer-sit" aria-label="Escuchar la situación">${ICO.voz}</button></div>` : ""}
            <div class="lec-objetivo"><span class="ico-circ">${ICO.diana}</span>
              <div><strong>Para qué le sirve</strong><p>${esc(l.para_que)}</p></div></div>
            <ul class="lec-meta">
              <li>${ICO.lista} ${total} pasos</li><li>${ICO.ok} ${acts.length ? acts.length + (acts.length > 1 ? " preguntas" : " pregunta") : "Sin práctica"}</li>
              <li>${ICO.reloj} ≈ ${minutos} min</li><li>${ICO.voz} Con audio</li>
            </ul>
            <h3 class="lec-sub">En esta lección</h3>
            <ol class="lec-temario">${l.pasos.map(p => `<li><span aria-hidden="true">${esc(p.icono)}</span> ${esc(resumen(p.texto))}</li>`).join("")}</ol>
            ${l.glosario.length ? `<details class="lec-glosario"><summary>${ICO.libro} Palabras clave (${l.glosario.length})</summary>
              <dl>${l.glosario.map(g => `<div><dt>${esc(g.termino)}</dt><dd>${esc(g.definicion)}</dd></div>`).join("")}</dl></details>` : ""}
            ${l.completada ? `<p class="insignia-ok">${ICO.ok} Ya completó esta lección. Puede repasarla cuando quiera.</p>` : ""}
            <button class="btn btn-grande" id="empezar">${l.completada ? "Repasar la lección" : "Empezar la lección"} ${ICO.der}</button>
          </div>
        </div>`;
    }

    function vistaPaso() {
      const p = l.pasos[paso];
      return `${encabezado()}
        <div class="leccion-cuerpo${l.dispositivo === "computador" ? " con-computador" : ""}">
          <figure class="dispositivo${l.dispositivo === "computador" ? " computador" : ""}" aria-hidden="true">
            <div class="dispositivo-pantalla">
              <span class="dispositivo-num">Paso ${paso + 1}</span>
              <span class="dispositivo-icono">${esc(p.icono)}</span>
            </div>
          </figure>
          <div class="leccion-texto">
            <div class="paso-tarjeta">
              <span class="paso-etq">Paso ${paso + 1} de ${total}</span>
              <p class="paso-texto">${esc(p.texto)}</p>
              ${p.consejo ? `<div class="paso-consejo"><span class="ico-consejo">${ICO.foco}</span><p><strong>Consejo:</strong> ${esc(p.consejo)}</p></div>` : ""}
              <button class="btn btn-audio" id="audio">${ICO.voz} Escuchar este paso</button>
              ${l.video_url ? `<a class="btn btn-sec" href="${esc(l.video_url)}" target="_blank" rel="noopener">🎬 Ver video (gasta datos)</a>` : ""}
            </div>
            <div class="fila nav-leccion">
              <button class="btn-icono ayuda-nav" id="ayuda-nav" aria-label="Ayuda: ¿Cómo uso esto?">?</button>
              <button class="btn btn-sec" id="atras">${ICO.izq} ${paso === 0 ? "Inicio" : "Atrás"}</button>
              <button class="btn" id="sig">${paso === total - 1 ? (act ? "Ir a la práctica" : "Terminar") : "Siguiente"} ${ICO.der}</button>
            </div>
          </div>
        </div>`;
    }

    function vistaPractica() {
      const act = acts[pregunta];
      if (!act) return `${encabezado()}<div class="practica"><p>Ha visto todos los pasos.</p>
        <button class="btn btn-verde btn-grande" id="fin">${ICO.ok} Marcar como terminada</button></div>`;
      return `${encabezado()}
        <section class="practica" aria-labelledby="preg">
          <div class="practica-cab"><span class="paso-etq">Practique lo aprendido</span>
            ${acts.length > 1 ? `<span class="practica-contador">Pregunta ${pregunta + 1} de ${acts.length}</span>` : ""}</div>
          ${acts.length > 1 ? `<div class="practica-puntos" aria-hidden="true">${acts.map((_, i) => `<span class="${i < pregunta ? "hecho" : i === pregunta ? "actual" : ""}"></span>`).join("")}</div>` : ""}
          <div class="practica-preg"><h3 id="preg">${esc(act.pregunta)}</h3>
            <button class="btn-icono" id="leer-preg" aria-label="Escuchar la pregunta y las opciones">${ICO.voz}</button></div>
          <div class="opciones" role="group" aria-label="Opciones de respuesta">
            ${mezclar(act.opciones).map((o, i) => `<button class="opcion" data-id="${o.id}">
              <span class="letra" aria-hidden="true">${"ABCDE"[i]}</span><span class="opcion-texto">${esc(o.texto)}</span>
              <span class="opcion-estado" aria-hidden="true"></span></button>`).join("")}
          </div>
          <div id="retro" aria-live="assertive"></div>
          <button class="enlace enlace-ico" id="repasar">${ICO.repetir} Repasar los pasos</button>
        </section>`;
    }

    function vistaCompletada() {
      const hechas = mod ? mod.lecciones.filter(x => x.completada || x.id === l.id).length : null;
      return `<div class="lec-fin">
          <div class="medalla" aria-hidden="true">${ICO.ok}</div>
          <h2>¡Lección completada!</h2>
          <p class="suave">${esc(l.titulo)}</p>
          ${l.recuerde.length ? `<div class="lec-recuerde"><strong>Lo que aprendió</strong>
            <ul>${l.recuerde.map(r => `<li>${ICO.ok}<span>${esc(r)}</span></li>`).join("")}</ul>
            <button class="enlace enlace-ico" id="leer-rec">${ICO.voz} Escuchar resumen</button></div>` : ""}
          ${mod ? `<div class="lec-fin-avance"><span>${esc(mod.icono)} ${esc(mod.titulo)}</span>
            <strong>${hechas} de ${mod.lecciones.length} lecciones</strong>${barra(Math.round(100 * hechas / mod.lecciones.length))}</div>` : ""}
          ${l.siguiente_id ? `<button class="btn btn-grande" onclick="location.hash='#leccion/${l.siguiente_id}'">Siguiente lección ${ICO.der}</button>`
                           : `<button class="btn btn-verde btn-grande" onclick="location.hash='#progreso'">🏅 Ver mi progreso y certificado</button>`}
          <button class="btn btn-sec" onclick="location.hash='#modulo/${l.modulo_id}'">Volver al módulo</button>
        </div>`;
    }

    function dibujar() {
      const fase = paso < 0 ? "inicio" : paso < total ? "paso" : paso === total ? "practica" : "fin";
      const html = { inicio: vistaInicio, paso: vistaPaso, practica: vistaPractica, fin: vistaCompletada }[fase]();
      const ayudas = {
        inicio: "Aquí ve de qué trata la lección y cuánto dura. Toque Empezar la lección cuando esté listo.",
        paso: "Lea el paso o toque Escuchar este paso. Use Siguiente para avanzar y Atrás para repetir.",
        practica: "Toque la respuesta que crea correcta. Le diremos si acertó y por qué.",
        fin: "¡Muy bien! Siga con la siguiente lección o vuelva al módulo.",
      };
      const conPaneles = fase === "paso" || fase === "practica";
      pantalla(`Lección ${l.posicion} de ${l.total}`, conPaneles
          ? `<div class="lec-3col">${panelIzquierdo()}<div class="leccion leccion-${fase}">${html}</div>${panelDerecho()}</div>`
          : `<div class="leccion leccion-${fase}">${html}</div>`,
        { atras: "#modulo/" + l.modulo_id, textoAtras: "Volver al módulo", ayuda: ayudas[fase], ancho: "ancho" });
      main.querySelectorAll("[data-leer-sit]").forEach(b => b.onclick = () => hablar(l.situacion));
      if (fase === "inicio") {
        $("#empezar").onclick = () => { paso = 0; dibujar(); };
        if ($("#leer-sit")) $("#leer-sit").onclick = () => hablar(l.situacion);
      }
      if (fase === "paso") {
        document.body.classList.add("en-paso");   // la ayuda va dentro de la navegación del paso
        $("#audio").onclick = () => hablar(`Paso ${paso + 1}. ${l.pasos[paso].texto} ${l.pasos[paso].consejo ? "Consejo: " + l.pasos[paso].consejo : ""}`);
        $("#atras").onclick = () => { paso--; dibujar(); };
        $("#ayuda-nav").onclick = () => $("#btn-ayuda").click();
        $("#sig").onclick = () => { paso++; dibujar(); };
      }
      if (fase === "practica") enlazarActividad();
      if (fase === "fin" && $("#leer-rec")) $("#leer-rec").onclick = () => hablar("Lo que aprendió. " + l.recuerde.join(". "));
    }

    function enlazarActividad() {
      const act = acts[pregunta];
      if (!act) {
        $("#fin").onclick = async () => { await API.post(`/api/lecciones/${l.id}/completar`); paso = total + 1; dibujar(); };
        return;
      }
      $("#repasar").onclick = () => { paso = 0; pregunta = 0; dibujar(); };
      $("#leer-preg").onclick = () => hablar(act.pregunta + ". " + [...document.querySelectorAll(".opcion .opcion-texto")]
        .map((o, i) => `Opción ${"ABCDE"[i]}: ${o.textContent}`).join(". "));
      document.querySelectorAll(".opcion").forEach(b => b.onclick = async () => {
        if (b.disabled) return;
        try {
          const r = await API.post(`/api/actividades/${act.id}/responder`, { opcion_id: Number(b.dataset.id) });
          if (r.correcta) {
            b.classList.add("ok"); b.querySelector(".opcion-estado").innerHTML = ICO.ok;
            document.querySelectorAll(".opcion").forEach(x => { x.disabled = true; });
            const hayOtra = pregunta + 1 < acts.length;
            $("#retro").innerHTML = `<div class="retro ok"><span class="retro-ico">${ICO.ok}</span>
              <div><strong>¡Correcto!</strong><p>${esc(r.explicacion)}</p></div></div>
              <button class="btn btn-grande" id="continuar">${hayOtra ? "Siguiente pregunta" : "Terminar la lección"} ${ICO.der}</button>`;
            hablar("Correcto. " + r.explicacion);
            $("#continuar").focus();
            $("#continuar").onclick = () => {
              if (hayOtra) { pregunta++; dibujar(); }
              else { paso = total + 1; dibujar(); }
            };
          } else {
            b.classList.add("mal"); b.disabled = true; b.querySelector(".opcion-estado").innerHTML = ICO.x;
            const porque = r.retroalimentacion || "Esa no es la respuesta.";
            $("#retro").innerHTML = `<div class="retro mal"><span class="retro-ico">${ICO.x}</span>
              <div><strong>Todavía no</strong><p>${esc(porque)}</p><p class="suave">Piénselo de nuevo e intente con otra opción.</p></div></div>`;
            hablar("Todavía no. " + porque + " Intente con otra opción.");
          }
        } catch (e) { aviso(e.message); }
      });
    }
    dibujar();
  }

  /* RF07 + RF08: progreso y certificados */
  async function vProgreso() {
    cargando();
    const p = await API.get("/api/progreso");
    pantalla("Mi progreso", `
      <div class="progreso-layout"><div class="progreso-resumen">
      <div class="anillo" style="--p:${p.porcentaje}" role="img" aria-label="Avance total ${p.porcentaje} por ciento"><span>${p.porcentaje}%</span></div>
      <p style="text-align:center">${p.completadas} de ${p.total} lecciones completadas</p></div>
      <div class="progreso-modulos">${p.modulos.map(m => m.terminado ? `
        <div class="tarjeta tarjeta-modulo recomendado">
          <span class="icono-circulo" aria-hidden="true">🏅</span>
          <span style="flex:1"><h3>¡Terminó "${esc(m.titulo)}"!</h3><span class="suave">Ya puede descargar su certificado</span></span>
        </div>
        ${API.sesion().usuario.invitado
          ? `<button class="btn" onclick="location.hash='#registro'">💾 Guarde su avance para recibir el certificado</button>`
          : `<button class="btn" data-cert="${m.modulo_id}">Descargar certificado (PDF)</button>`}` : `
        <div class="tarjeta tarjeta-modulo">
          <span class="icono-circulo" aria-hidden="true">${esc(m.icono)}</span>
          <span style="flex:1"><h3>${esc(m.titulo)}</h3><span class="suave">${m.completadas} de ${m.total} lecciones</span>${barra(m.porcentaje)}</span>
        </div>`).join("")}
      ${p.ultima_leccion_id ? `<button class="btn btn-sec" onclick="location.hash='#leccion/${p.ultima_leccion_id}'">Continuar donde iba</button>` : ""}
      <button class="btn btn-sec" onclick="location.hash='#rutas'">Volver a mis rutas</button></div></div>`,
      { atras: "#rutas", ayuda: "Aquí ve cuánto ha avanzado. Cuando termine un módulo aparece el botón para descargar su certificado." });
    document.querySelectorAll("[data-cert]").forEach(b => b.onclick = async () => {
      try { await API.descargar(`/api/certificados/${b.dataset.cert}`, `certificado_modulo_${b.dataset.cert}.pdf`); aviso("Certificado descargado."); }
      catch (e) { aviso(e.message); }
    });
  }

  /* RF09: panel del facilitador */
  async function vFacilitador(grupoId) {
    cargando();
    if (grupoId) {
      const g = await API.get(`/api/facilitador/grupos/${grupoId}/avance`);
      pantalla(g.grupo, `
        <form id="f-ins" class="tarjeta">
          <label for="cel-ins">Inscribir aprendiz (celular)</label>
          <input id="cel-ins" inputmode="numeric" maxlength="10" placeholder="3001234567">
          <p class="error" id="err" role="alert"></p>
          <button class="btn" type="submit">Inscribir</button>
        </form>
        <h2>Avance del grupo</h2>
        ${g.aprendices.length ? `<div class="tabla-scroll"><table>
          <thead><tr><th>Aprendiz</th><th>Total</th>${g.aprendices[0].modulos.map(m => `<th>${esc(m.titulo)}</th>`).join("")}<th>PIN</th></tr></thead>
          <tbody>${g.aprendices.map(a => `<tr><td>${esc(a.nombre)}<br><span class="suave">${esc(a.celular)}</span></td>
            <td><strong>${a.porcentaje}%</strong></td>${a.modulos.map(m => `<td>${m.porcentaje}%</td>`).join("")}
            <td><button class="btn btn-sec btn-chico" data-pin="${a.id}" data-nombre="${esc(a.nombre)}">Cambiar</button></td></tr>`).join("")}
          </tbody></table></div>` : '<p class="suave">Todavía no hay aprendices inscritos.</p>'}`,
        { atras: "#facilitador", ancho: "ancho", ayuda: "Inscriba aprendices con su número de celular. La tabla muestra el avance de cada uno por módulo. Si alguien olvidó su PIN, toque Cambiar." });
      $("#f-ins").onsubmit = async e => {
        e.preventDefault();
        try { const r = await API.post(`/api/facilitador/grupos/${grupoId}/inscribir`, { celular: $("#cel-ins").value.replace(/\D/g, "") });
              aviso(r.aprendiz + " fue inscrito."); vFacilitador(grupoId); }
        catch (err) { errorEn("#err", err); }
      };
      document.querySelectorAll("[data-pin]").forEach(b => b.onclick = async () => {
        const pin = prompt(`Nuevo PIN de 4 números para ${b.dataset.nombre}:`);
        if (!pin) return;
        try { await API.post(`/api/facilitador/aprendices/${b.dataset.pin}/restablecer-pin`, { pin_nuevo: pin }); aviso("PIN actualizado."); }
        catch (err) { aviso(err.message); }
      });
      return;
    }
    const grupos = await API.get("/api/facilitador/grupos");
    pantalla("Mis grupos", `
      <div class="rejilla-2">${grupos.map(g => `<button class="tarjeta tarjeta-modulo" onclick="location.hash='#facilitador/${g.id}'">
        <span class="icono-circulo" aria-hidden="true">👥</span><span><h3>${esc(g.nombre)}</h3>
        <span class="suave">${g.aprendices} ${g.aprendices === 1 ? "aprendiz" : "aprendices"}</span></span></button>`).join("") || '<p class="suave">Aún no tiene grupos.</p>'}</div>
      <form id="f-grupo" class="tarjeta">
        <label for="nom-grupo">Nombre del nuevo grupo</label>
        <input id="nom-grupo" maxlength="80" placeholder="Ej.: Salón comunal barrio Primero de Mayo">
        <p class="error" id="err" role="alert"></p>
        <button class="btn" type="submit">Crear grupo</button>
      </form>`, { ayuda: "Cree un grupo y luego entre a él para inscribir aprendices y ver su avance." });
    $("#f-grupo").onsubmit = async e => {
      e.preventDefault();
      try { await API.post("/api/facilitador/grupos", { nombre: $("#nom-grupo").value }); vFacilitador(); }
      catch (err) { errorEn("#err", err); }
    };
  }

  /* RF10 + RF11: panel del administrador */
  async function vAdmin(pestana = "modulos") {
    cargando();
    const tabs = [["modulos", "Módulos"], ["lecciones", "Lecciones"], ["usuarios", "Usuarios"], ["reportes", "Reportes"]];
    const cab = `<div class="pestanas" role="tablist">${tabs.map(([k, t]) =>
      `<button class="btn btn-sec btn-chico" role="tab" aria-selected="${k === pestana}" onclick="location.hash='#admin/${k}'">${t}</button>`).join("")}</div>`;
    const ay = "Use las pestañas para crear, consultar, modificar o eliminar módulos, lecciones y usuarios. En Reportes descarga el avance en CSV.";

    if (pestana === "modulos") {
      const mods = await API.get("/api/admin/modulos");
      pantalla("Administrar", cab + `
        <div class="admin-layout"><section class="admin-lista">
        <h2>Módulos</h2>
        <div class="tabla-scroll"><table><thead><tr><th>#</th><th>Módulo</th><th>Lecc.</th><th>Estado</th><th></th></tr></thead><tbody>
        ${mods.map(m => `<tr><td>${m.orden}</td><td>${esc(m.icono)} ${esc(m.titulo)}</td><td>${m.num_lecciones}</td>
          <td>${m.activo ? "Activo" : "Oculto"}</td>
          <td><button class="btn btn-sec btn-chico" data-ed="${m.id}">Editar</button>
              <button class="btn btn-peligro btn-chico" data-del="${m.id}">Eliminar</button></td></tr>`).join("")}
        </tbody></table></div>
        </section><section class="admin-form">
        <h2 id="t-form">Nuevo módulo</h2>
        <form id="f-mod" class="tarjeta">
          <input type="hidden" id="m-id">
          <div class="fila"><div><label for="m-orden">Orden</label><input id="m-orden" type="number" min="1" value="${mods.length + 1}"></div>
               <div><label for="m-icono">Ícono</label><input id="m-icono" value="📘" maxlength="4"></div></div>
          <label for="m-titulo">Título</label><input id="m-titulo" maxlength="80">
          <label for="m-desc">Descripción</label><textarea id="m-desc"></textarea>
          <label for="m-bloom">Nivel de Bloom</label><input id="m-bloom" placeholder="Aplicar">
          <label class="check"><input type="checkbox" id="m-activo" checked> Visible para los aprendices</label>
          <p class="error" id="err" role="alert"></p>
          <button class="btn" type="submit">Guardar módulo</button>
          <button class="btn btn-sec" type="reset" id="m-limpiar">Limpiar</button>
        </form></section></div>`, { ayuda: ay, ancho: "ancho" });
      document.querySelectorAll("[data-ed]").forEach(b => b.onclick = () => {
        const m = mods.find(x => x.id == b.dataset.ed);
        $("#t-form").textContent = "Editar módulo";
        $("#m-id").value = m.id; $("#m-orden").value = m.orden; $("#m-icono").value = m.icono;
        $("#m-titulo").value = m.titulo; $("#m-desc").value = m.descripcion; $("#m-bloom").value = m.nivel_bloom;
        $("#m-activo").checked = m.activo; $("#m-titulo").focus();
      });
      $("#m-limpiar").onclick = () => { $("#m-id").value = ""; $("#t-form").textContent = "Nuevo módulo"; };
      document.querySelectorAll("[data-del]").forEach(b => b.onclick = async () => {
        if (!confirm("¿Eliminar este módulo y todas sus lecciones? No se puede deshacer.")) return;
        try { await API.del("/api/admin/modulos/" + b.dataset.del); aviso("Módulo eliminado."); vAdmin("modulos"); } catch (e) { aviso(e.message); }
      });
      $("#f-mod").onsubmit = async e => {
        e.preventDefault();
        const id = $("#m-id").value;
        const datos = { orden: Number($("#m-orden").value), icono: $("#m-icono").value, titulo: $("#m-titulo").value,
          descripcion: $("#m-desc").value, nivel_bloom: $("#m-bloom").value, activo: $("#m-activo").checked };
        try { id ? await API.put("/api/admin/modulos/" + id, datos) : await API.post("/api/admin/modulos", datos);
              aviso("Módulo guardado correctamente."); vAdmin("modulos"); }
        catch (err) { errorEn("#err", err); }
      };
    }

    if (pestana === "lecciones") {
      const [mods, lecs] = await Promise.all([API.get("/api/admin/modulos"), API.get("/api/admin/lecciones")]);
      const nomMod = Object.fromEntries(mods.map(m => [m.id, m.titulo]));
      const N_PREG = 2;
      const bloque = q => `
          <fieldset class="tarjeta campo-pregunta"><legend><strong>Pregunta ${q + 1}</strong>${q > 0 ? " (opcional)" : ""}</legend>
            <label for="l-preg${q}">Pregunta</label><input id="l-preg${q}">
            <label for="l-bloom${q}">Nivel de Bloom</label>
            <select id="l-bloom${q}"><option>Recordar</option><option>Comprender</option><option>Aplicar</option><option>Analizar</option></select>
            ${[0, 1, 2].map(i => `<label for="l-op${q}-${i}">Opción ${"ABC"[i]}</label>
              <div class="fila"><input id="l-op${q}-${i}"><label class="check" style="flex:0 0 auto;margin:0"><input type="radio" name="l-ok${q}" value="${i}" ${i === 0 ? "checked" : ""}> Correcta</label></div>
              <input id="l-rt${q}-${i}" class="campo-retro" placeholder="Si la eligen y es incorrecta: ¿por qué no es?" aria-label="Retroalimentación de la opción ${"ABC"[i]}">`).join("")}
            <label for="l-expl${q}">Explicación de la respuesta correcta</label><textarea id="l-expl${q}" rows="2"></textarea>
          </fieldset>`;
      pantalla("Administrar", cab + `
        <div class="admin-layout"><section class="admin-lista">
        <h2>Lecciones</h2>
        <label for="filtro">Filtrar por módulo</label>
        <select id="filtro"><option value="">Todos</option>${mods.map(m => `<option value="${m.id}">${esc(m.titulo)}</option>`).join("")}</select>
        <div class="tabla-scroll"><table><thead><tr><th>Módulo</th><th>#</th><th>Lección</th><th>Contenido</th><th></th></tr></thead><tbody id="tb-lec">
        ${lecs.map(l => `<tr data-mod="${l.modulo_id}"><td>${esc(nomMod[l.modulo_id])}</td><td>${l.orden}</td><td>${esc(l.titulo)}${l.activo ? "" : " (oculta)"}</td>
          <td class="suave">${l.pasos.length} pasos · ${l.actividades.length} preg.</td>
          <td><button class="btn btn-sec btn-chico" data-ed="${l.id}">Editar</button>
              <button class="btn btn-peligro btn-chico" data-del="${l.id}">Eliminar</button></td></tr>`).join("")}
        </tbody></table></div>
        </section><section class="admin-form">
        <h2 id="t-form">Nueva lección</h2>
        <form id="f-lec" class="tarjeta">
          <input type="hidden" id="l-id">
          <div class="fila"><div><label for="l-mod">Módulo</label><select id="l-mod">${mods.map(m => `<option value="${m.id}">${esc(m.titulo)}</option>`).join("")}</select></div>
               <div><label for="l-orden">Orden</label><input id="l-orden" type="number" min="1" value="1"></div></div>
          <label for="l-titulo">Título</label><input id="l-titulo" maxlength="100">
          <label for="l-para">¿Para qué sirve?</label><input id="l-para">
          <label for="l-sit">Situación de la vida real</label>
          <textarea id="l-sit" rows="3" placeholder="Ej.: A doña Carmen le llegó un mensaje que…"></textarea>
          <label for="l-pasos">Pasos (uno por línea: ícono | texto | consejo opcional)</label>
          <textarea id="l-pasos" rows="6" placeholder="⚙️ | Abra Ajustes | Es el ícono de la tuerca&#10;📶 | Toque WiFi y actívelo"></textarea>
          <label for="l-glos">Palabras clave (una por línea: término: definición)</label>
          <textarea id="l-glos" rows="3" placeholder="WiFi: internet sin cables que llega desde un módem"></textarea>
          <label for="l-rec">Lo que aprendió (una idea clave por línea)</label>
          <textarea id="l-rec" rows="3"></textarea>
          <label for="l-video">Video opcional (enlace)</label><input id="l-video" type="url">
          <label for="l-disp">Los pasos se muestran en</label><select id="l-disp"><option value="celular">Celular</option><option value="computador">Computador</option></select>
          ${Array.from({ length: N_PREG }, (_, q) => bloque(q)).join("")}
          <label class="check"><input type="checkbox" id="l-activo" checked> Publicada</label>
          <p class="error" id="err" role="alert"></p>
          <button class="btn" type="submit">Guardar lección</button>
          <button class="btn btn-sec" type="reset" id="l-limpiar">Limpiar</button>
        </form></section></div>`, { ayuda: ay, ancho: "ancho" });
      $("#filtro").onchange = () => document.querySelectorAll("#tb-lec tr").forEach(tr =>
        tr.classList.toggle("oculto", !!$("#filtro").value && tr.dataset.mod !== $("#filtro").value));
      $("#l-limpiar").onclick = () => { $("#l-id").value = ""; $("#t-form").textContent = "Nueva lección"; };
      document.querySelectorAll("[data-ed]").forEach(b => b.onclick = () => {
        const l = lecs.find(x => x.id == b.dataset.ed);
        $("#t-form").textContent = "Editar lección";
        $("#l-id").value = l.id; $("#l-mod").value = l.modulo_id; $("#l-orden").value = l.orden; $("#l-titulo").value = l.titulo;
        $("#l-para").value = l.para_que; $("#l-sit").value = l.situacion || ""; $("#l-video").value = l.video_url || ""; $("#l-disp").value = l.dispositivo || "celular";
        $("#l-activo").checked = l.activo;
        $("#l-pasos").value = l.pasos.map(p => [p.icono, p.texto, p.consejo].filter(Boolean).join(" | ")).join("\n");
        $("#l-glos").value = l.glosario.map(g => `${g.termino}: ${g.definicion}`).join("\n");
        $("#l-rec").value = l.recuerde.join("\n");
        for (let q = 0; q < N_PREG; q++) {
          const a = l.actividades[q];
          $("#l-preg" + q).value = a ? a.pregunta : ""; $("#l-expl" + q).value = a ? a.explicacion : "";
          $("#l-bloom" + q).value = a && a.nivel_bloom ? a.nivel_bloom : (q === 0 ? "Recordar" : "Aplicar");
          [0, 1, 2].forEach(i => {
            $(`#l-op${q}-${i}`).value = a && a.opciones[i] ? a.opciones[i].texto : "";
            $(`#l-rt${q}-${i}`).value = a && a.opciones[i] ? (a.opciones[i].retroalimentacion || "") : "";
          });
          const k = a ? a.opciones.findIndex(o => o.correcta) : 0;
          document.querySelectorAll(`input[name=l-ok${q}]`).forEach(r => { r.checked = Number(r.value) === k; });
        }
        $("#l-titulo").focus();
      });
      document.querySelectorAll("[data-del]").forEach(b => b.onclick = async () => {
        if (!confirm("¿Eliminar esta lección? No se puede deshacer.")) return;
        try { await API.del("/api/admin/lecciones/" + b.dataset.del); aviso("Lección eliminada."); vAdmin("lecciones"); } catch (e) { aviso(e.message); }
      });
      $("#f-lec").onsubmit = async e => {
        e.preventDefault();
        const lineas = id => $(id).value.split("\n").map(x => x.trim()).filter(Boolean);
        const pasos = lineas("#l-pasos").map(x => {
          const partes = x.split("|").map(t => t.trim());
          if (partes.length === 1) return { icono: "👉", texto: partes[0], consejo: "" };
          return { icono: partes[0] || "👉", texto: partes[1] || "", consejo: partes.slice(2).join(" | ") };
        });
        const glosario = lineas("#l-glos").map(x => {
          const k = x.indexOf(":");
          return k > 0 ? { termino: x.slice(0, k).trim(), definicion: x.slice(k + 1).trim() } : null;
        }).filter(Boolean);
        const actividades = [];
        for (let q = 0; q < N_PREG; q++) {
          if (!$("#l-preg" + q).value.trim()) continue;
          const ok = Number(document.querySelector(`input[name=l-ok${q}]:checked`).value);
          actividades.push({ pregunta: $("#l-preg" + q).value, explicacion: $("#l-expl" + q).value, nivel_bloom: $("#l-bloom" + q).value,
            opciones: [0, 1, 2].map(i => ({ texto: $(`#l-op${q}-${i}`).value.trim(), correcta: i === ok,
              retroalimentacion: $(`#l-rt${q}-${i}`).value.trim() })).filter(o => o.texto) });
        }
        const datos = { modulo_id: Number($("#l-mod").value), orden: Number($("#l-orden").value), titulo: $("#l-titulo").value,
          para_que: $("#l-para").value, situacion: $("#l-sit").value, pasos, glosario, recuerde: lineas("#l-rec"),
          video_url: $("#l-video").value || null, dispositivo: $("#l-disp").value, activo: $("#l-activo").checked, actividades };
        const id = $("#l-id").value;
        try { id ? await API.put("/api/admin/lecciones/" + id, datos) : await API.post("/api/admin/lecciones", datos);
              aviso("Lección guardada correctamente."); vAdmin("lecciones"); }
        catch (err) { errorEn("#err", err); }
      };
    }

    if (pestana === "usuarios") {
      const us = await API.get("/api/admin/usuarios");
      pantalla("Administrar", cab + `
        <div class="admin-layout"><section class="admin-lista">
        <h2>Usuarios</h2>
        <div class="tabla-scroll"><table><thead><tr><th>Nombre</th><th>Celular</th><th>Rol</th><th>Estado</th><th></th></tr></thead><tbody>
        ${us.map(u => `<tr><td>${esc(u.nombre)}</td><td>${esc(u.celular)}</td><td>${u.rol}</td><td>${u.activo ? "Activo" : "Inactivo"}</td>
          <td><button class="btn btn-sec btn-chico" data-ed="${u.id}">Editar</button>
          ${u.activo ? `<button class="btn btn-peligro btn-chico" data-del="${u.id}">Desactivar</button>` : ""}</td></tr>`).join("")}
        </tbody></table></div>
        </section><section class="admin-form">
        <h2 id="t-form">Nuevo usuario</h2>
        <form id="f-us" class="tarjeta">
          <input type="hidden" id="u-id">
          <label for="u-nombre">Nombre</label><input id="u-nombre" maxlength="80">
          <label for="u-cel">Celular</label><input id="u-cel" inputmode="numeric" maxlength="10">
          <label for="u-pin">PIN (déjelo vacío para no cambiarlo)</label><input id="u-pin" class="pin" inputmode="numeric" maxlength="4">
          <label for="u-rol">Rol</label><select id="u-rol"><option>aprendiz</option><option>facilitador</option><option>administrador</option></select>
          <label class="check"><input type="checkbox" id="u-activo" checked> Activo</label>
          <p class="error" id="err" role="alert"></p>
          <button class="btn" type="submit">Guardar usuario</button>
          <button class="btn btn-sec" type="reset" id="u-limpiar">Limpiar</button>
        </form></section></div>`, { ayuda: ay, ancho: "ancho" });
      $("#u-limpiar").onclick = () => { $("#u-id").value = ""; $("#t-form").textContent = "Nuevo usuario"; };
      document.querySelectorAll("[data-ed]").forEach(b => b.onclick = () => {
        const u = us.find(x => x.id == b.dataset.ed);
        $("#t-form").textContent = "Editar usuario";
        $("#u-id").value = u.id; $("#u-nombre").value = u.nombre; $("#u-cel").value = u.celular;
        $("#u-rol").value = u.rol; $("#u-activo").checked = u.activo; $("#u-pin").value = ""; $("#u-nombre").focus();
      });
      document.querySelectorAll("[data-del]").forEach(b => b.onclick = async () => {
        if (!confirm("¿Desactivar este usuario? Su historial se conserva.")) return;
        try { await API.del("/api/admin/usuarios/" + b.dataset.del); aviso("Usuario desactivado."); vAdmin("usuarios"); } catch (e) { aviso(e.message); }
      });
      $("#f-us").onsubmit = async e => {
        e.preventDefault();
        const id = $("#u-id").value;
        const datos = { nombre: $("#u-nombre").value, celular: $("#u-cel").value.replace(/\D/g, ""), rol: $("#u-rol").value,
          activo: $("#u-activo").checked, pin: $("#u-pin").value || null };
        try { id ? await API.put("/api/admin/usuarios/" + id, datos) : await API.post("/api/admin/usuarios", datos);
              aviso("Usuario guardado correctamente."); vAdmin("usuarios"); }
        catch (err) { errorEn("#err", err); }
      };
    }

    if (pestana === "reportes") {
      pantalla("Administrar", cab + `
        <h2>Reportes del piloto</h2>
        <div class="tarjeta"><p>Descargue el avance de todos los aprendices (lecciones completadas, porcentaje por módulo y
        respuestas correctas) en formato CSV, listo para abrir en Excel.</p>
        <button class="btn btn-ancho-auto" id="csv">⬇️ Descargar reporte CSV</button></div>`, { ayuda: ay, ancho: "ancho" });
      $("#csv").onclick = async () => {
        try { await API.descargar("/api/admin/reportes/progreso.csv", "reporte_progreso.csv"); aviso("Reporte descargado."); }
        catch (e) { aviso(e.message); }
      };
    }
  }

  /* ---------------- Enrutador ---------------- */
  async function enrutar() {
    const [ruta, param] = (location.hash.slice(1) || "").split("/");
    const s = API.sesion();
    if (ruta === "salir") { API.guardarSesion(null); location.hash = "#login"; return; }
    if (!s && !["login", "registro"].includes(ruta)) { location.hash = "#login"; return; }
    if (s && (ruta === "" || ruta === "login" || (ruta === "registro" && !s.usuario.invitado))) { location.hash = "#rutas"; return; }
    try {
      switch (ruta) {
        case "login": return vLogin();
        case "registro": return vRegistro();
        case "diagnostico": return await vDiagnostico();
        case "rutas": return await vRutas();
        case "modulo": return await vModulo(param);
        case "leccion": return await vLeccion(param);
        case "progreso": return await vProgreso();
        case "certificados": return await vCertificados();
        case "facilitador": return await vFacilitador(param);
        case "admin": return await vAdmin(param);
        default: location.hash = "#rutas";
      }
    } catch (e) {
      pantalla("TIC para Todos", `<div class="tarjeta"><p class="error">${esc(e.message)}</p>
        <button class="btn" onclick="location.reload()">Intentar de nuevo</button></div>`, { atras: "#rutas" });
    }
  }
  window.addEventListener("hashchange", enrutar);
  enrutar();

  /* ---------------- PWA: funcionamiento sin conexión (RNF09) ---------------- */
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => navigator.serviceWorker.register("/sw.js").catch(() => {}));
  }
})();
