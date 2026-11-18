"""Lógica de negocio compartida: cálculo de avance y serialización de contenidos."""
import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Leccion, Modulo, Progreso, Usuario


def lecciones_completadas(db: Session, usuario_id: int) -> set[int]:
    return set(db.scalars(
        select(Progreso.leccion_id).where(Progreso.usuario_id == usuario_id, Progreso.completada)))


def avance_por_modulo(db: Session, usuario: Usuario) -> list[dict]:
    hechas = lecciones_completadas(db, usuario.id)
    modulos = db.scalars(select(Modulo).where(Modulo.activo).order_by(Modulo.orden)).all()
    salida = []
    for m in modulos:
        ids = [l.id for l in m.lecciones if l.activo]
        n_hechas = len([i for i in ids if i in hechas])
        salida.append({
            "modulo_id": m.id, "orden": m.orden, "titulo": m.titulo, "icono": m.icono,
            "total": len(ids), "completadas": n_hechas,
            "porcentaje": round(100 * n_hechas / len(ids)) if ids else 0,
            "terminado": bool(ids) and n_hechas == len(ids),
        })
    return salida


def resumen_avance(db: Session, usuario: Usuario) -> dict:
    modulos = avance_por_modulo(db, usuario)
    total = sum(m["total"] for m in modulos)
    hechas = sum(m["completadas"] for m in modulos)
    return {
        "total": total, "completadas": hechas,
        "porcentaje": round(100 * hechas / total) if total else 0,
        "modulos": modulos,
    }


def leccion_dict(l: Leccion, incluir_correctas: bool = False) -> dict:
    return {
        "id": l.id, "modulo_id": l.modulo_id, "orden": l.orden, "titulo": l.titulo,
        "para_que": l.para_que, "situacion": l.situacion or "",
        "pasos": json.loads(l.pasos or "[]"), "glosario": json.loads(l.glosario or "[]"),
        "recuerde": json.loads(l.recuerde or "[]"),
        "video_url": l.video_url, "dispositivo": l.dispositivo or "celular", "activo": l.activo,
        "actividades": [{
            "id": a.id, "pregunta": a.pregunta, "nivel_bloom": a.nivel_bloom,
            **({"explicacion": a.explicacion} if incluir_correctas else {}),
            "opciones": [{"id": o.id, "texto": o.texto,
                          **({"correcta": o.correcta, "retroalimentacion": o.retroalimentacion or ""}
                             if incluir_correctas else {})}
                         for o in a.opciones],
        } for a in l.actividades],
    }


def modulo_dict(m: Modulo) -> dict:
    return {"id": m.id, "orden": m.orden, "titulo": m.titulo, "descripcion": m.descripcion,
            "icono": m.icono, "nivel_bloom": m.nivel_bloom, "activo": m.activo,
            "num_lecciones": len([l for l in m.lecciones if l.activo])}
