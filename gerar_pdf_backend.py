from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from datetime import datetime
import io
import os

app = Flask(__name__)
CORS(app)

VERDE = HexColor("#2F4A3F")
DOURADO = HexColor("#B08D57")
TEXTO = HexColor("#2C1E16")
OFFWHITE = HexColor("#F6F4EF")

def format_money(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

@app.route("/gerar", methods=["POST"])
def gerar():
    data = request.json or {}
    nome = data.get("nome", "CONDOMINIO").upper()
    hoje = datetime.now()
    data_str = hoje.strftime("%d/%m/%Y")
    arquivo_data = hoje.strftime("%Y.%m.%d")

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4

    # Cabeçalho
    c.setFillColor(VERDE)
    c.rect(0, h - 40*mm, w, 40*mm, fill=1, stroke=0)
    c.setFillColor(OFFWHITE)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(20*mm, h - 22*mm, "ATLAS HALL")
    c.setFont("Helvetica", 10)
    c.drawString(20*mm, h - 28*mm, "PROPOSTA COMERCIAL · ADMINISTRAÇÃO DE CONDOMÍNIOS")

    # Título
    c.setFillColor(TEXTO)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(20*mm, h - 55*mm, f"PROPOSTA — {nome}")
    c.setFont("Helvetica", 10)
    c.drawString(20*mm, h - 62*mm, f"Data: {data_str}")

    # Dados do condomínio
    y = h - 75*mm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(20*mm, y, "DADOS DO CONDOMÍNIO")
    y -= 8*mm
    c.setFont("Helvetica", 10)
    linhas = [
        f"Perfil: {data.get('perfil', '—')}  ·  Unidades: {data.get('unidades', '—')}  ·  Tamanho: {data.get('tamanho', '—').upper()}",
        f"Saldo: {data.get('saldo', '—')}  ·  Conta: {data.get('conta', '—')}  ·  Funcionários: {data.get('func', '—')}",
        f"Garantidora: {data.get('garantidora', '—')}",
    ]
    for linha in linhas:
        c.drawString(20*mm, y, linha)
        y -= 6*mm

    # Valores
    y -= 6*mm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(20*mm, y, "VALORES")
    y -= 8*mm
    c.setFont("Helvetica", 10)
    adm = data.get("admAtual", 0)
    adm_un = data.get("admPorUnidade", 0)
    sug = data.get("totalSugestao", 0)
    sug_un = data.get("precoUnidadeSugestao", 0)
    prop = data.get("totalProposta", sug)
    prop_un = data.get("propostaPorUnidade", sug_un)

    valores = [
        f"ADM Atual: {format_money(adm)}  ({format_money(adm_un)}/un)",
        f"Sugestão Atlas: {format_money(sug)}  ({format_money(sug_un)}/un)",
        f"Proposta Atlas: {format_money(prop)}  ({format_money(prop_un)}/un)",
    ]
    for v in valores:
        c.drawString(20*mm, y, v)
        y -= 6*mm

    # Status
    y -= 4*mm
    status = data.get("status", "—")
    detalhe = data.get("statusDetalhe", "")
    c.setFont("Helvetica-Bold", 11)
    c.drawString(20*mm, y, f"STATUS: {status}")
    if detalhe:
        y -= 6*mm
        c.setFont("Helvetica", 9)
        c.drawString(20*mm, y, detalhe)

    motivo = data.get("motivo", "")
    if motivo:
        y -= 8*mm
        c.setFont("Helvetica-Bold", 10)
        c.drawString(20*mm, y, "MOTIVO:")
        y -= 6*mm
        c.setFont("Helvetica", 9)
        c.drawString(20*mm, y, motivo[:120])

    # Rodapé
    c.setFillColor(DOURADO)
    c.rect(0, 0, w, 15*mm, fill=1, stroke=0)
    c.setFillColor(OFFWHITE)
    c.setFont("Helvetica", 8)
    c.drawString(20*mm, 6*mm, "Documento gerado pela ferramenta de precificação Atlas Hall")

    c.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"{arquivo_data} - Proposta Atlas Hall - {nome}.pdf", mimetype="application/pdf")

@app.route("/health")
def health():
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
