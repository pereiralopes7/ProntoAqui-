import json
from datetime import datetime
from decimal import Decimal, InvalidOperation
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
        "valor_servico": None,
        "nome_recebedor": None,
        "tipo_chave_pix": None,
        "chave_pix": None,
        "descricao_pagamento": None,
        "data_liberacao": None,
        "data_finalizacao": None,
    }


def normalizar_status(item):
    status = criar_status_padrao(item.get("contratante_id"), item.get("prestador_id"))
    status.update(item)

    if status.get("status") == "aguardando_negociacao":
        status["status"] = STATUS_NEGOCIACAO

    return status


def buscar_status_servico(contratante_id, prestador_id):
    conversa_id = gerar_id_conversa(contratante_id, prestador_id)

    for item in carregar_status():
        if item.get("conversa_id") == conversa_id:
            return normalizar_status(item)

    return criar_status_padrao(contratante_id, prestador_id)


def normalizar_valor_servico(valor):
    valor = str(valor or "").strip().replace("R$", "").replace(" ", "")

    if "," in valor:
        valor = valor.replace(".", "").replace(",", ".")

    try:
        valor_decimal = Decimal(valor)
    except (InvalidOperation, ValueError):
        raise ValueError("Informe um valor de serviço válido.")

    if valor_decimal <= 0:
        raise ValueError("O valor do serviço deve ser maior que zero.")

    return f"{valor_decimal.quantize(Decimal('0.01'))}"


def validar_dados_pagamento(valor_servico, nome_recebedor, tipo_chave_pix, chave_pix):
    valor_normalizado = normalizar_valor_servico(valor_servico)
    nome_recebedor = str(nome_recebedor or "").strip()
    tipo_chave_pix = str(tipo_chave_pix or "").strip()
    chave_pix = str(chave_pix or "").strip()

    tipos_validos = {"CPF", "E-mail", "Telefone", "Chave aleatória"}

    if not nome_recebedor:
        raise ValueError("Informe o nome do recebedor.")

    if tipo_chave_pix not in tipos_validos:
        raise ValueError("Informe um tipo de chave Pix válido.")

    if not chave_pix:
        raise ValueError("Informe a chave Pix.")

    return valor_normalizado, nome_recebedor, tipo_chave_pix, chave_pix


def liberar_finalizacao(
    contratante_id,
    prestador_id,
    valor_servico,
    nome_recebedor,
    tipo_chave_pix,
    chave_pix,
    descricao_pagamento=None,
):
    # Fluxo de pagamento simulado para apresentação. Integração Pix real será implementada futuramente.
    valor_servico, nome_recebedor, tipo_chave_pix, chave_pix = validar_dados_pagamento(
        valor_servico,
        nome_recebedor,
        tipo_chave_pix,
        chave_pix,
    )
    novo_status = criar_status_padrao(contratante_id, prestador_id)
    status = carregar_status()

    for indice, item in enumerate(status):
        if item.get("conversa_id") == novo_status["conversa_id"]:
            novo_status = normalizar_status(item)
            novo_status["status"] = STATUS_LIBERADO
            novo_status["finalizacao_liberada"] = True
            novo_status["valor_servico"] = valor_servico
            novo_status["nome_recebedor"] = nome_recebedor
            novo_status["tipo_chave_pix"] = tipo_chave_pix
            novo_status["chave_pix"] = chave_pix
            novo_status["descricao_pagamento"] = str(descricao_pagamento or "").strip() or None
            novo_status["data_liberacao"] = novo_status.get("data_liberacao") or agora_iso()
            status[indice] = novo_status
            salvar_status(status)
            return novo_status

    novo_status["status"] = STATUS_LIBERADO
    novo_status["finalizacao_liberada"] = True
    novo_status["valor_servico"] = valor_servico
    novo_status["nome_recebedor"] = nome_recebedor
    novo_status["tipo_chave_pix"] = tipo_chave_pix
    novo_status["chave_pix"] = chave_pix
    novo_status["descricao_pagamento"] = str(descricao_pagamento or "").strip() or None
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

        item = normalizar_status(item)

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


def buscar_pagamento_por_conversa(conversa_id):
    for item in carregar_status():
        item = normalizar_status(item)

        if item.get("conversa_id") == conversa_id:
            return item

    return None


def verificar_usuario_na_conversa(conversa_id, usuario_id):
    status = buscar_pagamento_por_conversa(conversa_id)

    if not status:
        return False

    return int(usuario_id) in (
        int(status.get("contratante_id")),
        int(status.get("prestador_id")),
    )
