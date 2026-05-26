import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHAT_FILE = PROJECT_ROOT / "chat_messages.json"
LEGACY_CHAT_FILE = Path(__file__).resolve().parent.parent / "chat_messages.json"
DAYS_TO_KEEP = 7


def agora_iso():
    return datetime.now().isoformat(timespec="seconds")


def gerar_id_conversa(user1, user2):
    ids = sorted([int(user1), int(user2)])
    return f"chat_{ids[0]}_{ids[1]}"


def garantir_arquivo_chat():
    if not CHAT_FILE.exists():
        mensagens_iniciais = []

        if LEGACY_CHAT_FILE.exists():
            mensagens_iniciais = _ler_json_seguro(LEGACY_CHAT_FILE)

        salvar_mensagens(mensagens_iniciais)


def _ler_json_seguro(path):
    try:
        conteudo = path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return []

    if not conteudo:
        return []

    try:
        dados = json.loads(conteudo)
    except json.JSONDecodeError:
        return []

    return dados if isinstance(dados, list) else []


def normalizar_mensagem(mensagem):
    try:
        remetente_id = int(mensagem.get("remetente_id"))
        destinatario_id = int(mensagem.get("destinatario_id"))
    except (TypeError, ValueError):
        return None

    texto = (mensagem.get("texto") or mensagem.get("mensagem") or "").strip()

    if not texto:
        return None

    conversa_id = mensagem.get("conversa_id") or mensagem.get("id_conversa")

    if not conversa_id:
        conversa_id = gerar_id_conversa(remetente_id, destinatario_id)

    return {
        "id": str(mensagem.get("id") or uuid.uuid4()),
        "conversa_id": str(conversa_id),
        "remetente_id": remetente_id,
        "destinatario_id": destinatario_id,
        "texto": texto,
        "data_envio": mensagem.get("data_envio") or mensagem.get("data") or agora_iso(),
        "lida": bool(mensagem.get("lida", False)),
    }


def carregar_mensagens():
    garantir_arquivo_chat()

    mensagens = []

    for mensagem in _ler_json_seguro(CHAT_FILE):
        mensagem_normalizada = normalizar_mensagem(mensagem)

        if mensagem_normalizada:
            mensagens.append(mensagem_normalizada)

    return mensagens


def salvar_mensagens(mensagens):
    CHAT_FILE.write_text(
        json.dumps(mensagens, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def mensagem_recente(mensagem):
    try:
        data_envio = datetime.fromisoformat(str(mensagem["data_envio"]))
    except (KeyError, ValueError, TypeError):
        return False

    return data_envio >= datetime.now() - timedelta(days=DAYS_TO_KEEP)


def limpar_mensagens_antigas():
    mensagens = [msg for msg in carregar_mensagens() if mensagem_recente(msg)]
    salvar_mensagens(mensagens)
    return mensagens


def salvar_mensagem(remetente_id, destinatario_id, texto):
    remetente_id = int(remetente_id)
    destinatario_id = int(destinatario_id)
    texto = (texto or "").strip()

    if remetente_id == destinatario_id:
        raise ValueError("Você não pode enviar mensagem para si mesmo.")

    if not texto:
        raise ValueError("Digite uma mensagem antes de enviar.")

    mensagens = limpar_mensagens_antigas()

    mensagem = {
        "id": str(uuid.uuid4()),
        "conversa_id": gerar_id_conversa(remetente_id, destinatario_id),
        "remetente_id": remetente_id,
        "destinatario_id": destinatario_id,
        "texto": texto,
        "data_envio": agora_iso(),
        "lida": False,
    }

    mensagens.append(mensagem)
    salvar_mensagens(mensagens)

    return mensagem


def buscar_historico(remetente_id, destinatario_id):
    remetente_id = int(remetente_id)
    destinatario_id = int(destinatario_id)

    if remetente_id == destinatario_id:
        raise ValueError("Você não pode buscar uma conversa consigo mesmo.")

    conversa_id = gerar_id_conversa(remetente_id, destinatario_id)
    mensagens = limpar_mensagens_antigas()

    return [
        mensagem
        for mensagem in mensagens
        if mensagem["conversa_id"] == conversa_id
    ]


def listar_conversas_do_usuario(usuario_id):
    usuario_id = int(usuario_id)
    conversas = {}

    for mensagem in limpar_mensagens_antigas():
        remetente_id = int(mensagem["remetente_id"])
        destinatario_id = int(mensagem["destinatario_id"])

        if usuario_id not in (remetente_id, destinatario_id):
            continue

        outro_usuario_id = destinatario_id if remetente_id == usuario_id else remetente_id
        conversa_id = mensagem.get("conversa_id") or gerar_id_conversa(usuario_id, outro_usuario_id)
        conversa_atual = conversas.get(conversa_id)

        if conversa_atual and mensagem["data_envio"] <= conversa_atual["data_ultima_mensagem"]:
            continue

        conversas[conversa_id] = {
            "conversa_id": conversa_id,
            "outro_usuario_id": outro_usuario_id,
            "ultima_mensagem": mensagem["texto"],
            "data_ultima_mensagem": mensagem["data_envio"],
            "remetente_id": remetente_id,
            "destinatario_id": destinatario_id,
        }

    return sorted(
        conversas.values(),
        key=lambda item: item["data_ultima_mensagem"],
        reverse=True,
    )
