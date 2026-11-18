import os
import tempfile

import pytest

# Base de datos temporal, aislada de la de desarrollo
# (TEST_DATABASE_URL permite correr las mismas pruebas contra PostgreSQL)
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["DATABASE_URL"] = os.getenv("TEST_DATABASE_URL", f"sqlite:///{_tmp.name}")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


def _login(client, celular, pin="1234"):
    r = client.post("/api/auth/login", json={"celular": celular, "pin": pin})
    assert r.status_code == 200, r.text
    return {"Authorization": "Bearer " + r.json()["token"]}


@pytest.fixture(scope="session")
def admin(client):
    return _login(client, "3000000001")


@pytest.fixture(scope="session")
def facilitador(client):
    return _login(client, "3000000002")


@pytest.fixture(scope="session")
def aprendiz(client):
    r = client.post("/api/auth/registro", json={
        "nombre": "Aprendiz Prueba", "celular": "3109998877", "pin": "2468", "acepta_datos": True})
    assert r.status_code == 201, r.text
    return {"Authorization": "Bearer " + r.json()["token"]}
