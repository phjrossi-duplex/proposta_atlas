from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from pptx import Presentation
from datetime import datetime
import io
import os
import tempfile
import subprocess
import traceback

app = Flask(__name__)
CORS(app)

TEMPLATE = os.path.join(os.path.dirname(__file__), "template.pptx")

@app.route("/gerar", methods=["POST"])
def gerar():
    try:
        data = request.json or {}
        nome = data.get("nome", "CONDOMINIO").upper()
        hoje = datetime.now()
        data_str = hoje.strftime("%d/%m/%Y")
        arquivo_data = hoje.strftime("%Y.%m.%d")

        if not os.path.exists(TEMPLATE):
            return jsonify({"error": "template.pptx não encontrado"}), 500

        prs = Presentation(TEMPLATE)

        # Capa (slide 0)
        for shape in prs.slides[0].shapes:
            if shape.has_text_frame:
                for p in shape.text_frame.paragraphs:
                    for run in p.runs:
                        if "NOME DO CONDOMINIO" in run.text or "CONDOMÍNIO" in run.text.upper():
                            run.text = nome
                        if "ANO.MÊS.DIA" in run.text or "DATA" in run.text.upper():
                            run.text = data_str

        # Slide 8 (índice 7)
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

        # Salva PPTX e tenta converter
        with tempfile.TemporaryDirectory() as tmp:
            pptx_path = os.path.join(tmp, "proposta.pptx")
            pdf_path = os.path.join(tmp, "proposta.pdf")
            prs.save(pptx_path)

            # Tenta LibreOffice; se falhar, devolve o PPTX
            try:
                result = subprocess.run(
                    ["libreoffice", "--headless", "--convert-to", "pdf", "--outdir", tmp, pptx_path],
                    capture_output=True, timeout=60
                )
                if result.returncode == 0 and os.path.exists(pdf_path):
                    return send_file(pdf_path, as_attachment=True, download_name=f"{arquivo_data} - Proposta Atlas Hall - {nome}.pdf")
            except Exception:
                pass

            # Fallback: devolve o PPTX editado
            return send_file(pptx_path, as_attachment=True, download_name=f"{arquivo_data} - Proposta Atlas Hall - {nome}.pptx")

    except Exception as e:
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500

@app.route("/health")
def health():
    return jsonify({"ok": True, "template": os.path.exists(TEMPLATE)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
