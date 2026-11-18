"""Punto de entrada de la API REST y del servidor de la PWA.

Ejecutar desde la carpeta backend/:
    uvicorn app.main:app --reload
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from sqlalchemy import inspect, text
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import models  # noqa: F401  (registra las tablas)
from .config import FRONTEND_DIR
from .database import Base, SessionLocal, engine
from .routers import admin, aprendiz, auth, facilitador
from .seed import sembrar


COLUMNAS_NUEVAS = {  # tabla: [(columna, definición SQL)]
    "lecciones": [("situacion", "TEXT DEFAULT ''"), ("glosario", "TEXT DEFAULT '[]'"),
                  ("recuerde", "TEXT DEFAULT '[]'"), ("dispositivo", "VARCHAR(12) DEFAULT 'celular'")],
    "actividades": [("orden", "INTEGER DEFAULT 1"), ("nivel_bloom", "VARCHAR(20) DEFAULT ''")],
    "opciones": [("retroalimentacion", "TEXT DEFAULT ''")],
    "usuarios": [("intentos_fallidos", "INTEGER DEFAULT 0"), ("bloqueado_hasta", "TIMESTAMP"),
                 ("invitado", "BOOLEAN DEFAULT 0")],
}


def migrar():
    """Agrega columnas que no existan (bases de datos creadas con una versión anterior)."""
    insp = inspect(engine)
    with engine.begin() as con:
        for tabla, cols in COLUMNAS_NUEVAS.items():
            if not insp.has_table(tabla):
                continue
            existentes = {c["name"] for c in insp.get_columns(tabla)}
            for nombre, definicion in cols:
                if nombre not in existentes:
                    con.execute(text(f"ALTER TABLE {tabla} ADD COLUMN {nombre} {definicion}"))


@asynccontextmanager
async def ciclo_vida(_: FastAPI):
    Base.metadata.create_all(engine)
    migrar()
    with SessionLocal() as db:
        sembrar(db)
    yield


app = FastAPI(
    title="TIC para Todos - API",
    description="Plataforma web de alfabetización digital para comunidades vulnerables de Valledupar.",
    version="1.0.0",
    lifespan=ciclo_vida,
)

for r in (auth.router, aprendiz.router, facilitador.router, admin.router):
    app.include_router(r)


@app.middleware("http")
async def cabeceras_seguridad(request: Request, call_next):
    """Cabeceras HTTP de seguridad para todas las respuestas."""
    resp = await call_next(request)
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("X-Frame-Options", "DENY")
    resp.headers.setdefault("Referrer-Policy", "no-referrer")
    resp.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    if not request.url.path.startswith(("/docs", "/redoc", "/openapi")):
        resp.headers.setdefault("Content-Security-Policy",
                                "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
                                "script-src 'self' 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'; "
                                "base-uri 'self'; form-action 'self'")
    if request.url.path.startswith("/api/"):
        resp.headers.setdefault("Cache-Control", "no-store")
    return resp


@app.get("/api/salud", tags=["Sistema"])
def salud():
    return {"estado": "ok"}


@app.get("/sw.js", include_in_schema=False)
def service_worker():
    # El service worker debe servirse desde la raíz para controlar toda la app
    return FileResponse(FRONTEND_DIR / "sw.js", media_type="application/javascript",
                        headers={"Cache-Control": "no-cache"})


app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
