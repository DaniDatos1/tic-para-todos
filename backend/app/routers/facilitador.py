"""RF09 y RF02 (recuperación de acceso): grupos, inscripción y avance del grupo."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Grupo, Usuario
from ..schemas import GrupoIn, InscribirIn, ResetPinIn
from ..security import hash_pin, requiere_rol
from ..servicios import resumen_avance

router = APIRouter(prefix="/api/facilitador", tags=["Facilitador"])
solo_facilitador = requiere_rol("facilitador", "administrador")


def _grupo_propio(db: Session, grupo_id: int, f: Usuario) -> Grupo:
    g = db.get(Grupo, grupo_id)
    if not g or (f.rol != "administrador" and g.facilitador_id != f.id):
        raise HTTPException(404, "Grupo no encontrado.")
    return g


@router.get("/grupos")
def mis_grupos(db: Session = Depends(get_db), f: Usuario = Depends(solo_facilitador)):
    q = select(Grupo).order_by(Grupo.id)
    if f.rol != "administrador":
        q = q.where(Grupo.facilitador_id == f.id)
    salida = []
    for g in db.scalars(q):
        n = len(db.scalars(select(Usuario.id).where(Usuario.grupo_id == g.id)).all())
        salida.append({"id": g.id, "nombre": g.nombre, "aprendices": n})
    return salida


@router.post("/grupos", status_code=201)
def crear_grupo(datos: GrupoIn, db: Session = Depends(get_db), f: Usuario = Depends(solo_facilitador)):
    g = Grupo(nombre=datos.nombre.strip(), facilitador_id=f.id)
    db.add(g)
    db.commit()
    return {"id": g.id, "nombre": g.nombre}


@router.post("/grupos/{grupo_id}/inscribir")
def inscribir(grupo_id: int, datos: InscribirIn, db: Session = Depends(get_db),
              f: Usuario = Depends(solo_facilitador)):
    g = _grupo_propio(db, grupo_id, f)
    a = db.scalar(select(Usuario).where(Usuario.celular == datos.celular))
    if not a or a.rol != "aprendiz":
        raise HTTPException(404, "No hay un aprendiz registrado con ese celular.")
    a.grupo_id = g.id
    db.commit()
    return {"ok": True, "aprendiz": a.nombre}


@router.get("/grupos/{grupo_id}/avance")
def avance_grupo(grupo_id: int, db: Session = Depends(get_db), f: Usuario = Depends(solo_facilitador)):
    g = _grupo_propio(db, grupo_id, f)
    aprendices = db.scalars(select(Usuario).where(Usuario.grupo_id == g.id).order_by(Usuario.nombre))
    return {"grupo": g.nombre, "aprendices": [
        {"id": a.id, "nombre": a.nombre, "celular": a.celular, **resumen_avance(db, a)}
        for a in aprendices]}


@router.post("/aprendices/{aprendiz_id}/restablecer-pin")
def restablecer_pin(aprendiz_id: int, datos: ResetPinIn, db: Session = Depends(get_db),
                    f: Usuario = Depends(solo_facilitador)):
    a = db.get(Usuario, aprendiz_id)
    if not a or a.rol != "aprendiz":
        raise HTTPException(404, "Aprendiz no encontrado.")
    if f.rol != "administrador":
        _grupo_propio(db, a.grupo_id or 0, f)
    a.pin_hash = hash_pin(datos.pin_nuevo)
    a.intentos_fallidos, a.bloqueado_hasta = 0, None   # desbloquea la cuenta
    db.commit()
    return {"ok": True}
