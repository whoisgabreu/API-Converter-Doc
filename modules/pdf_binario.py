# modules/pdf_binario.py
import os
import uuid
import base64
import subprocess
import platform
import logging
import tempfile
import zipfile
from io import BytesIO
from pathlib import Path

logger = logging.getLogger(__name__)

# Apenas importa docx2pdf se for Windows
if platform.system() == "Windows":
    try:
        from docx2pdf import convert as convert_docx2pdf
    except ImportError:
        logger.warning("Biblioteca 'docx2pdf' não encontrada. Conversão DOCX no Windows não funcionará.")


def convert_docx_base64_to_pdf(file_base64: str) -> bytes:
    """
    Converte um arquivo DOCX (em base64) para PDF (em binário).
    Também aceita PDF em base64 e retorna diretamente.
    """

    # 🔧 Remove prefixo base64 (caso venha do frontend)
    if "base64," in file_base64:
        file_base64 = file_base64.split("base64,")[1]

    # 🔓 Decode base64
    try:
        file_data = base64.b64decode(file_base64)
    except Exception as e:
        logger.error(f"Erro ao decodificar base64: {e}")
        raise ValueError(f"Base64 inválido: {e}")

    logger.info(f"Primeiros bytes do arquivo: {file_data[:10]}")

    # 🧠 Detecta PDF
    if file_data.startswith(b'%PDF'):
        logger.info("Arquivo já é PDF. Retornando sem conversão.")
        return file_data

    # 🧠 Detecta DOCX (ZIP válido + estrutura)
    if file_data.startswith(b'PK'):
        try:
            with zipfile.ZipFile(BytesIO(file_data)) as z:
                if 'word/document.xml' not in z.namelist():
                    raise ValueError("Arquivo ZIP não é um DOCX válido.")
        except zipfile.BadZipFile:
            raise ValueError("Arquivo não é um DOCX válido (ZIP corrompido).")

        logger.info("Arquivo DOCX válido detectado. Iniciando conversão...")

    else:
        logger.error("Formato de arquivo não suportado.")
        raise ValueError("Formato de arquivo não suportado. Envie DOCX ou PDF.")

    # 📁 Conversão DOCX → PDF
    with tempfile.TemporaryDirectory() as temp_dir:
        file_id = str(uuid.uuid4())
        input_path = Path(temp_dir) / f"{file_id}.docx"
        output_path = Path(temp_dir) / f"{file_id}.pdf"

        input_path.write_bytes(file_data)

        try:
            system_type = platform.system()

            if system_type == "Windows":
                convert_docx2pdf(str(input_path), str(output_path))

            else:
                subprocess.run([
                    "libreoffice",
                    "--headless",
                    "--convert-to", "pdf",
                    str(input_path),
                    "--outdir", temp_dir
                ], check=True, timeout=60, capture_output=True)

            if not output_path.exists():
                logger.error("PDF não foi gerado.")
                raise RuntimeError("Falha na geração do PDF.")

            pdf_binary = output_path.read_bytes()
            logger.info("Conversão concluída com sucesso.")

            return pdf_binary

        except subprocess.TimeoutExpired:
            logger.error("Timeout na conversão.")
            raise RuntimeError("A conversão demorou demais.")

        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode() if e.stderr else str(e)
            logger.error(f"Erro no LibreOffice: {stderr}")
            raise RuntimeError("Erro no LibreOffice durante conversão.")

        except Exception as e:
            logger.error(f"Erro inesperado: {e}")
            raise RuntimeError(f"Erro inesperado: {str(e)}")
