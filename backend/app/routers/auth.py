"""RF01, RF02, RF13: entrada como invitado, registro con celular y PIN, consentimiento e inicio
de sesión.

El acceso principal es como invitado: no se pide ningún dato personal. El dispositivo guarda un
código y una clave aleatorios que le permiten volver a entrar con el mismo avance. Si la persona
quiere conservar su avance en otro dispositivo o recibir certificados, lo guarda con nombre,
celular y PIN (y ahí sí acepta el tratamiento de datos).
"""
import secrets
import time
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import CONSENTIMIENTO_VERSION, MAX_INTENTOS, MINUTOS_BLOQUEO
from ..database import get_db
from ..models import Consentimiento, Usuario
from ..schemas import InvitadoIn, LoginIn, RegistroIn
from ..security import crear_token, hash_pin, usuario_actual, verificar_pin

router = APIRouter(prefix="/api/auth", tags=["Autenticación"])


MAX_INVITADOS_HORA = 60            # invitados nuevos por dirección IP en una hora
_invitados_recientes: dict[str, list[float]] = {}


def _sesion(u: Usuario) -> dict:
    return {"token": crear_token(u.id),
            "usuario": {"id": u.id, "nombre": u.nombre, "rol": u.rol,
                        "celular": None if u.invitado else u.celular, "invitado": bool(u.invitado)}}


def _ip_cliente(request: Request) -> str:
    """IP real del visitante. Si la petición llega desde el mismo equipo (un túnel como Cloudflare
    Tunnel o un proxy local), se usa la cabecera que ese intermediario agrega; si llega directo,
    se usa la IP de la conexión, porque en ese caso las cabeceras podrían falsificarse."""
    ip = request.client.host if request.client else "desconocido"
    if ip in ("127.0.0.1", "::1", "localhost"):
        reenviada = request.headers.get("cf-connecting-ip") or request.headers.get("x-forwarded-for", "")
        if reenviada:
            return reenviada.split(",")[0].strip()
    return ip


def _limitar_invitados(ip: str) -> None:
    ahora = time.time()
    recientes = [t for t in _invitados_recientes.get(ip, []) if t > ahora - 3600]
    if len(recientes) >= MAX_INVITADOS_HORA:
        raise HTTPException(429, "Se han creado demasiados accesos desde esta conexión. Intente más tarde.")
    recientes.append(ahora)
    _invitados_recientes[ip] = recientes


@router.post("/invitado")
def entrar_como_invitado(datos: InvitadoIn, request: Request, db: Session = Depends(get_db)):
    if datos.codigo and datos.clave:
        u = db.scalar(select(Usuario).where(Usuario.celular == datos.codigo, Usuario.invitado.is_(True)))
        if u and u.activo and verificar_pin(datos.clave, u.pin_hash):
            return _sesion(u)
    _limitar_invitados(_ip_cliente(request))
    codigo = "i" + secrets.token_hex(5)[:9]      # no empieza por 3: nunca choca con un celular
    while db.scalar(select(Usuario.id).where(Usuario.celular == codigo)):
        codigo = "i" + secrets.token_hex(5)[:9]
    clave = secrets.token_urlsafe(24)
    u = Usuario(nombre="Invitado", celular=codigo, pin_hash=hash_pin(clave), invitado=True)
    db.add(u)
    db.commit()
    return {**_sesion(u), "credencial": {"codigo": codigo, "clave": clave}}


@router.post("/guardar-avance")
def guardar_avance(datos: RegistroIn, db: Session = Depends(get_db), u: Usuario = Depends(usuario_actual)):
    """Convierte al invitado en una cuenta con nombre, celular y PIN. Conserva todo su avance."""
    if not u.invitado:
        raise HTTPException(400, "Su avance ya está guardado en su cuenta.")
    if not datos.acepta_datos:
        raise HTTPException(400, "Debe aceptar el tratamiento de datos para guardar su avance.")
    if db.scalar(select(Usuario).where(Usuario.celular == datos.celular)):
        raise HTTPException(409, "Ese número ya está registrado. Si es suyo, salga y entre con su celular y PIN.")
    u.nombre, u.celular, u.pin_hash, u.invitado = datos.nombre.strip(), datos.celular, hash_pin(datos.pin), False
    db.add(Consentimiento(usuario_id=u.id, version=CONSENTIMIENTO_VERSION, aceptado=True))
    db.commit()
    return _sesion(u)


@router.post("/registro", status_code=201)
def registrar(datos: RegistroIn, db: Session = Depends(get_db)):
    if not datos.acepta_datos:
        raise HTTPException(400, "Debe aceptar el tratamiento de datos para registrarse.")
    if db.scalar(select(Usuario).where(Usuario.celular == datos.celular)):
        raise HTTPException(409, "Ese número de celular ya está registrado.")
    u = Usuario(nombre=datos.nombre.strip(), celular=datos.celular, pin_hash=hash_pin(datos.pin))
    db.add(u)
    db.flush()
    db.add(Consentimiento(usuario_id=u.id, version=CONSENTIMIENTO_VERSION, aceptado=True))
    db.commit()
    return _sesion(u)


@router.post("/login")
def login(datos: LoginIn, db: Session = Depends(get_db)):
    u = db.scalar(select(Usuario).where(Usuario.celular == datos.celular))
    if not u:
        raise HTTPException(401, "Número o PIN incorrecto.")
    ahora = datetime.now()
    if u.bloqueado_hasta and u.bloqueado_hasta > ahora:
        minutos = max(1, round((u.bloqueado_hasta - ahora).total_seconds() / 60))
        raise HTTPException(429, f"Demasiados intentos fallidos. Espere {minutos} minutos o pida "
                                 "a su facilitador que le cambie el PIN.")
    if not verificar_pin(datos.pin, u.pin_hash):
        u.intentos_fallidos = (u.intentos_fallidos or 0) + 1
        quedan = MAX_INTENTOS - u.intentos_fallidos
        if quedan <= 0:
            u.bloqueado_hasta = ahora + timedelta(minutes=MINUTOS_BLOQUEO)
            u.intentos_fallidos = 0
            db.commit()
            raise HTTPException(429, f"Demasiados intentos fallidos. La cuenta quedó bloqueada "
                                     f"{MINUTOS_BLOQUEO} minutos.")
        db.commit()
        raise HTTPException(401, f"Número o PIN incorrecto. Le quedan {quedan} intentos.")
    if not u.activo:
        raise HTTPException(403, "Su cuenta está desactivada. Hable con su facilitador.")
    u.intentos_fallidos, u.bloqueado_hasta = 0, None
    db.commit()
    return _sesion(u)


@router.get("/yo")
def yo(u: Usuario = Depends(usuario_actual)):
    return {"id": u.id, "nombre": u.nombre, "rol": u.rol, "invitado": bool(u.invitado),
            "celular": None if u.invitado else u.celular,
            "grupo_id": u.grupo_id, "ultima_leccion_id": u.ultima_leccion_id}
