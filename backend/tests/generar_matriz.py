"""Ejecuta las pruebas y genera la matriz de casos de prueba (CSV y Markdown) para el documento.

Uso (desde backend/):  python tests/generar_matriz.py
Salida: ../docs/matriz_casos_prueba.csv y ../docs/matriz_casos_prueba.md
"""
import csv
import sys
from datetime import date
from pathlib import Path

import pytest

DOCS = Path(__file__).resolve().parents[2] / "docs"


class Recolector:
    def __init__(self):
        self.casos = {}

    def pytest_runtest_logreport(self, report):
        if report.when != "call" and not (report.when == "setup" and report.failed):
            return
        item = self.items.get(report.nodeid)
        m = item.get_closest_marker("caso") if item else None
        if not m:
            return
        cid, rf, desc = m.args
        c = self.casos.setdefault(cid, {"id": cid, "rf": rf, "desc": desc, "prueba": item.originalname,
                                        "ejecuciones": 0, "fallas": 0})
        c["ejecuciones"] += 1
        c["fallas"] += int(report.failed)

    def pytest_collection_finish(self, session):
        self.items = {i.nodeid: i for i in session.items}


def main():
    r = Recolector()
    codigo = pytest.main(["-q", "tests"], plugins=[r])
    casos = sorted(r.casos.values(), key=lambda c: c["id"])
    if not casos:
        sys.exit("No se ejecutaron pruebas. Ejecute el script desde la carpeta backend/.")
    DOCS.mkdir(exist_ok=True)
    hoy = date.today().isoformat()
    with open(DOCS / "matriz_casos_prueba.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["ID", "Requerimiento", "Descripción", "Prueba automatizada", "Resultado", "Fecha"])
        for c in casos:
            w.writerow([c["id"], c["rf"], c["desc"], c["prueba"],
                        "Aprobado" if not c["fallas"] else "Fallido", hoy])
    ok = sum(1 for c in casos if not c["fallas"])
    with open(DOCS / "matriz_casos_prueba.md", "w", encoding="utf-8") as f:
        f.write(f"# Matriz de casos de prueba\n\nEjecución: {hoy}. Aprobados: {ok} de {len(casos)} "
                f"({round(100 * ok / len(casos))} %).\n\n")
        f.write("| ID | Req. | Descripción | Resultado |\n|---|---|---|---|\n")
        for c in casos:
            f.write(f"| {c['id']} | {c['rf']} | {c['desc']} | {'Aprobado' if not c['fallas'] else 'Fallido'} |\n")
    print(f"\nMatriz generada en {DOCS}: {ok}/{len(casos)} casos aprobados.")
    sys.exit(codigo)


if __name__ == "__main__":
    main()
