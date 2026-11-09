from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from pptx import Presentation
from datetime import datetime
import io
import os
import tempfile
import subprocess

app = Flask(__name__)
CORS(app)

TEMPLATE = os.path.join(os.path.dirname(__file__), "template.pptx")

@app.route("/gerar", methods=["POST"])
def gerar():
    data = request.json or {}
    nome = data.get("nome", "CONDOMINIO").upper()
    hoje = datetime.now()
    data_str = hoje.strftime("%d/%m/%Y")
    arquivo_data = hoje.strftime("%Y.%m.%d")

    prs = Presentation(TEMPLATE)

    # Capa (slide 0) — procura e substitui placeholders
    for shape in prs.slides[0].shapes:
        if shape.has_text_frame:
            for p in shape.text_frame.paragraphs:
                for run in p.runs:
                    if "NOME DO CONDOMINIO" in run.text or "CONDOMÍNIO" in run.text.upper():
                        run.text = nome
                    if "ANO.MÊS.DIA" in run.text or "DATA" in run.text.upper():
                        run.text = data_str

    # Slide 8 (índice 7) — valores financeiros
    if len(prs.slides) > 7:
        slide8 = prs.slides[7]
        adm = data.get("admAtual", 0)
        adm_un = data.get("admPorUnidade", 0)
        proposta = data.get("totalProposta", data.get("totalSugestao", 0))
        prop_un = data.get("propostaPorUnidade", data.get("precoUnidadeSugestao", 0))

        valores = [adm, adm_un, proposta, prop_un]
        idx = 0
        for shape in slide8.shapes:
            if shape.has_text_frame and idx < 4:
                for p in shape.text_frame.paragraphs:
                    for run in p.runs:
                        if any(x in run.text for x in ["R$", "0,00", "VALOR", "TOTAL"]):
                            run.text = f"R$ {valores[idx]:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                            idx += 1
                            break
                    if idx >= 4:
                        break

    # Salva PPTX temporário e converte para PDF
    with tempfile.TemporaryDirectory() as tmp:
        pptx_path = os.path.join(tmp, "proposta.pptx")
        pdf_path = os.path.join(tmp, "proposta.pdf")
        prs.save(pptx_path)

        # Converte com LibreOffice
        subprocess.run(
            ["libreoffice", "--headless", "--convert-to", "pdf", "--outdir", tmp, pptx_path],
            check=True, capture_output=True
        )

        return send_file(pdf_path, as_attachment=True, download_name=f"{arquivo_data} - Proposta Atlas Hall - {nome}.pdf")

@app.route("/health")
def health():
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
