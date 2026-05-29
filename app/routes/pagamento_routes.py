from flask import Blueprint, jsonify, request

from app.database.connection import get_connection
from app.services.pagamento_service import criar_pagamento
from app.services.servico_status_service import (
    buscar_pagamento_por_conversa,
    buscar_status_servico,
    finalizar_servico,
    verificar_usuario_na_conversa,
)
from app.utils.jwt_handler import decodificar_token

pagamento = Blueprint("pagamento", __name__)


def get_user_id_from_token():
    auth_header = request.headers.get("Authorization", "")

    if not auth_header.startswith("Bearer "):
        return None

    payload = decodificar_token(auth_header.replace("Bearer ", "", 1))

    if not payload:
        return None

    return payload.get("user_id")


def get_usuario_logado():
    user_id = get_user_id_from_token()

    if not user_id:
        return None

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id_usuario, nome, tipo_usuario
        FROM usuarios
        WHERE id_usuario = ?
        """,
        (user_id,),
    )
    usuario = cursor.fetchone()
    conn.close()
    return usuario


def tipo_consumidor(tipo_usuario):
    return tipo_usuario in ("contratante", "consumidor")


def montar_payload_pagamento(status):
    return {
        "conversa_id": status.get("conversa_id"),
        "contratante_id": status.get("contratante_id"),
        "prestador_id": status.get("prestador_id"),
        "status": status.get("status"),
        "finalizacao_liberada": status.get("finalizacao_liberada"),
        "valor_servico": status.get("valor_servico"),
        "nome_recebedor": status.get("nome_recebedor"),
        "tipo_chave_pix": status.get("tipo_chave_pix"),
        "chave_pix": status.get("chave_pix"),
        "descricao_pagamento": status.get("descricao_pagamento"),
    }


@pagamento.route("/pagar", methods=["POST"])
def pagar():
    user_id = get_user_id_from_token()

    if not user_id:
        return jsonify({"erro": "Usuário não autenticado"}), 401

    data = request.json or {}
    pagador_id = int(data.get("pagador_id") or 0)
    recebedor_id = int(data.get("recebedor_id") or 0)

    if int(user_id) != pagador_id:
        return jsonify({"erro": "Pagamento não autorizado para este usuário."}), 403

    status = buscar_status_servico(pagador_id, recebedor_id)

    if not status.get("finalizacao_liberada"):
        return jsonify({"erro": "A finalização ainda não foi liberada pelo prestador."}), 400

    criar_pagamento(
        data.get("servico_id"),
        pagador_id,
        recebedor_id,
        data["valor"],
        data["metodo"]
    )

    return {"msg": "Pagamento registrado"}


@pagamento.route("/pagamento/dados/<path:conversa_id>", methods=["GET"])
def dados_pagamento(conversa_id):
    usuario = get_usuario_logado()

    if not usuario:
        return jsonify({"erro": "Usuário não autenticado"}), 401

    status = buscar_pagamento_por_conversa(conversa_id)

    if not status:
        return jsonify({"erro": "Conversa não encontrada."}), 404

    if not verificar_usuario_na_conversa(conversa_id, usuario["id_usuario"]):
        return jsonify({"erro": "Você não tem acesso a este pagamento."}), 403

    if not status.get("finalizacao_liberada"):
        return jsonify({"erro": "Pagamento ainda não liberado pelo prestador."}), 400

    return jsonify(montar_payload_pagamento(status)), 200


@pagamento.route("/pagamento/confirmar", methods=["POST"])
def confirmar_pagamento():
    usuario = get_usuario_logado()

    if not usuario:
        return jsonify({"erro": "Usuário não autenticado"}), 401

    if not tipo_consumidor(usuario["tipo_usuario"]):
        return jsonify({"erro": "Apenas o contratante pode confirmar o pagamento."}), 403

    data = request.json or request.form or {}
    conversa_id = data.get("conversa_id")

    if not conversa_id:
        return jsonify({"erro": "Conversa não informada."}), 400

    status = buscar_pagamento_por_conversa(conversa_id)

    if not status:
        return jsonify({"erro": "Conversa não encontrada."}), 404

    if not verificar_usuario_na_conversa(conversa_id, usuario["id_usuario"]):
        return jsonify({"erro": "Você não tem acesso a este pagamento."}), 403

    if int(status["contratante_id"]) != int(usuario["id_usuario"]):
        return jsonify({"erro": "Apenas o contratante desta conversa pode confirmar o pagamento."}), 403

    if not status.get("finalizacao_liberada"):
        return jsonify({"erro": "Pagamento ainda não liberado pelo prestador."}), 400

    try:
        status_finalizado = finalizar_servico(status["contratante_id"], status["prestador_id"])
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400

    return jsonify({
        "mensagem": "Pagamento confirmado e serviço finalizado com sucesso.",
        "servico": montar_payload_pagamento(status_finalizado),
    }), 200
