# modules/pdf_binario.py
import os
import uuid
import base64
import subprocess
import platform
import logging
import tempfile
from pathlib import Path

# Configuração de logger para o módulo
logger = logging.getLogger(__name__)

# Apenas importa docx2pdf se for Windows
if platform.system() == "Windows":
    try:
        from docx2pdf import convert as convert_docx2pdf
    except ImportError:
        logger.warning("Biblioteca 'docx2pdf' não encontrada. Conversão DOCX no Windows não funcionará.")

def convert_docx_base64_to_pdf(file_base64: str) -> bytes:
    """
    Converte um arquivo DOCX (em base64) para PDF (em binário) de forma segura.
    """
    try:
        file_data = base64.b64decode(file_base64)
    except Exception as e:
        logger.error(f"Erro ao decodificar base64: {e}")
        raise ValueError(f"Base64 inválido: {e}")

    # Validação rápida de cabeçalho DOCX (arquivos ZIP começam com PK)
    if not file_data.startswith(b'PK'):
        logger.warning("Tentativa de conversão de arquivo que não parece ser um DOCX válido.")
        raise ValueError("O conteúdo fornecido não parece ser um documento DOCX válido.")

    # Usando diretório temporário para isolamento e limpeza automática
    with tempfile.TemporaryDirectory() as temp_dir:
        file_id = str(uuid.uuid4())
        input_path = Path(temp_dir) / f"{file_id}.docx"
        output_path = Path(temp_dir) / f"{file_id}.pdf"

        # Salva o arquivo .docx temporariamente
        input_path.write_bytes(file_data)
        logger.info(f"Iniciando conversão do documento {file_id}")

        try:
            system_type = platform.system()

            if system_type == "Windows":
                # Nota: docx2pdf requer Microsoft Word instalado no Windows
                convert_docx2pdf(str(input_path), str(output_path))
            else:
                # Usa libreoffice no Linux/macOS
                subprocess.run([
                    "libreoffice",
                    "--headless",
                    "--convert-to", "pdf",
                    str(input_path),
                    "--outdir", temp_dir
                ], check=True, timeout=60, capture_output=True)

            # Verifica se o arquivo de saída foi gerado
            if not output_path.exists():
                logger.error(f"Arquivo PDF não foi gerado para {file_id}")
                raise RuntimeError("Falha na geração do arquivo PDF pelo motor de conversão.")

            # Lê o PDF e retorna como binário
            pdf_binary = output_path.read_bytes()
            logger.info(f"Conversão concluída com sucesso: {file_id}")
            
            return pdf_binary

        except subprocess.TimeoutExpired:
            logger.error(f"Tempo limite de conversão excedido para {file_id}")
            raise RuntimeError("A conversão demorou demais e foi interrompida.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Erro no LibreOffice ({e.returncode}): {e.stderr.decode() if e.stderr else str(e)}")
            raise RuntimeError("Erro interno no motor de conversão (LibreOffice).")
        except Exception as e:
            logger.error(f"Erro inesperado durante a conversão: {e}")
            raise RuntimeError(f"Ocorreu um erro inesperado: {str(e)}")
