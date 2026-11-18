"""Configuración central de la aplicación (variables de entorno con valores por defecto)."""
import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent          # carpeta backend/
PROJECT_DIR = BASE_DIR.parent                               # raíz del repositorio
FRONTEND_DIR = PROJECT_DIR / "frontend"

# SQLite en desarrollo; en producción se usa PostgreSQL, p. ej.:
# DATABASE_URL=postgresql+psycopg://usuario:clave@localhost:5432/aprendo
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'aprendo.db'}")
# Los servicios en la nube (Render, Railway, Heroku) entregan la dirección como postgres:// o
# postgresql://; SQLAlchemy necesita que se indique el controlador psycopg.
for _prefijo in ("postgres://", "postgresql://"):
    if DATABASE_URL.startswith(_prefijo):
        DATABASE_URL = "postgresql+psycopg://" + DATABASE_URL[len(_prefijo):]
        break

def _clave_secreta() -> str:
    """Clave para firmar las sesiones. Se toma de la variable de entorno SECRET_KEY; si no
    existe, se genera una aleatoria la primera vez y se guarda en backend/.secret_key
    (archivo excluido del repositorio)."""
    if os.getenv("SECRET_KEY"):
        return os.environ["SECRET_KEY"]
    archivo = BASE_DIR / ".secret_key"
    try:
        if archivo.exists():
            return archivo.read_text().strip()
        clave = secrets.token_hex(32)
        archivo.write_text(clave)
        return clave
    except OSError:
        return secrets.token_hex(32)


SECRET_KEY = _clave_secreta()
TOKEN_HORAS = int(os.getenv("TOKEN_HORAS", "12"))

# Protección contra adivinar el PIN: tras MAX_INTENTOS fallidos la cuenta se bloquea un tiempo
MAX_INTENTOS = int(os.getenv("MAX_INTENTOS", "5"))
MINUTOS_BLOQUEO = int(os.getenv("MINUTOS_BLOQUEO", "15"))

CONSENTIMIENTO_VERSION = "1.0"

# Porcentaje mínimo de la prueba diagnóstica para considerar dominado un módulo
UMBRAL_DOMINIO = 0.7
