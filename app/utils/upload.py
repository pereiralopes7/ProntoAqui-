import os
import uuid
from werkzeug.utils import secure_filename

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
UPLOAD_FOLDER = "uploads"
UPLOAD_FOLDER_ABSOLUTE = os.path.join(PROJECT_ROOT, UPLOAD_FOLDER)
EXTENSOES_PERMITIDAS = {".jpg", ".jpeg", ".png"}


def extensao_permitida(filename):
    _, extensao = os.path.splitext(filename or "")
    return extensao.lower() in EXTENSOES_PERMITIDAS


def salvar_foto(file):
    os.makedirs(UPLOAD_FOLDER_ABSOLUTE, exist_ok=True)

    filename = secure_filename(file.filename or "foto")
    nome, extensao = os.path.splitext(filename)
    extensao = extensao.lower()

    if not extensao_permitida(filename):
        raise ValueError("Formato de foto inválido. Envie JPG, JPEG ou PNG.")

    nome_base = nome or "foto"
    filename_unico = f"{uuid.uuid4().hex}-{nome_base}{extensao}"

    caminho_absoluto = os.path.join(UPLOAD_FOLDER_ABSOLUTE, filename_unico)
    file.save(caminho_absoluto)

    return os.path.join(UPLOAD_FOLDER, filename_unico).replace(os.sep, "/")
