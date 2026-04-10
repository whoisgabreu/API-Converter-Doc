# Flask
from flask import Flask, request, jsonify, Response

# DOCX > PDF
from modules.pdf_binario import convert_docx_base64_to_pdf

# HTML > PDF
from weasyprint import HTML

# Bibliotecas de suporte
from dotenv import load_dotenv
import os
import logging

# Configuração de logging global
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
load_dotenv()

API_KEY = os.getenv("API_KEY")

def require_api_key(func):
    def wrapper(*args, **kwargs):
        key = request.headers.get("X-API-KEY")
        if key != API_KEY:
            return jsonify({"error": "Unauthorized"}), 401
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper


### Conversor de Documentos

# DOCX > PDF
@app.route("/convert/docx", methods=["POST"])
@require_api_key
def convert_docx_endpoint():
    data = request.get_json()

    if not data or 'file_base64' not in data:
        return jsonify({"error": "Campo 'file_base64' não encontrado"}), 400

    try:
        pdf_bytes = convert_docx_base64_to_pdf(data['file_base64'])

        return Response(
            pdf_bytes,
            mimetype='application/pdf',
            headers={
                "Content-Disposition": "inline; filename=arquivo.pdf"
            }
        )
    except Exception as e:
        logger.error(f"Erro no endpoint /convert/docx: {e}")
        return jsonify({"error": str(e)}), 500

# HTML > PDF
@app.route("/convert/html", methods=["POST"])
@require_api_key
def convert_html_endpoint():
    data = request.get_json()
    if not data or 'html_content' not in data:
        return jsonify({"error": "Campo 'html_content' não encontrado"}), 400

    try:
        html_content = data['html_content']
        pdf_bytes = HTML(string=html_content).write_pdf()

        return Response(
            pdf_bytes,
            mimetype='application/pdf',
            headers={"Content-Disposition": "inline; filename=arquivo.pdf"}
        )
    except Exception as e:
        logger.error(f"Erro no endpoint /convert/html: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    logger.info("Iniciando API de Conversão de Documentos...")
    app.run(host="0.0.0.0", port=5000, debug=True)