"""Modelo de datos (Figura 3 del documento maestro)."""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def ahora() -> datetime:
    return datetime.now()


class Grupo(Base):
    __tablename__ = "grupos"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80))
    facilitador_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL", use_alter=True, name="fk_grupos_facilitador"))
    creado: Mapped[datetime] = mapped_column(DateTime, default=ahora)


class Usuario(Base):
    __tablename__ = "usuarios"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80))
    celular: Mapped[str] = mapped_column(String(10), unique=True, index=True)
    pin_hash: Mapped[str] = mapped_column(String(100))
    rol: Mapped[str] = mapped_column(String(15), default="aprendiz")  # aprendiz | facilitador | administrador
    invitado: Mapped[bool] = mapped_column(Boolean, default=False)   # entró sin registrarse
    grupo_id: Mapped[int | None] = mapped_column(ForeignKey("grupos.id", ondelete="SET NULL"))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    intentos_fallidos: Mapped[int] = mapped_column(Integer, default=0)
    bloqueado_hasta: Mapped[datetime | None] = mapped_column(DateTime)
    ultima_leccion_id: Mapped[int | None] = mapped_column(ForeignKey("lecciones.id", ondelete="SET NULL"))
    creado: Mapped[datetime] = mapped_column(DateTime, default=ahora)


class Consentimiento(Base):
    __tablename__ = "consentimientos"
    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"))
    version: Mapped[str] = mapped_column(String(10))
    aceptado: Mapped[bool] = mapped_column(Boolean)
    fecha: Mapped[datetime] = mapped_column(DateTime, default=ahora)


class Modulo(Base):
    __tablename__ = "modulos"
    id: Mapped[int] = mapped_column(primary_key=True)
    orden: Mapped[int] = mapped_column(Integer)
    titulo: Mapped[str] = mapped_column(String(80))
    descripcion: Mapped[str] = mapped_column(Text, default="")
    icono: Mapped[str] = mapped_column(String(8), default="📘")
    nivel_bloom: Mapped[str] = mapped_column(String(40), default="")
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    lecciones: Mapped[list["Leccion"]] = relationship(
        back_populates="modulo", cascade="all, delete-orphan", order_by="Leccion.orden")


class Leccion(Base):
    __tablename__ = "lecciones"
    id: Mapped[int] = mapped_column(primary_key=True)
    modulo_id: Mapped[int] = mapped_column(ForeignKey("modulos.id", ondelete="CASCADE"))
    orden: Mapped[int] = mapped_column(Integer)
    titulo: Mapped[str] = mapped_column(String(100))
    para_que: Mapped[str] = mapped_column(Text, default="")
    situacion: Mapped[str] = mapped_column(Text, default="")   # caso de la vida real (andragogía)
    pasos: Mapped[str] = mapped_column(Text, default="[]")      # JSON: [{"icono","texto","consejo"}]
    glosario: Mapped[str] = mapped_column(Text, default="[]")   # JSON: [{"termino","definicion"}]
    recuerde: Mapped[str] = mapped_column(Text, default="[]")   # JSON: ["idea clave", ...]
    video_url: Mapped[str | None] = mapped_column(String(300))
    dispositivo: Mapped[str] = mapped_column(String(12), default="celular")  # celular | computador
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    modulo: Mapped[Modulo] = relationship(back_populates="lecciones")
    actividades: Mapped[list["Actividad"]] = relationship(
        back_populates="leccion", cascade="all, delete-orphan", order_by="Actividad.orden")


class Actividad(Base):
    __tablename__ = "actividades"
    id: Mapped[int] = mapped_column(primary_key=True)
    leccion_id: Mapped[int] = mapped_column(ForeignKey("lecciones.id", ondelete="CASCADE"))
    pregunta: Mapped[str] = mapped_column(Text)
    explicacion: Mapped[str] = mapped_column(Text, default="")
    orden: Mapped[int] = mapped_column(Integer, default=1)
    nivel_bloom: Mapped[str] = mapped_column(String(20), default="")
    leccion: Mapped[Leccion] = relationship(back_populates="actividades")
    opciones: Mapped[list["Opcion"]] = relationship(
        back_populates="actividad", cascade="all, delete-orphan")


class Opcion(Base):
    __tablename__ = "opciones"
    id: Mapped[int] = mapped_column(primary_key=True)
    actividad_id: Mapped[int] = mapped_column(ForeignKey("actividades.id", ondelete="CASCADE"))
    texto: Mapped[str] = mapped_column(String(200))
    correcta: Mapped[bool] = mapped_column(Boolean, default=False)
    retroalimentacion: Mapped[str] = mapped_column(Text, default="")  # por qué no es (si es incorrecta)
    actividad: Mapped[Actividad] = relationship(back_populates="opciones")


class Progreso(Base):
    __tablename__ = "progreso"
    __table_args__ = (UniqueConstraint("usuario_id", "leccion_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"))
    leccion_id: Mapped[int] = mapped_column(ForeignKey("lecciones.id", ondelete="CASCADE"))
    completada: Mapped[bool] = mapped_column(Boolean, default=False)
    fecha: Mapped[datetime] = mapped_column(DateTime, default=ahora)


class Respuesta(Base):
    __tablename__ = "respuestas"
    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"))
    actividad_id: Mapped[int] = mapped_column(ForeignKey("actividades.id", ondelete="CASCADE"))
    opcion_id: Mapped[int] = mapped_column(ForeignKey("opciones.id", ondelete="CASCADE"))
    correcta: Mapped[bool] = mapped_column(Boolean)
    fecha: Mapped[datetime] = mapped_column(DateTime, default=ahora)


class PreguntaDiagnostico(Base):
    __tablename__ = "preguntas_diagnostico"
    id: Mapped[int] = mapped_column(primary_key=True)
    orden: Mapped[int] = mapped_column(Integer)
    texto: Mapped[str] = mapped_column(String(200))
    modulo_id: Mapped[int] = mapped_column(ForeignKey("modulos.id", ondelete="CASCADE"))


class Diagnostico(Base):
    __tablename__ = "diagnosticos"
    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"))
    puntaje: Mapped[int] = mapped_column(Integer)          # 0-100
    modulo_recomendado_id: Mapped[int] = mapped_column(ForeignKey("modulos.id", ondelete="CASCADE"))
    fecha: Mapped[datetime] = mapped_column(DateTime, default=ahora)


class Certificado(Base):
    __tablename__ = "certificados"
    __table_args__ = (UniqueConstraint("usuario_id", "modulo_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"))
    modulo_id: Mapped[int] = mapped_column(ForeignKey("modulos.id", ondelete="CASCADE"))
    codigo: Mapped[str] = mapped_column(String(20), unique=True)
    fecha: Mapped[datetime] = mapped_column(DateTime, default=ahora)
