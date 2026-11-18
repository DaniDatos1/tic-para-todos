"""RF10 y RF11: CRUD de módulos, lecciones, actividades y usuarios; exportación CSV."""
import csv
import io
import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Actividad, Leccion, Modulo, Opcion, Respuesta, Usuario
from ..schemas import ActividadIn, LeccionIn, ModuloIn, UsuarioAdminIn
from ..security import hash_pin, requiere_rol
from ..servicios import leccion_dict, modulo_dict, resumen_avance

router = APIRouter(prefix="/api/admin", tags=["Administrador"])
solo_admin = requiere_rol("administrador")


def _obtener(db: Session, modelo, id_: int, nombre: str):
    obj = db.get(modelo, id_)
    if not obj:
        raise HTTPException(404, f"{nombre} no encontrado(a).")
    return obj


# ----------------- Módulos -----------------
@router.get("/modulos")
def listar_modulos(db: Session = Depends(get_db), _: Usuario = Depends(solo_admin)):
    return [modulo_dict(m) for m in db.scalars(select(Modulo).order_by(Modulo.orden))]


@router.post("/modulos", status_code=201)
def crear_modulo(datos: ModuloIn, db: Session = Depends(get_db), _: Usuario = Depends(solo_admin)):
    m = Modulo(**datos.model_dump())
    db.add(m)
    db.commit()
    return modulo_dict(m)


@router.put("/modulos/{modulo_id}")
def editar_modulo(modulo_id: int, datos: ModuloIn, db: Session = Depends(get_db),
                  _: Usuario = Depends(solo_admin)):
    m = _obtener(db, Modulo, modulo_id, "Módulo")
    for k, v in datos.model_dump().items():
        setattr(m, k, v)
    db.commit()
    return modulo_dict(m)


@router.delete("/modulos/{modulo_id}", status_code=204)
def eliminar_modulo(modulo_id: int, db: Session = Depends(get_db), _: Usuario = Depends(solo_admin)):
    db.delete(_obtener(db, Modulo, modulo_id, "Módulo"))
    db.commit()


# ----------------- Lecciones (con su actividad) -----------------
def _guardar_actividades(db: Session, l: Leccion, lista: list[ActividadIn]):
    for datos in lista:
        if sum(o.correcta for o in datos.opciones) != 1:
            raise HTTPException(400, "Cada pregunta debe tener exactamente una opción correcta.")
    for a in list(l.actividades):
        db.delete(a)
    db.flush()
    for k, datos in enumerate(lista, start=1):
        a = Actividad(leccion_id=l.id, orden=k, pregunta=datos.pregunta,
                      explicacion=datos.explicacion, nivel_bloom=datos.nivel_bloom)
        a.opciones = [Opcion(texto=o.texto, correcta=o.correcta,
                             retroalimentacion="" if o.correcta else o.retroalimentacion)
                      for o in datos.opciones]
        db.add(a)


def _asignar_campos(l: Leccion, datos: LeccionIn):
    l.modulo_id, l.orden, l.titulo = datos.modulo_id, datos.orden, datos.titulo
    l.para_que, l.situacion, l.video_url, l.activo = datos.para_que, datos.situacion, datos.video_url, datos.activo
    l.dispositivo = datos.dispositivo
    l.pasos = json.dumps([p.model_dump() for p in datos.pasos], ensure_ascii=False)
    l.glosario = json.dumps([g.model_dump() for g in datos.glosario], ensure_ascii=False)
    l.recuerde = json.dumps([r for r in datos.recuerde if r.strip()], ensure_ascii=False)


@router.get("/lecciones")
def listar_lecciones(modulo_id: int | None = None, db: Session = Depends(get_db),
                     _: Usuario = Depends(solo_admin)):
    q = select(Leccion).order_by(Leccion.modulo_id, Leccion.orden)
    if modulo_id:
        q = q.where(Leccion.modulo_id == modulo_id)
    return [leccion_dict(l, incluir_correctas=True) for l in db.scalars(q)]


@router.get("/lecciones/{leccion_id}")
def ver_leccion(leccion_id: int, db: Session = Depends(get_db), _: Usuario = Depends(solo_admin)):
    return leccion_dict(_obtener(db, Leccion, leccion_id, "Lección"), incluir_correctas=True)


@router.post("/lecciones", status_code=201)
def crear_leccion(datos: LeccionIn, db: Session = Depends(get_db), _: Usuario = Depends(solo_admin)):
    _obtener(db, Modulo, datos.modulo_id, "Módulo")
    l = Leccion()
    _asignar_campos(l, datos)
    db.add(l)
    db.flush()
    _guardar_actividades(db, l, datos.todas_las_actividades())
    db.commit()
    db.refresh(l)
    return leccion_dict(l, incluir_correctas=True)


@router.put("/lecciones/{leccion_id}")
def editar_leccion(leccion_id: int, datos: LeccionIn, db: Session = Depends(get_db),
                   _: Usuario = Depends(solo_admin)):
    l = _obtener(db, Leccion, leccion_id, "Lección")
    _obtener(db, Modulo, datos.modulo_id, "Módulo")
    _asignar_campos(l, datos)
    _guardar_actividades(db, l, datos.todas_las_actividades())
    db.commit()
    db.refresh(l)
    return leccion_dict(l, incluir_correctas=True)


@router.delete("/lecciones/{leccion_id}", status_code=204)
def eliminar_leccion(leccion_id: int, db: Session = Depends(get_db), _: Usuario = Depends(solo_admin)):
    l = _obtener(db, Leccion, leccion_id, "Lección")
    for u in db.scalars(select(Usuario).where(Usuario.ultima_leccion_id == l.id)):
        u.ultima_leccion_id = None
    db.delete(l)
    db.commit()


# ----------------- Usuarios -----------------
def _usuario_dict(u: Usuario) -> dict:
    return {"id": u.id, "nombre": u.nombre, "celular": u.celular, "rol": u.rol,
            "activo": u.activo, "grupo_id": u.grupo_id, "creado": u.creado.isoformat()}


@router.get("/usuarios")
def listar_usuarios(db: Session = Depends(get_db), _: Usuario = Depends(solo_admin)):
    # Los invitados no se listan: no tienen nombre ni celular. Aparecen en el reporte de progreso.
    return [_usuario_dict(u) for u in db.scalars(select(Usuario).where(Usuario.invitado.is_(False)).order_by(Usuario.id))]


@router.post("/usuarios", status_code=201)
def crear_usuario(datos: UsuarioAdminIn, db: Session = Depends(get_db), _: Usuario = Depends(solo_admin)):
    if not datos.pin:
        raise HTTPException(400, "Debe asignar un PIN.")
    if db.scalar(select(Usuario).where(Usuario.celular == datos.celular)):
        raise HTTPException(409, "Ese número de celular ya está registrado.")
    u = Usuario(nombre=datos.nombre, celular=datos.celular, rol=datos.rol,
                activo=datos.activo, pin_hash=hash_pin(datos.pin))
    db.add(u)
    db.commit()
    return _usuario_dict(u)


@router.put("/usuarios/{usuario_id}")
def editar_usuario(usuario_id: int, datos: UsuarioAdminIn, db: Session = Depends(get_db),
                   admin: Usuario = Depends(solo_admin)):
    u = _obtener(db, Usuario, usuario_id, "Usuario")
    otro = db.scalar(select(Usuario).where(Usuario.celular == datos.celular, Usuario.id != u.id))
    if otro:
        raise HTTPException(409, "Ese número de celular ya está registrado.")
    if u.id == admin.id and (datos.rol != "administrador" or not datos.activo):
        raise HTTPException(400, "No puede quitarse a sí mismo el rol de administrador.")
    u.nombre, u.celular, u.rol, u.activo = datos.nombre, datos.celular, datos.rol, datos.activo
    if datos.pin:
        u.pin_hash = hash_pin(datos.pin)
        u.intentos_fallidos, u.bloqueado_hasta = 0, None
    db.commit()
    return _usuario_dict(u)


@router.delete("/usuarios/{usuario_id}")
def desactivar_usuario(usuario_id: int, db: Session = Depends(get_db),
                       admin: Usuario = Depends(solo_admin)):
    """Eliminación lógica: se desactiva para conservar el historial del piloto."""
    u = _obtener(db, Usuario, usuario_id, "Usuario")
    if u.id == admin.id:
        raise HTTPException(400, "No puede desactivar su propia cuenta.")
    u.activo = False
    db.commit()
    return _usuario_dict(u)


# ----------------- RF11: reporte CSV -----------------
def _celda_segura(v):
    """Evita la inyección de fórmulas al abrir el CSV en Excel (=, +, -, @)."""
    if isinstance(v, str) and v[:1] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + v
    return v


@router.get("/reportes/progreso.csv")
def reporte_csv(db: Session = Depends(get_db), _: Usuario = Depends(solo_admin)):
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=";")
    modulos = db.scalars(select(Modulo).where(Modulo.activo).order_by(Modulo.orden)).all()
    w.writerow(["id", "nombre", "rol", "tipo", "grupo_id", "fecha_registro", "lecciones_completadas",
                "porcentaje_total", *[f"% {m.titulo}" for m in modulos],
                "respuestas", "respuestas_correctas"])
    for u in db.scalars(select(Usuario).where(Usuario.rol == "aprendiz").order_by(Usuario.id)):
        r = resumen_avance(db, u)
        por_mod = {x["modulo_id"]: x["porcentaje"] for x in r["modulos"]}
        n_resp = db.scalar(select(func.count()).where(Respuesta.usuario_id == u.id))
        n_ok = db.scalar(select(func.count()).where(Respuesta.usuario_id == u.id, Respuesta.correcta))
        w.writerow([u.id, _celda_segura(u.nombre), u.rol, "invitado" if u.invitado else "registrado", u.grupo_id or "", u.creado.strftime("%Y-%m-%d"),
                    r["completadas"], r["porcentaje"], *[por_mod.get(m.id, 0) for m in modulos],
                    n_resp, n_ok])
    return StreamingResponse(iter(["﻿" + buf.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": 'attachment; filename="reporte_progreso.csv"'})
