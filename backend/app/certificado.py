"""RF08: generación del certificado de participación en PDF con ReportLab."""
from datetime import datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.pdfgen import canvas

AZUL = colors.HexColor("#1F4E8C")
VERDE = colors.HexColor("#2E7D4F")
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]


def generar_pdf(nombre: str, modulo: str, lecciones: int, codigo: str, fecha: datetime) -> bytes:
    buf = BytesIO()
    w, h = landscape(letter)
    c = canvas.Canvas(buf, pagesize=(w, h))
    c.setTitle(f"Certificado - {modulo}")

    c.setStrokeColor(AZUL)
    c.setLineWidth(6)
    c.rect(30, 30, w - 60, h - 60)
    c.setLineWidth(1.5)
    c.rect(42, 42, w - 84, h - 84)

    c.setFillColor(AZUL)
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(w / 2, h - 95, "TIC PARA TODOS")
    c.setFont("Helvetica", 11)
    c.setFillColor(colors.black)
    c.drawCentredString(w / 2, h - 113, "Plataforma de alfabetización digital - Valledupar, Cesar")

    c.setFont("Helvetica-Bold", 30)
    c.setFillColor(AZUL)
    c.drawCentredString(w / 2, h - 175, "Certificado de participación")

    c.setFillColor(colors.black)
    c.setFont("Helvetica", 14)
    c.drawCentredString(w / 2, h - 220, "Se certifica que")
    c.setFont("Helvetica-Bold", 26)
    c.drawCentredString(w / 2, h - 262, nombre)
    c.setStrokeColor(colors.grey)
    c.line(w / 2 - 220, h - 272, w / 2 + 220, h - 272)

    c.setFont("Helvetica", 14)
    c.drawCentredString(w / 2, h - 305, "completó satisfactoriamente el módulo")
    c.setFont("Helvetica-Bold", 20)
    c.setFillColor(VERDE)
    c.drawCentredString(w / 2, h - 338, f"«{modulo}»")
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 12)
    c.drawCentredString(w / 2, h - 362, f"({lecciones} lecciones de autoaprendizaje)")

    f = f"{fecha.day} de {MESES[fecha.month - 1]} de {fecha.year}"
    c.drawCentredString(w / 2, h - 400, f"Valledupar, {f}")

    c.setFont("Helvetica", 9)
    c.setFillColor(colors.grey)
    c.drawString(60, 60, f"Código de verificación: {codigo}")
    c.drawRightString(w - 60, 60, "Proyecto de grado - Ingeniería de Sistemas - UNAD")
    c.showPage()
    c.save()
    return buf.getvalue()
