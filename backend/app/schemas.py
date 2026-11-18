"""Esquemas de entrada (validación con Pydantic)."""
from typing import Literal

from pydantic import BaseModel, Field, field_validator

CELULAR = r"^3\d{9}$"   # celular colombiano de 10 dígitos
PIN = r"^\d{4}$"


def pin_trivial(pin: str) -> bool:
    """PIN fáciles de adivinar: todos iguales (0000) o consecutivos (1234, 4321)."""
    if len(set(pin)) == 1:
        return True
    d = [int(c) for c in pin]
    pasos = {d[i + 1] - d[i] for i in range(len(d) - 1)}
    return pasos in ({1}, {-1})


def _validar_pin(v: str | None) -> str | None:
    if v is not None and pin_trivial(v):
        raise ValueError("PIN demasiado fácil de adivinar (evite 1234, 0000 o similares)")
    return v


class RegistroIn(BaseModel):
    nombre: str = Field(min_length=2, max_length=80)
    celular: str = Field(pattern=CELULAR)
    pin: str = Field(pattern=PIN)
    acepta_datos: bool

    _pin = field_validator("pin")(_validar_pin)


class LoginIn(BaseModel):
    celular: str = Field(pattern=CELULAR)
    pin: str = Field(pattern=PIN)


class DiagnosticoIn(BaseModel):
    # pregunta_id -> 0 (no sé), 1 (con ayuda), 2 (lo hago solo)
    respuestas: dict[int, int]


class RespuestaIn(BaseModel):
    opcion_id: int


class ModuloIn(BaseModel):
    orden: int = Field(ge=1)
    titulo: str = Field(min_length=2, max_length=80)
    descripcion: str = ""
    icono: str = "📘"
    nivel_bloom: str = ""
    activo: bool = True


class Paso(BaseModel):
    icono: str = "👉"
    texto: str = Field(min_length=1)
    consejo: str = ""


class Termino(BaseModel):
    termino: str = Field(min_length=1, max_length=60)
    definicion: str = Field(min_length=1)


class OpcionIn(BaseModel):
    texto: str = Field(min_length=1, max_length=200)
    correcta: bool = False
    retroalimentacion: str = ""


class ActividadIn(BaseModel):
    pregunta: str = Field(min_length=3)
    explicacion: str = ""
    nivel_bloom: str = ""
    opciones: list[OpcionIn] = Field(min_length=2)


class LeccionIn(BaseModel):
    modulo_id: int
    orden: int = Field(ge=1)
    titulo: str = Field(min_length=2, max_length=100)
    para_que: str = ""
    situacion: str = ""
    pasos: list[Paso] = Field(min_length=1)
    glosario: list[Termino] = []
    recuerde: list[str] = []
    video_url: str | None = None
    dispositivo: Literal["celular", "computador"] = "celular"
    activo: bool = True
    actividades: list[ActividadIn] = []
    actividad: ActividadIn | None = None   # compatibilidad: una sola actividad

    def todas_las_actividades(self) -> list[ActividadIn]:
        return self.actividades or ([self.actividad] if self.actividad else [])


class GrupoIn(BaseModel):
    nombre: str = Field(min_length=2, max_length=80)


class InscribirIn(BaseModel):
    celular: str = Field(pattern=CELULAR)


class UsuarioAdminIn(BaseModel):
    nombre: str = Field(min_length=2, max_length=80)
    celular: str = Field(pattern=CELULAR)
    pin: str | None = Field(default=None, pattern=PIN)
    rol: str = Field(pattern=r"^(aprendiz|facilitador|administrador)$")
    activo: bool = True

    _pin = field_validator("pin")(_validar_pin)


class ResetPinIn(BaseModel):
    pin_nuevo: str = Field(pattern=PIN)

    _pin = field_validator("pin_nuevo")(_validar_pin)


class InvitadoIn(BaseModel):
    """Entrada sin registro. Si el dispositivo ya tiene código y clave de invitado, se recupera
    ese mismo usuario (y su avance); si no, se crea uno nuevo."""
    codigo: str | None = Field(default=None, max_length=10)
    clave: str | None = Field(default=None, max_length=64)
