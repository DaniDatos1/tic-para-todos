"""Capa de datos: motor SQLAlchemy y sesión por petición."""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import DATABASE_URL

_es_sqlite = DATABASE_URL.startswith("sqlite")
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if _es_sqlite else {},
    pool_pre_ping=not _es_sqlite,   # en la nube, revisa la conexión antes de usarla
)

if _es_sqlite:
    @event.listens_for(engine, "connect")
    def _activar_fk(conn, _):
        conn.execute("PRAGMA foreign_keys=ON")

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
