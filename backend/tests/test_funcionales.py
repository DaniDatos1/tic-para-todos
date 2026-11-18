"""Pruebas funcionales automatizadas. Cada prueba corresponde a un caso de la matriz (CP-xx)
y a un requerimiento funcional (RFxx) del documento maestro."""
import pytest

from app.security import verificar_pin


def _opciones(client, admin, leccion_id, k):
    """Devuelve (id_correcta, [ids_incorrectas]) de la pregunta k de una lección (vista de administrador)."""
    act = client.get(f"/api/admin/lecciones/{leccion_id}", headers=admin).json()["actividades"][k]
    ok = next(o["id"] for o in act["opciones"] if o["correcta"])
    return act["id"], ok, [o["id"] for o in act["opciones"] if not o["correcta"]]


def _completar_modulo(client, h, modulo_id):
    for lec in client.get(f"/api/modulos/{modulo_id}", headers=h).json()["lecciones"]:
        for act in client.get(f"/api/lecciones/{lec['id']}", headers=h).json()["actividades"]:
            for op in act["opciones"]:
                if client.post(f"/api/actividades/{act['id']}/responder", headers=h,
                               json={"opcion_id": op["id"]}).json()["correcta"]:
                    break


# ---------------- RF01 / RF13: registro y consentimiento ----------------
@pytest.mark.caso("CP-01", "RF01", "Registro con nombre, celular y PIN sin correo")
def test_registro_exitoso(client):
    r = client.post("/api/auth/registro", json={
        "nombre": "Luz Marina", "celular": "3201234567", "pin": "1357", "acepta_datos": True})
    assert r.status_code == 201
    assert r.json()["usuario"]["rol"] == "aprendiz" and r.json()["token"]


@pytest.mark.caso("CP-02", "RF13", "Registro rechazado si no acepta el tratamiento de datos")
def test_registro_sin_consentimiento(client):
    r = client.post("/api/auth/registro", json={
        "nombre": "Sin Consentimiento", "celular": "3201112233", "pin": "1357", "acepta_datos": False})
    assert r.status_code == 400


@pytest.mark.caso("CP-03", "RF01", "Registro rechazado con celular duplicado")
def test_registro_duplicado(client):
    r = client.post("/api/auth/registro", json={
        "nombre": "Repetida", "celular": "3201234567", "pin": "2580", "acepta_datos": True})
    assert r.status_code == 409


@pytest.mark.caso("CP-04", "RF01", "Validación de formato de celular (10 dígitos) y PIN (4 dígitos)")
@pytest.mark.parametrize("celular,pin", [("12345", "1234"), ("3001234567", "12"), ("3001234567", "abcd")])
def test_registro_datos_invalidos(client, celular, pin):
    r = client.post("/api/auth/registro", json={
        "nombre": "X Y", "celular": celular, "pin": pin, "acepta_datos": True})
    assert r.status_code == 422


@pytest.mark.caso("CP-05", "RF13", "El consentimiento queda registrado con fecha y versión")
def test_consentimiento_guardado(client):
    from sqlalchemy import select
    from app.database import SessionLocal
    from app.models import Consentimiento, Usuario
    with SessionLocal() as db:
        u = db.scalar(select(Usuario).where(Usuario.celular == "3201234567"))
        c = db.scalar(select(Consentimiento).where(Consentimiento.usuario_id == u.id))
        assert c and c.aceptado and c.version and c.fecha


# ---------------- RF02 y RNF05: inicio de sesión ----------------
@pytest.mark.caso("CP-06", "RF02", "Inicio de sesión con celular y PIN correctos")
def test_login_correcto(client):
    r = client.post("/api/auth/login", json={"celular": "3201234567", "pin": "1357"})
    assert r.status_code == 200 and r.json()["usuario"]["nombre"] == "Luz Marina"


@pytest.mark.caso("CP-07", "RF02", "Inicio de sesión rechazado con PIN incorrecto")
def test_login_incorrecto(client):
    r = client.post("/api/auth/login", json={"celular": "3201234567", "pin": "0000"})
    assert r.status_code == 401


@pytest.mark.caso("CP-08", "RNF05", "El PIN se almacena cifrado con bcrypt, nunca en texto plano")
def test_pin_hash(client):
    from sqlalchemy import select
    from app.database import SessionLocal
    from app.models import Usuario
    with SessionLocal() as db:
        u = db.scalar(select(Usuario).where(Usuario.celular == "3201234567"))
        assert u.pin_hash != "1357" and u.pin_hash.startswith("$2") and verificar_pin("1357", u.pin_hash)


@pytest.mark.caso("CP-09", "RNF05", "Las rutas protegidas exigen sesión válida")
def test_ruta_protegida(client):
    assert client.get("/api/rutas").status_code == 401
    assert client.get("/api/rutas", headers={"Authorization": "Bearer falso"}).status_code == 401


# ---------------- RF03: diagnóstico ----------------
@pytest.mark.caso("CP-10", "RF03", "La prueba diagnóstica tiene 10 preguntas")
def test_diagnostico_preguntas(client, aprendiz):
    assert len(client.get("/api/diagnostico/preguntas", headers=aprendiz).json()) == 10


@pytest.mark.caso("CP-11", "RF03", "El diagnóstico recomienda el primer módulo no dominado")
def test_diagnostico_recomendacion(client, aprendiz):
    ps = client.get("/api/diagnostico/preguntas", headers=aprendiz).json()
    # Domina las 3 primeras (módulo 1) y no sabe el resto -> debe recomendar el módulo 2
    resp = {p["id"]: (2 if i < 3 else 0) for i, p in enumerate(ps)}
    r = client.post("/api/diagnostico", headers=aprendiz, json={"respuestas": resp}).json()
    assert r["modulo_recomendado"]["titulo"] == "Comunicación y productividad digital" and r["puntaje"] == 30


@pytest.mark.caso("CP-12", "RF03", "El diagnóstico se rechaza si faltan respuestas")
def test_diagnostico_incompleto(client, aprendiz):
    ps = client.get("/api/diagnostico/preguntas", headers=aprendiz).json()
    r = client.post("/api/diagnostico", headers=aprendiz, json={"respuestas": {ps[0]["id"]: 2}})
    assert r.status_code == 400


# ---------------- RF04 / RF05: rutas y lecciones ----------------
@pytest.mark.caso("CP-13", "RF04", "Las rutas muestran los cuatro módulos y el recomendado")
def test_rutas(client, aprendiz):
    r = client.get("/api/rutas", headers=aprendiz).json()
    assert [m["titulo"] for m in r["modulos"]] == ["Alfabetización y herramientas digitales", "Comunicación y productividad digital",
                                                "Seguridad y ciudadanía digital", "Tecnología para el empleo y el emprendimiento"]
    assert r["recomendado_id"] == r["modulos"][1]["id"]


@pytest.mark.caso("CP-14", "RF05", "Cada lección presenta título, propósito y pasos")
def test_leccion_contenido(client, aprendiz):
    l = client.get("/api/lecciones/1", headers=aprendiz).json()
    assert l["titulo"] and l["para_que"] and len(l["pasos"]) >= 3 and l["posicion"] == 1


@pytest.mark.caso("CP-35", "RF05", "Todas las lecciones traen situación real, consejos, palabras clave y resumen")
def test_contenido_enriquecido(client, admin):
    lecs = client.get("/api/admin/lecciones", headers=admin).json()
    assert len(lecs) == 20
    for l in lecs:
        assert l["situacion"] and len(l["pasos"]) == 5 and all(p["texto"] and p["consejo"] for p in l["pasos"])
        assert len(l["glosario"]) >= 2 and len(l["recuerde"]) >= 3
        assert l["dispositivo"] in ("celular", "computador")
    assert {l["dispositivo"] for l in lecs} == {"celular", "computador"}


@pytest.mark.caso("CP-36", "RF06", "Cada lección tiene dos preguntas: una de recordar/comprender y una de aplicar/analizar")
def test_preguntas_bloom(client, admin):
    for l in client.get("/api/admin/lecciones", headers=admin).json():
        niveles = [a["nivel_bloom"] for a in l["actividades"]]
        assert len(niveles) == 2 and niveles[0] in ("Recordar", "Comprender") and niveles[1] in ("Aplicar", "Analizar")
        assert all(sum(o["correcta"] for o in a["opciones"]) == 1 for a in l["actividades"])


@pytest.mark.caso("CP-15", "RF06", "La actividad no expone la respuesta correcta antes de responder")
def test_actividad_sin_respuesta(client, aprendiz):
    act = client.get("/api/lecciones/1", headers=aprendiz).json()["actividades"][0]
    assert all("correcta" not in o for o in act["opciones"])


# ---------------- RF06 / RF07: actividades y progreso ----------------
@pytest.mark.caso("CP-16", "RF06", "Respuesta incorrecta: explica por qué no es y no revela la correcta")
def test_respuesta_incorrecta(client, aprendiz, admin):
    aid, _, malas = _opciones(client, admin, 1, 0)
    r = client.post(f"/api/actividades/{aid}/responder", headers=aprendiz, json={"opcion_id": malas[0]}).json()
    assert r["correcta"] is False and len(r["retroalimentacion"]) > 20
    assert r["opcion_correcta_id"] is None and r["explicacion"] == ""
    assert client.get("/api/progreso", headers=aprendiz).json()["completadas"] == 0


@pytest.mark.caso("CP-17", "RF06", "Respuesta correcta: retroalimentación con explicación")
def test_respuesta_correcta(client, aprendiz, admin):
    aid, ok, _ = _opciones(client, admin, 1, 0)
    r = client.post(f"/api/actividades/{aid}/responder", headers=aprendiz, json={"opcion_id": ok}).json()
    assert r["correcta"] is True and r["explicacion"]
    assert r["leccion_completada"] is False   # aún falta la segunda pregunta


@pytest.mark.caso("CP-37", "RF07", "La lección se completa solo al acertar todas sus preguntas")
def test_completar_todas(client, aprendiz, admin):
    aid, ok, _ = _opciones(client, admin, 1, 1)
    r = client.post(f"/api/actividades/{aid}/responder", headers=aprendiz, json={"opcion_id": ok}).json()
    assert r["correcta"] is True and r["leccion_completada"] is True


@pytest.mark.caso("CP-18", "RF07", "El progreso se registra y se recuerda la última lección vista")
def test_progreso(client, aprendiz):
    client.get("/api/lecciones/2", headers=aprendiz)
    p = client.get("/api/progreso", headers=aprendiz).json()
    assert p["completadas"] == 1 and p["ultima_leccion_id"] == 2 and p["porcentaje"] == 5  # 1 de 20


# ---------------- RF08: certificado ----------------
@pytest.mark.caso("CP-19", "RF08", "No se entrega certificado si el módulo no está terminado")
def test_certificado_bloqueado(client, aprendiz):
    assert client.get("/api/certificados/1", headers=aprendiz).status_code == 400


@pytest.mark.caso("CP-20", "RF08", "Se genera el certificado PDF al terminar el módulo")
def test_certificado_pdf(client, aprendiz):
    _completar_modulo(client, aprendiz, 1)
    r = client.get("/api/certificados/1", headers=aprendiz)
    assert r.status_code == 200 and r.headers["content-type"] == "application/pdf"
    assert r.content.startswith(b"%PDF") and len(r.content) > 1000


# ---------------- RF09 / RF02: facilitador ----------------
@pytest.mark.caso("CP-21", "RF09", "El facilitador crea un grupo")
def test_crear_grupo(client, facilitador):
    r = client.post("/api/facilitador/grupos", headers=facilitador, json={"nombre": "Barrio Primero de Mayo"})
    assert r.status_code == 201


@pytest.mark.caso("CP-22", "RF09", "El facilitador inscribe a un aprendiz y consulta su avance")
def test_inscribir_y_avance(client, facilitador):
    gid = [g for g in client.get("/api/facilitador/grupos", headers=facilitador).json()
           if g["nombre"] == "Barrio Primero de Mayo"][0]["id"]
    assert client.post(f"/api/facilitador/grupos/{gid}/inscribir", headers=facilitador,
                       json={"celular": "3109998877"}).status_code == 200
    av = client.get(f"/api/facilitador/grupos/{gid}/avance", headers=facilitador).json()
    assert av["aprendices"][0]["nombre"] == "Aprendiz Prueba" and av["aprendices"][0]["modulos"][0]["porcentaje"] == 100


@pytest.mark.caso("CP-23", "RF02", "El facilitador restablece el PIN de un aprendiz de su grupo")
def test_restablecer_pin(client, facilitador):
    uid = client.post("/api/auth/login", json={"celular": "3109998877", "pin": "2468"}).json()["usuario"]["id"]
    assert client.post(f"/api/facilitador/aprendices/{uid}/restablecer-pin", headers=facilitador,
                       json={"pin_nuevo": "9753"}).status_code == 200
    assert client.post("/api/auth/login", json={"celular": "3109998877", "pin": "9753"}).status_code == 200


@pytest.mark.caso("CP-24", "RF09", "Un aprendiz no puede acceder al panel del facilitador")
def test_permiso_facilitador(client, aprendiz):
    assert client.get("/api/facilitador/grupos", headers=aprendiz).status_code == 403


# ---------------- RF10: CRUD del administrador ----------------
@pytest.mark.caso("CP-25", "RF10", "Crear (C) un módulo")
def test_crud_crear_modulo(client, admin, request):
    r = client.post("/api/admin/modulos", headers=admin, json={"orden": 5, "titulo": "Módulo de prueba"})
    assert r.status_code == 201
    request.config.cache.set("mod_id", r.json()["id"])


@pytest.mark.caso("CP-26", "RF10", "Consultar (R) y modificar (U) un módulo")
def test_crud_editar_modulo(client, admin, request):
    mid = request.config.cache.get("mod_id", None)
    assert any(m["id"] == mid for m in client.get("/api/admin/modulos", headers=admin).json())
    r = client.put(f"/api/admin/modulos/{mid}", headers=admin,
                   json={"orden": 5, "titulo": "Módulo editado", "activo": False})
    assert r.status_code == 200 and r.json()["titulo"] == "Módulo editado"


@pytest.mark.caso("CP-27", "RF10", "Crear una lección con su actividad sin modificar el código")
def test_crud_crear_leccion(client, admin, aprendiz, request):
    r = client.post("/api/admin/lecciones", headers=admin, json={
        "modulo_id": 2, "orden": 5, "titulo": "Usar Nequi con seguridad", "para_que": "Enviar dinero",
        "situacion": "Don José quiere enviarle dinero a su nieta.",
        "pasos": [{"icono": "📲", "texto": "Instale la app oficial", "consejo": "Solo desde la tienda"}],
        "glosario": [{"termino": "Billetera digital", "definicion": "App para guardar y enviar dinero"}],
        "recuerde": ["Nunca comparta su clave"],
        "actividad": {"pregunta": "¿Comparte su clave?", "explicacion": "Nunca.",
                      "opciones": [{"texto": "Nunca", "correcta": True}, {"texto": "Sí"}]}})
    assert r.status_code == 201
    lid = r.json()["id"]
    assert r.json()["situacion"] and r.json()["glosario"][0]["termino"] == "Billetera digital"
    assert r.json()["pasos"][0]["consejo"] == "Solo desde la tienda"
    request.config.cache.set("lec_id", lid)
    assert client.get(f"/api/lecciones/{lid}", headers=aprendiz).json()["titulo"] == "Usar Nequi con seguridad"


@pytest.mark.caso("CP-28", "RF10", "Modificar una lección y validar una sola opción correcta")
def test_crud_editar_leccion(client, admin, request):
    lid = request.config.cache.get("lec_id", None)
    base = {"modulo_id": 2, "orden": 5, "titulo": "Usar Nequi (editada)", "pasos": [{"texto": "Paso"}]}
    mala = {**base, "actividad": {"pregunta": "¿Cuál es la correcta?", "opciones": [{"texto": "a", "correcta": True}, {"texto": "b", "correcta": True}]}}
    assert client.put(f"/api/admin/lecciones/{lid}", headers=admin, json=mala).status_code == 400
    assert client.put(f"/api/admin/lecciones/{lid}", headers=admin, json=base).json()["titulo"] == "Usar Nequi (editada)"


@pytest.mark.caso("CP-29", "RF10", "Eliminar (D) una lección y un módulo")
def test_crud_eliminar(client, admin, request):
    lid = request.config.cache.get("lec_id", None)
    mid = request.config.cache.get("mod_id", None)
    assert client.delete(f"/api/admin/lecciones/{lid}", headers=admin).status_code == 204
    assert client.get(f"/api/admin/lecciones/{lid}", headers=admin).status_code == 404
    assert client.delete(f"/api/admin/modulos/{mid}", headers=admin).status_code == 204


@pytest.mark.caso("CP-30", "RF10", "Gestión de usuarios: crear, editar y desactivar")
def test_crud_usuarios(client, admin):
    r = client.post("/api/admin/usuarios", headers=admin, json={
        "nombre": "Nuevo Facilitador", "celular": "3155550000", "pin": "1122", "rol": "facilitador"})
    assert r.status_code == 201
    uid = r.json()["id"]
    assert client.put(f"/api/admin/usuarios/{uid}", headers=admin, json={
        "nombre": "Facilitador Editado", "celular": "3155550000", "rol": "facilitador"}).status_code == 200
    assert client.delete(f"/api/admin/usuarios/{uid}", headers=admin).json()["activo"] is False
    assert client.post("/api/auth/login", json={"celular": "3155550000", "pin": "1122"}).status_code == 403


@pytest.mark.caso("CP-31", "RF10", "Un aprendiz no puede usar las funciones de administración")
def test_permiso_admin(client, aprendiz):
    assert client.post("/api/admin/modulos", headers=aprendiz, json={"orden": 9, "titulo": "Hack"}).status_code == 403


# ---------------- RF11: reportes ----------------
@pytest.mark.caso("CP-32", "RF11", "Exportar el reporte de progreso en CSV")
def test_reporte_csv(client, admin):
    r = client.get("/api/admin/reportes/progreso.csv", headers=admin)
    assert r.status_code == 200 and "text/csv" in r.headers["content-type"]
    texto = r.content.decode("utf-8-sig")
    assert texto.splitlines()[0].startswith("id;nombre") and "Aprendiz Prueba" in texto


# ---------------- RF12 / RNF09: interfaz y PWA ----------------
@pytest.mark.caso("CP-33", "RF12", "La interfaz incluye controles de letra, contraste, voz y ayuda")
def test_interfaz_accesible(client):
    html = client.get("/").text
    for control in ('id="btn-letra"', 'id="btn-contraste"', 'id="btn-ayuda"', 'lang="es"'):
        assert control in html
    assert "speechSynthesis" in client.get("/js/app.js").text


@pytest.mark.caso("CP-34", "RNF09", "La PWA expone manifiesto y service worker")
def test_pwa(client):
    assert client.get("/manifest.json").json()["display"] == "standalone"
    assert "caches" in client.get("/sw.js").text


# ---------------- Preguntas: dificultad y retroalimentación ----------------
@pytest.mark.caso("CP-38", "RF06", "Cada opción incorrecta tiene su propia explicación de por qué no es")
def test_retro_por_opcion(client, admin):
    for l in client.get("/api/admin/lecciones", headers=admin).json():
        for a in l["actividades"]:
            assert len(a["opciones"]) == 3
            assert all(o["retroalimentacion"] for o in a["opciones"] if not o["correcta"])


@pytest.mark.caso("CP-39", "RF06", "La opción correcta no ocupa siempre la misma posición")
def test_posicion_variable(client, admin):
    pos = [next(i for i, o in enumerate(a["opciones"]) if o["correcta"])
           for l in client.get("/api/admin/lecciones", headers=admin).json() for a in l["actividades"]]
    assert len(set(pos)) == 3 and max(pos.count(i) for i in range(3)) < len(pos) * 0.6


# ---------------- Seguridad ----------------
@pytest.mark.caso("CP-40", "RNF05", "La cuenta se bloquea tras 5 intentos fallidos de PIN")
def test_bloqueo_intentos(client):
    client.post("/api/auth/registro", json={"nombre": "Prueba Bloqueo", "celular": "3127778899",
                                            "pin": "4826", "acepta_datos": True})
    for i in range(4):
        r = client.post("/api/auth/login", json={"celular": "3127778899", "pin": "0001"})
        assert r.status_code == 401 and "quedan" in r.json()["detail"]
    assert client.post("/api/auth/login", json={"celular": "3127778899", "pin": "0001"}).status_code == 429
    # aunque ahora use el PIN correcto, sigue bloqueada
    assert client.post("/api/auth/login", json={"celular": "3127778899", "pin": "4826"}).status_code == 429


@pytest.mark.caso("CP-41", "RNF05", "No se permiten PIN fáciles de adivinar (1234, 0000, 9876)")
@pytest.mark.parametrize("pin", ["1234", "0000", "9876", "5555"])
def test_pin_trivial(client, pin):
    r = client.post("/api/auth/registro", json={"nombre": "PIN Debil", "celular": "3130001122",
                                                "pin": pin, "acepta_datos": True})
    assert r.status_code == 422 and "fácil" in str(r.json())


@pytest.mark.caso("CP-42", "RNF05", "El servidor envía cabeceras de seguridad HTTP")
def test_cabeceras(client):
    h = client.get("/").headers
    assert h["x-frame-options"] == "DENY" and h["x-content-type-options"] == "nosniff"
    assert "frame-ancestors 'none'" in h["content-security-policy"]
    assert client.get("/api/salud").headers["cache-control"] == "no-store"


@pytest.mark.caso("CP-43", "RNF05", "El reporte CSV neutraliza fórmulas maliciosas en los nombres")
def test_csv_inyeccion(client, admin):
    client.post("/api/auth/registro", json={"nombre": "=HYPERLINK(\"x\")", "celular": "3141112233",
                                            "pin": "7392", "acepta_datos": True})
    texto = client.get("/api/admin/reportes/progreso.csv", headers=admin).content.decode("utf-8-sig")
    assert "'=HYPERLINK" in texto and ";=HYPERLINK" not in texto


# ---------------- Entrada como invitado ----------------
def _invitado(client, cred=None):
    r = client.post("/api/auth/invitado", json=cred or {})
    assert r.status_code == 200
    d = r.json()
    return d, {"Authorization": "Bearer " + d["token"]}


@pytest.mark.caso("CP-44", "RF02", "Se puede entrar como invitado sin dar ningún dato personal")
def test_invitado_entra(client):
    d, h = _invitado(client)
    assert d["usuario"]["invitado"] is True and d["usuario"]["celular"] is None
    assert d["credencial"]["codigo"] and len(d["credencial"]["clave"]) >= 24
    assert client.get("/api/rutas", headers=h).status_code == 200


@pytest.mark.caso("CP-45", "RF02", "El invitado vuelve a entrar desde su dispositivo y conserva su avance")
def test_invitado_conserva_avance(client, admin):
    d, h = _invitado(client)
    act, ok, _ = _opciones(client, admin, 1, 0)
    client.post(f"/api/actividades/{act}/responder", headers=h, json={"opcion_id": ok})
    d2, h2 = _invitado(client, d["credencial"])
    assert d2["usuario"]["id"] == d["usuario"]["id"] and "credencial" not in d2
    # con una clave equivocada no recupera esa cuenta: obtiene un invitado nuevo
    d3, _ = _invitado(client, {"codigo": d["credencial"]["codigo"], "clave": "x" * 30})
    assert d3["usuario"]["id"] != d["usuario"]["id"]


@pytest.mark.caso("CP-46", "RF01", "El invitado guarda su avance con nombre, celular y PIN sin perder lo hecho")
def test_invitado_guarda_avance(client, admin):
    d, h = _invitado(client)
    for k in range(2):
        act, ok, _ = _opciones(client, admin, 1, k)
        client.post(f"/api/actividades/{act}/responder", headers=h, json={"opcion_id": ok})
    assert client.get("/api/progreso", headers=h).json()["completadas"] == 1
    assert client.post("/api/auth/guardar-avance", headers=h, json={
        "nombre": "Ana Invitada", "celular": "3159998877", "pin": "4826", "acepta_datos": False}).status_code == 400
    r = client.post("/api/auth/guardar-avance", headers=h, json={
        "nombre": "Ana Invitada", "celular": "3159998877", "pin": "4826", "acepta_datos": True})
    assert r.status_code == 200 and r.json()["usuario"]["invitado"] is False
    s = client.post("/api/auth/login", json={"celular": "3159998877", "pin": "4826"}).json()
    hl = {"Authorization": "Bearer " + s["token"]}
    assert s["usuario"]["id"] == d["usuario"]["id"]
    assert client.get("/api/progreso", headers=hl).json()["completadas"] == 1


@pytest.mark.caso("CP-47", "RF08", "El invitado debe guardar su avance para recibir certificados")
def test_invitado_sin_certificado(client):
    _, h = _invitado(client)
    _completar_modulo(client, h, 1)
    r = client.get("/api/certificados/1", headers=h)
    assert r.status_code == 403 and "Guardar mi avance" in r.json()["detail"]


@pytest.mark.caso("CP-48", "RNF05", "Detrás de un túnel, el límite de invitados se cuenta por la IP real de cada visitante")
def test_invitado_ip_real_tras_tunel():
    from starlette.requests import Request as Req
    from app.routers.auth import _ip_cliente
    def req(host, headers):
        return Req({"type": "http", "client": (host, 1), "headers": [(k.encode(), v.encode()) for k, v in headers.items()]})
    assert _ip_cliente(req("127.0.0.1", {"cf-connecting-ip": "181.50.1.2"})) == "181.50.1.2"
    assert _ip_cliente(req("127.0.0.1", {"x-forwarded-for": "190.1.1.1, 10.0.0.1"})) == "190.1.1.1"
    # una petición directa no puede falsificar su IP con la cabecera
    assert _ip_cliente(req("200.1.1.1", {"cf-connecting-ip": "1.1.1.1"})) == "200.1.1.1"


@pytest.mark.caso("CP-49", "RNF05", "En un despliegue público no se crean los usuarios de prueba, solo el administrador configurado")
def test_despliegue_sin_usuarios_de_prueba(monkeypatch):
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import sessionmaker
    from app.database import Base
    from app.models import Usuario
    from app.security import verificar_pin
    from app import seed
    eng = create_engine("sqlite://")
    Base.metadata.create_all(eng)
    monkeypatch.setenv("ADMIN_CELULAR", "3109876543")
    monkeypatch.setenv("ADMIN_PIN", "4826")
    with sessionmaker(bind=eng)() as db:
        assert seed.sembrar(db)
        usuarios = db.scalars(select(Usuario)).all()
        assert [(u.celular, u.rol) for u in usuarios] == [("3109876543", "administrador")]
        assert verificar_pin("4826", usuarios[0].pin_hash)
    monkeypatch.setenv("ADMIN_PIN", "1234")   # un PIN fácil se rechaza
    eng2 = create_engine("sqlite://")
    Base.metadata.create_all(eng2)
    with sessionmaker(bind=eng2)() as db, pytest.raises(SystemExit):
        seed.sembrar(db)
