import json
from datetime import datetime
from pathlib import Path

from app.services.chat_json_service import gerar_id_conversa


PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATUS_FILE = PROJECT_ROOT / "servicos_status.json"
LEGACY_STATUS_FILE = PROJECT_ROOT / "chat_service_status.json"

STATUS_NEGOCIACAO = "negociacao"
STATUS_LIBERADO = "finalizacao_liberada"
STATUS_FINALIZADO = "finalizado"


def agora_iso():
    return datetime.now().isoformat(timespec="seconds")


def garantir_arquivo_status():
    if not STATUS_FILE.exists():
        status_inicial = []

        if LEGACY_STATUS_FILE.exists():
            status_inicial = _ler_status_seguro(LEGACY_STATUS_FILE)

        salvar_status(status_inicial)


def _ler_status_seguro(path):
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

    if not isinstance(dados, list):
        return []

    for item in dados:
        if item.get("status") == "aguardando_negociacao":
            item["status"] = STATUS_NEGOCIACAO

    return dados


def carregar_status():
    garantir_arquivo_status()

    return _ler_status_seguro(STATUS_FILE)


def salvar_status(status):
    STATUS_FILE.write_text(
        json.dumps(status, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def criar_status_padrao(contratante_id, prestador_id):
    contratante_id = int(contratante_id)
    prestador_id = int(prestador_id)

    return {
        "conversa_id": gerar_id_conversa(contratante_id, prestador_id),
        "contratante_id": contratante_id,
        "prestador_id": prestador_id,
        "status": STATUS_NEGOCIACAO,
        "finalizacao_liberada": False,
        "data_liberacao": None,
        "data_finalizacao": None,
    }


def buscar_status_servico(contratante_id, prestador_id):
    conversa_id = gerar_id_conversa(contratante_id, prestador_id)

    for item in carregar_status():
        if item.get("conversa_id") == conversa_id:
            return item

    return criar_status_padrao(contratante_id, prestador_id)


def liberar_finalizacao(contratante_id, prestador_id):
    novo_status = criar_status_padrao(contratante_id, prestador_id)
    status = carregar_status()

    for indice, item in enumerate(status):
        if item.get("conversa_id") == novo_status["conversa_id"]:
            novo_status = {**item}
            novo_status["status"] = STATUS_LIBERADO
            novo_status["finalizacao_liberada"] = True
            novo_status["data_liberacao"] = novo_status.get("data_liberacao") or agora_iso()
            status[indice] = novo_status
            salvar_status(status)
            return novo_status

    novo_status["status"] = STATUS_LIBERADO
    novo_status["finalizacao_liberada"] = True
    novo_status["data_liberacao"] = agora_iso()
    status.append(novo_status)
    salvar_status(status)
    return novo_status


def finalizar_servico(contratante_id, prestador_id):
    status = carregar_status()
    conversa_id = gerar_id_conversa(contratante_id, prestador_id)

    for indice, item in enumerate(status):
        if item.get("conversa_id") != conversa_id:
            continue

        if not item.get("finalizacao_liberada"):
            raise ValueError("A finalização ainda não foi liberada pelo prestador.")

        item = {**item}
        item["status"] = STATUS_FINALIZADO
        item["finalizacao_liberada"] = True
        item["data_finalizacao"] = agora_iso()
        status[indice] = item
        salvar_status(status)
        return item

    raise ValueError("A finalização ainda não foi liberada pelo prestador.")
