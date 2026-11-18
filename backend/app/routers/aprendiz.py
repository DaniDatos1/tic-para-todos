"""RF03-RF08: diagnóstico, rutas, lecciones, actividades, progreso y certificados."""
import secrets

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..certificado import generar_pdf
from ..config import UMBRAL_DOMINIO
from ..database import get_db
from ..models import (Actividad, Certificado, Diagnostico, Leccion, Modulo, Opcion,
                      PreguntaDiagnostico, Progreso, Respuesta, Usuario)
from ..schemas import DiagnosticoIn, RespuestaIn
from ..security import usuario_actual
from ..servicios import (avance_por_modulo, leccion_dict, lecciones_completadas, modulo_dict,
                         resumen_avance)

router = APIRouter(prefix="/api", tags=["Aprendiz"])


# ---------- RF03: prueba diagnóstica ----------
@router.get("/diagnostico/preguntas")
def preguntas_diagnostico(db: Session = Depends(get_db), _: Usuario = Depends(usuario_actual)):
    ps = db.scalars(select(PreguntaDiagnostico).order_by(PreguntaDiagnostico.orden)).all()
    return [{"id": p.id, "texto": p.texto} for p in ps]


@router.post("/diagnostico")
def responder_diagnostico(datos: DiagnosticoIn, db: Session = Depends(get_db),
                          u: Usuario = Depends(usuario_actual)):
    preguntas = db.scalars(select(PreguntaDiagnostico)).all()
    if not preguntas or set(datos.respuestas) != {p.id for p in preguntas}:
        raise HTTPException(400, "Debe responder todas las preguntas.")
    if any(v not in (0, 1, 2) for v in datos.respuestas.values()):
        raise HTTPException(400, "Respuesta no válida.")

    por_modulo: dict[int, list[int]] = {}
    for p in preguntas:
        por_modulo.setdefault(p.modulo_id, []).append(datos.respuestas[p.id])
    modulos = db.scalars(select(Modulo).where(Modulo.activo).order_by(Modulo.orden)).all()
    # Se recomienda el primer módulo (en orden) que no esté dominado
    recomendado = modulos[-1]
    for m in modulos:
        vals = por_modulo.get(m.id, [])
        if vals and sum(vals) / (2 * len(vals)) < UMBRAL_DOMINIO:
            recomendado = m
            break
    puntaje = round(100 * sum(datos.respuestas.values()) / (2 * len(preguntas)))
    db.add(Diagnostico(usuario_id=u.id, puntaje=puntaje, modulo_recomendado_id=recomendado.id))
    db.commit()
    return {"puntaje": puntaje, "modulo_recomendado": modulo_dict(recomendado)}


# ---------- RF04: rutas de aprendizaje ----------
@router.get("/rutas")
def rutas(db: Session = Depends(get_db), u: Usuario = Depends(usuario_actual)):
    modulos = db.scalars(select(Modulo).where(Modulo.activo).order_by(Modulo.orden)).all()
    avance = {a["modulo_id"]: a for a in avance_por_modulo(db, u)}
    diag = db.scalar(select(Diagnostico).where(Diagnostico.usuario_id == u.id)
                     .order_by(Diagnostico.id.desc()))
    ul = db.get(Leccion, u.ultima_leccion_id) if u.ultima_leccion_id else None
    return {
        "recomendado_id": diag.modulo_recomendado_id if diag else None,
        "hizo_diagnostico": diag is not None,
        "ultima_leccion_id": u.ultima_leccion_id,
        "ultima_leccion": {"id": ul.id, "titulo": ul.titulo, "modulo_titulo": ul.modulo.titulo,
                           "modulo_orden": ul.modulo.orden} if ul and ul.activo else None,
        "modulos": [{**modulo_dict(m), "avance": avance.get(m.id)} for m in modulos],
    }


@router.get("/modulos/{modulo_id}")
def ver_modulo(modulo_id: int, db: Session = Depends(get_db), u: Usuario = Depends(usuario_actual)):
    m = db.get(Modulo, modulo_id)
    if not m or not m.activo:
        raise HTTPException(404, "Módulo no encontrado.")
    hechas = lecciones_completadas(db, u.id)
    return {**modulo_dict(m), "lecciones": [
        {"id": l.id, "orden": l.orden, "titulo": l.titulo, "para_que": l.para_que,
         "dispositivo": l.dispositivo or "celular", "completada": l.id in hechas}
        for l in m.lecciones if l.activo]}


# ---------- RF05: lección ----------
@router.get("/lecciones/{leccion_id}")
def ver_leccion(leccion_id: int, db: Session = Depends(get_db), u: Usuario = Depends(usuario_actual)):
    l = db.get(Leccion, leccion_id)
    if not l or not l.activo:
        raise HTTPException(404, "Lección no encontrada.")
    u.ultima_leccion_id = l.id               # RF07: recordar dónde quedó
    db.commit()
    hermanas = [x for x in l.modulo.lecciones if x.activo]
    pos = hermanas.index(l)
    return {**leccion_dict(l), "modulo_titulo": l.modulo.titulo,
            "posicion": pos + 1, "total": len(hermanas),
            "anterior_id": hermanas[pos - 1].id if pos > 0 else None,
            "siguiente_id": hermanas[pos + 1].id if pos + 1 < len(hermanas) else None,
            "completada": l.id in lecciones_completadas(db, u.id)}


# ---------- RF06: actividad con retroalimentación inmediata ----------
@router.post("/actividades/{actividad_id}/responder")
def responder(actividad_id: int, datos: RespuestaIn, db: Session = Depends(get_db),
              u: Usuario = Depends(usuario_actual)):
    a = db.get(Actividad, actividad_id)
    op = db.get(Opcion, datos.opcion_id)
    if not a or not op or op.actividad_id != a.id:
        raise HTTPException(404, "Actividad u opción no encontrada.")
    db.add(Respuesta(usuario_id=u.id, actividad_id=a.id, opcion_id=op.id, correcta=op.correcta))
    db.flush()
    # La lección se completa cuando el aprendiz ha acertado TODAS sus preguntas
    ids = {x.id for x in a.leccion.actividades}
    acertadas = set(db.scalars(select(Respuesta.actividad_id).where(
        Respuesta.usuario_id == u.id, Respuesta.correcta, Respuesta.actividad_id.in_(ids))))
    completada = acertadas >= ids
    if completada:
        _marcar_completada(db, u.id, a.leccion_id)
    db.commit()
    correcta = next(o for o in a.opciones if o.correcta)
    return {"correcta": op.correcta, "explicacion": a.explicacion if op.correcta else "",
            "retroalimentacion": "" if op.correcta else (op.retroalimentacion or ""),
            "opcion_correcta_id": correcta.id if op.correcta else None,
            "leccion_completada": completada}


def _marcar_completada(db: Session, usuario_id: int, leccion_id: int):
    p = db.scalar(select(Progreso).where(Progreso.usuario_id == usuario_id,
                                         Progreso.leccion_id == leccion_id))
    if p:
        p.completada = True
    else:
        db.add(Progreso(usuario_id=usuario_id, leccion_id=leccion_id, completada=True))


@router.post("/lecciones/{leccion_id}/completar")
def completar(leccion_id: int, db: Session = Depends(get_db), u: Usuario = Depends(usuario_actual)):
    """Para lecciones sin actividad: se marcan completadas al terminar de leerlas."""
    l = db.get(Leccion, leccion_id)
    if not l:
        raise HTTPException(404, "Lección no encontrada.")
    if l.actividades:
        raise HTTPException(400, "Responda la actividad para completar esta lección.")
    _marcar_completada(db, u.id, l.id)
    db.commit()
    return {"ok": True}


# ---------- RF07: progreso ----------
@router.get("/progreso")
def progreso(db: Session = Depends(get_db), u: Usuario = Depends(usuario_actual)):
    return {**resumen_avance(db, u), "ultima_leccion_id": u.ultima_leccion_id}


# ---------- RF08: certificado PDF ----------
@router.get("/certificados/{modulo_id}")
def certificado(modulo_id: int, db: Session = Depends(get_db), u: Usuario = Depends(usuario_actual)):
    m = db.get(Modulo, modulo_id)
    if not m:
        raise HTTPException(404, "Módulo no encontrado.")
    if u.invitado:
        raise HTTPException(403, "Para recibir su certificado con su nombre, primero toque Guardar mi avance.")
    av = next((a for a in avance_por_modulo(db, u) if a["modulo_id"] == m.id), None)
    if not av or not av["terminado"]:
        raise HTTPException(400, "Termine todas las lecciones del módulo para obtener el certificado.")
    c = db.scalar(select(Certificado).where(Certificado.usuario_id == u.id,
                                            Certificado.modulo_id == m.id))
    if not c:
        c = Certificado(usuario_id=u.id, modulo_id=m.id, codigo=secrets.token_hex(4).upper())
        db.add(c)
        db.commit()
    pdf = generar_pdf(u.nombre, m.titulo, av["total"], c.codigo, c.fecha)
    return Response(pdf, media_type="application/pdf", headers={
        "Content-Disposition": f'attachment; filename="certificado_{m.orden}_{c.codigo}.pdf"'})
