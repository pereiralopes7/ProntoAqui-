from flask import Blueprint, jsonify, request

from app.services.pagamento_service import criar_pagamento
from app.services.servico_status_service import buscar_status_servico
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
