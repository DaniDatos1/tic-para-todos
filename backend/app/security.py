"""Autenticación: PIN con bcrypt (RNF05) y token firmado con HMAC."""
import base64
import hashlib
import hmac
import time

import bcrypt
from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from .config import SECRET_KEY, TOKEN_HORAS
from .database import get_db
from .models import Usuario


def hash_pin(pin: str) -> str:
    return bcrypt.hashpw(pin.encode(), bcrypt.gensalt()).decode()


def verificar_pin(pin: str, pin_hash: str) -> bool:
    return bcrypt.checkpw(pin.encode(), pin_hash.encode())


def _firma(datos: str) -> str:
    return hmac.new(SECRET_KEY.encode(), datos.encode(), hashlib.sha256).hexdigest()


def crear_token(usuario_id: int) -> str:
    exp = int(time.time()) + TOKEN_HORAS * 3600
    datos = f"{usuario_id}:{exp}"
    return base64.urlsafe_b64encode(f"{datos}:{_firma(datos)}".encode()).decode()


def leer_token(token: str) -> int | None:
    try:
        uid, exp, firma = base64.urlsafe_b64decode(token.encode()).decode().split(":")
    except Exception:
        return None
    if not hmac.compare_digest(firma, _firma(f"{uid}:{exp}")) or int(exp) < time.time():
        return None
    return int(uid)


def usuario_actual(authorization: str = Header(default=""), db: Session = Depends(get_db)) -> Usuario:
    token = authorization.removeprefix("Bearer ").strip()
    uid = leer_token(token) if token else None
    usuario = db.get(Usuario, uid) if uid else None
    if not usuario or not usuario.activo:
        raise HTTPException(401, "Sesión no válida. Vuelva a iniciar sesión.")
    return usuario


def requiere_rol(*roles: str):
    def _dep(usuario: Usuario = Depends(usuario_actual)) -> Usuario:
        if usuario.rol not in roles:
            raise HTTPException(403, "No tiene permiso para esta acción.")
        return usuario
    return _dep
