/* Cliente de la API REST. Guarda la sesión en localStorage. */
const API = (() => {
  const CLAVE = "aprendo_sesion";
  const CLAVE_INV = "aprendo_invitado";   // código y clave del invitado en este dispositivo

  function leerSesion() {
    try { return JSON.parse(localStorage.getItem(CLAVE)); } catch { return null; }
  }
  function guardarSesion(s) {
    try { s ? localStorage.setItem(CLAVE, JSON.stringify(s)) : localStorage.removeItem(CLAVE); } catch { /* sin almacenamiento */ }
  }

  function leerInvitado() {
    try { return JSON.parse(localStorage.getItem(CLAVE_INV)); } catch { return null; }
  }
  function guardarInvitado(c) {
    try { c ? localStorage.setItem(CLAVE_INV, JSON.stringify(c)) : localStorage.removeItem(CLAVE_INV); } catch { /* sin almacenamiento */ }
  }

  /* Entra como invitado. Si este dispositivo ya tiene un invitado, recupera su avance. */
  async function entrarInvitado() {
    const r = await fetch("/api/auth/invitado", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(leerInvitado() || {}) }).catch(() => null);
    if (!r) throw new Error("Sin conexión. Revise su internet e intente de nuevo.");
    const datos = await r.json();
    if (!r.ok) throw new Error(datos.detail || "No se pudo entrar. Intente de nuevo.");
    if (datos.credencial) guardarInvitado(datos.credencial);
    delete datos.credencial;
    guardarSesion(datos);
    return datos;
  }

  async function pedir(metodo, ruta, cuerpo, reintento = false) {
    const s = leerSesion();
    const opciones = { method: metodo, headers: {} };
    if (s) opciones.headers.Authorization = "Bearer " + s.token;
    if (cuerpo !== undefined) {
      opciones.headers["Content-Type"] = "application/json";
      opciones.body = JSON.stringify(cuerpo);
    }
    let r;
    try {
      r = await fetch(ruta, opciones);
    } catch {
      throw new Error("Sin conexión. Revise su internet e intente de nuevo.");
    }
    if (r.status === 401 && s) {
      if (s.usuario.invitado && leerInvitado() && !reintento) {   // la sesión venció: se renueva sola
        try { await entrarInvitado(); return pedir(metodo, ruta, cuerpo, true); } catch { /* sigue abajo */ }
      }
      guardarSesion(null);
      location.hash = "#login";
      throw new Error("Su sesión terminó. Entre de nuevo.");
    }
    if (r.status === 204) return null;
    const tipo = r.headers.get("content-type") || "";
    const datos = tipo.includes("application/json") ? await r.json() : await r.blob();
    if (!r.ok) {
      let msg = "Ocurrió un error. Intente de nuevo.";
      if (datos && typeof datos.detail === "string") msg = datos.detail;
      else if (datos && Array.isArray(datos.detail)) msg = "Revise los datos: " + traducirValidacion(datos.detail);
      throw new Error(msg);
    }
    return datos;
  }

  function traducirValidacion(det) {
    const campos = { celular: "el celular debe tener 10 números y empezar por 3", pin: "el PIN debe tener 4 números",
      nombre: "escriba su nombre", pin_nuevo: "el PIN debe tener 4 números" };
    return det.map(d => d.type === "value_error" ? d.msg.replace(/^Value error,\s*/, "")
                                                 : (campos[d.loc[d.loc.length - 1]] || d.msg)).join("; ");
  }

  async function descargar(ruta, nombre) {
    const blob = await pedir("GET", ruta);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = nombre; document.body.appendChild(a); a.click();
    a.remove(); setTimeout(() => URL.revokeObjectURL(url), 2000);
  }

  return {
    sesion: leerSesion, guardarSesion, descargar, invitado: leerInvitado, guardarInvitado, entrarInvitado,
    get: r => pedir("GET", r), post: (r, c) => pedir("POST", r, c ?? {}),
    put: (r, c) => pedir("PUT", r, c), del: r => pedir("DELETE", r),
  };
})();
