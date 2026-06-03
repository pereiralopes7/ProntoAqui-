import re
import unicodedata
from decimal import Decimal, InvalidOperation


def formatar_valor_pix(valor):
    valor = str(valor or "").strip().replace("R$", "").replace(" ", "")

    if "," in valor:
        valor = valor.replace(".", "").replace(",", ".")

    try:
        valor_decimal = Decimal(valor)
    except (InvalidOperation, ValueError):
        raise ValueError("Valor do serviço não informado.")

    if valor_decimal <= 0:
        raise ValueError("O valor do serviço deve ser maior que zero.")

    return f"{valor_decimal.quantize(Decimal('0.01'))}"


def remover_acentos(valor):
    texto = str(valor or "")
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(char for char in texto if unicodedata.category(char) != "Mn")
    return texto


def limitar_texto(valor, tamanho):
    texto = remover_acentos(valor).strip()
    return texto[:tamanho]


def montar_campo(id, valor):
    valor = str(valor or "")
    tamanho = len(valor.encode("utf-8"))
    return f"{id}{tamanho:02d}{valor}"


def crc16(payload):
    polinomio = 0x1021
    resultado = 0xFFFF

    for byte in payload.encode("utf-8"):
        resultado ^= byte << 8

        for _ in range(8):
            if resultado & 0x8000:
                resultado = (resultado << 1) ^ polinomio
            else:
                resultado <<= 1

            resultado &= 0xFFFF

    return f"{resultado:04X}"


def normalizar_txid(txid):
    txid = remover_acentos(txid or "")
    txid = re.sub(r"[^A-Za-z0-9]", "", txid).upper()
    return (txid or "PRONTOAQUI")[:25]


def validar_crc_pix(payload):
    payload = str(payload or "").strip()

    if len(payload) < 8 or not payload.startswith("000201"):
        return False

    payload_sem_crc = payload[:-4]
    crc_informado = payload[-4:].upper()

    if not payload_sem_crc.endswith("6304"):
        return False

    return crc16(payload_sem_crc) == crc_informado


def gerar_pix_copia_cola(
    chave_pix,
    nome_recebedor,
    cidade_recebedor,
    valor,
    txid,
    descricao=None,
):
    chave_pix = str(chave_pix or "").strip()
    nome_recebedor = limitar_texto(nome_recebedor, 25).upper()
    cidade_recebedor = limitar_texto(cidade_recebedor or "INDAIATUBA", 15).upper()
    descricao = limitar_texto(descricao or "Servico ProntoAqui", 72)
    txid = normalizar_txid(txid)
    valor_formatado = formatar_valor_pix(valor)

    if not chave_pix:
        raise ValueError("Chave Pix não informada pelo prestador.")

    if not nome_recebedor:
        raise ValueError("Informe o nome do recebedor.")

    if not cidade_recebedor:
        raise ValueError("Informe a cidade do recebedor.")

    merchant_account = (
        montar_campo("00", "br.gov.bcb.pix") +
        montar_campo("01", chave_pix)
    )

    if descricao:
        merchant_account += montar_campo("02", descricao)

    payload_sem_crc = (
        montar_campo("00", "01") +
        montar_campo("26", merchant_account) +
        montar_campo("52", "0000") +
        montar_campo("53", "986") +
        montar_campo("54", valor_formatado) +
        montar_campo("58", "BR") +
        montar_campo("59", nome_recebedor) +
        montar_campo("60", cidade_recebedor) +
        montar_campo("62", montar_campo("05", txid)) +
        "6304"
    )

    return payload_sem_crc + crc16(payload_sem_crc)
