from flask import Blueprint, current_app, jsonify, request
from app.utils.upload import salvar_foto
from app.services.chat_json_service import (
    buscar_historico,
    carregar_mensagens,
    listar_conversas_do_usuario,
    salvar_mensagem,
)
from app.services.servico_status_service import (
    buscar_status_servico,
    finalizar_servico,
    liberar_finalizacao,
)
from app.utils.jwt_handler import decodificar_token

chat = Blueprint("chat", __name__)


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

    from app.database.connection import get_connection

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id_usuario, nome, tipo_usuario, foto_perfil, foto_posicao_y
        FROM usuarios
        WHERE id_usuario = ?
        """,
        (user_id,),
    )
    usuario = cursor.fetchone()
    conn.close()

    return usuario


def buscar_usuario_por_id(user_id):
    from app.database.connection import get_connection

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id_usuario, nome, tipo_usuario, foto_perfil, foto_posicao_y
        FROM usuarios
        WHERE id_usuario = ?
        """,
        (user_id,),
    )
    usuario = cursor.fetchone()
    conn.close()
    return usuario


def normalizar_foto_chat(foto_perfil):
    if not foto_perfil:
        return "/img/default-user.svg"

    foto_perfil = str(foto_perfil).strip().replace("\\", "/")

    if foto_perfil.startswith("http") or foto_perfil.startswith("/"):
        return foto_perfil

    if foto_perfil.startswith("uploads/"):
        return "/" + foto_perfil

    return "/uploads/" + foto_perfil


def buscar_profissao_usuario(user_id):
    from app.database.connection import get_connection

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT profissao
        FROM perfis_trabalhador
        WHERE usuario_id = ?
        """,
        (user_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return row["profissao"] if row else ""


def tipo_consumidor(tipo_usuario):
    return tipo_usuario in ("contratante", "consumidor")


def tipo_prestador(tipo_usuario):
    return tipo_usuario in ("contratado", "prestador")


def preparar_status_response(status, usuario, prestador_id):
    tipo_usuario = usuario["tipo_usuario"]
    user_id = int(usuario["id_usuario"])
    pode_liberar = (
        tipo_prestador(tipo_usuario)
        and user_id == int(prestador_id)
        and not status.get("finalizacao_liberada")
        and status.get("status") != "finalizado"
    )
    pode_finalizar = (
        tipo_consumidor(tipo_usuario)
        and user_id == int(status.get("contratante_id"))
        and bool(status.get("finalizacao_liberada"))
        and status.get("status") != "finalizado"
    )

    return {
        **status,
        "pode_liberar": pode_liberar,
        "pode_finalizar": pode_finalizar,
        "usuario_logado_tipo": tipo_usuario,
    }


def verificar_conversa_existente(usuario_1, usuario_2):
    try:
        return bool(buscar_historico(usuario_1, usuario_2))
    except ValueError:
        return False


def emitir_mensagem_socket(mensagem):
    socketio = current_app.extensions.get("socketio")

    if not socketio:
        return

    payload = {
        **mensagem,
        "id_conversa": mensagem["conversa_id"],
        "data": mensagem["data_envio"],
    }

    socketio.emit("receive_message", payload, room=mensagem["conversa_id"])
    socketio.emit("receber_mensagem", payload, room=mensagem["conversa_id"])
    socketio.emit("nova_mensagem", payload, room=mensagem["conversa_id"])


@chat.route("/upload-chat", methods=["POST"])
def upload_chat():
    file = request.files["file"]
    caminho = salvar_foto(file)
    return {"imagem": caminho}


@chat.route("/historico", methods=["GET"])
def historico():
    user1 = request.args.get("user1")
    user2 = request.args.get("user2")

    if not user1 or not user2:
        return jsonify({"erro": "Informe user1 e user2"}), 400

    try:
        if int(user1) == int(user2):
            return jsonify({"mensagens": []})

        return jsonify({"mensagens": buscar_historico(user1, user2)})
    except ValueError:
        return jsonify({"erro": "IDs de usuário inválidos"}), 400
    except Exception as e:
        print("Erro ao buscar histórico:", e)
        return jsonify({"erro": str(e)}), 500


@chat.route("/chat/historico/<int:destinatario_id>", methods=["GET"])
def historico_chat(destinatario_id):
    user_id = get_user_id_from_token()

    if not user_id:
        return jsonify({"erro": "Usuário não autenticado"}), 401

    if int(user_id) == int(destinatario_id):
        return jsonify({"erro": "Você não pode buscar uma conversa consigo mesmo."}), 400

    try:
        return jsonify({
            "mensagens": buscar_historico(user_id, destinatario_id)
        }), 200
    except Exception as e:
        print("Erro ao buscar histórico do chat:", e)
        return jsonify({"erro": str(e)}), 500


@chat.route("/chat/enviar", methods=["POST"])
def enviar_chat():
    user_id = get_user_id_from_token()

    if not user_id:
        return jsonify({"erro": "Usuário não autenticado"}), 401

    data = request.json or request.form or {}
    destinatario_id = data.get("destinatario_id")
    texto = data.get("texto")

    if not destinatario_id:
        return jsonify({"erro": "Destinatário não informado"}), 400

    try:
        mensagem = salvar_mensagem(user_id, destinatario_id, texto)
        emitir_mensagem_socket(mensagem)

        return jsonify({
            "mensagem": "Mensagem enviada com sucesso",
            "chat": mensagem
        }), 201
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        print("Erro ao enviar mensagem:", e)
        return jsonify({"erro": str(e)}), 500


@chat.route("/chat/solicitacoes-recebidas", methods=["GET"])
def solicitacoes_recebidas():
    usuario = get_usuario_logado()

    if not usuario:
        return jsonify({"erro": "Usuário não autenticado"}), 401

    if not tipo_prestador(usuario["tipo_usuario"]):
        return jsonify({"erro": "Apenas prestadores podem acessar solicitações recebidas."}), 403

    prestador_id = int(usuario["id_usuario"])
    conversas = {}

    for mensagem in carregar_mensagens():
        remetente_id = int(mensagem["remetente_id"])
        destinatario_id = int(mensagem["destinatario_id"])

        if prestador_id not in (remetente_id, destinatario_id):
            continue

        outro_id = destinatario_id if remetente_id == prestador_id else remetente_id
        outro_usuario = buscar_usuario_por_id(outro_id)

        if not outro_usuario or not tipo_consumidor(outro_usuario["tipo_usuario"]):
            continue

        conversa_atual = conversas.get(outro_id)

        if not conversa_atual or mensagem["data_envio"] > conversa_atual["data_ultima_mensagem"]:
            status = buscar_status_servico(outro_id, prestador_id)
            conversas[outro_id] = {
                "consumidor_id": outro_id,
                "consumidor_nome": outro_usuario["nome"],
                "ultima_mensagem": mensagem["texto"],
                "data_ultima_mensagem": mensagem["data_envio"],
                "status_servico": status["status"],
                "finalizacao_liberada": status["finalizacao_liberada"],
            }

    solicitacoes = sorted(
        conversas.values(),
        key=lambda item: item["data_ultima_mensagem"],
        reverse=True,
    )

    return jsonify({"solicitacoes": solicitacoes}), 200


@chat.route("/chat/minhas-solicitacoes", methods=["GET"])
def minhas_solicitacoes():
    usuario = get_usuario_logado()

    if not usuario:
        return jsonify({"erro": "Usuário não autenticado"}), 401

    usuario_id = int(usuario["id_usuario"])
    usuario_tipo = usuario["tipo_usuario"]

    solicitacoes = []

    for conversa in listar_conversas_do_usuario(usuario_id):
        outro_id = int(conversa["outro_usuario_id"])
        outro_usuario = buscar_usuario_por_id(outro_id)

        if not outro_usuario:
            continue

        if tipo_consumidor(usuario_tipo) and not tipo_prestador(outro_usuario["tipo_usuario"]):
            continue

        if tipo_prestador(usuario_tipo) and not tipo_consumidor(outro_usuario["tipo_usuario"]):
            continue

        if tipo_consumidor(usuario_tipo):
            contratante_id = usuario_id
            prestador_id = outro_id
            outro_usuario_tipo = "prestador"
        else:
            contratante_id = outro_id
            prestador_id = usuario_id
            outro_usuario_tipo = "consumidor"

        status = buscar_status_servico(contratante_id, prestador_id)
        solicitacoes.append({
            "conversa_id": conversa["conversa_id"],
            "outro_usuario_id": outro_id,
            "outro_usuario_nome": outro_usuario["nome"],
            "outro_usuario_tipo": outro_usuario_tipo,
            "profissao": buscar_profissao_usuario(outro_id) if outro_usuario_tipo == "prestador" else "",
            "foto_perfil": normalizar_foto_chat(outro_usuario["foto_perfil"]),
            "foto_posicao_y": outro_usuario["foto_posicao_y"] if outro_usuario["foto_posicao_y"] is not None else 50,
            "ultima_mensagem": conversa["ultima_mensagem"],
            "data_ultima_mensagem": conversa["data_ultima_mensagem"],
            "status_servico": status["status"],
            "finalizacao_liberada": status["finalizacao_liberada"],
        })

    return jsonify({
        "tipo_usuario": usuario_tipo,
        "solicitacoes": solicitacoes,
    }), 200


@chat.route("/chat/status-servico/<int:outro_usuario_id>", methods=["GET"])
def status_servico(outro_usuario_id):
    usuario = get_usuario_logado()

    if not usuario:
        return jsonify({"erro": "Usuário não autenticado"}), 401

    user_id = int(usuario["id_usuario"])
    contratante_id = request.args.get("contratante_id", type=int)
    outro_usuario = buscar_usuario_por_id(outro_usuario_id)

    if not outro_usuario:
        return jsonify({"erro": "Usuário não encontrado."}), 404

    if user_id == int(outro_usuario_id) and not contratante_id:
        return jsonify({
            "erro": "Informe o contratante para consultar uma conversa do prestador."
        }), 400

    if user_id == int(outro_usuario_id):
        usuario_tipo = usuario["tipo_usuario"]

        if not tipo_prestador(usuario_tipo):
            return jsonify({"erro": "Apenas prestadores podem consultar essa conversa."}), 403

        prestador_id = user_id
        status = buscar_status_servico(contratante_id, prestador_id)
    elif tipo_consumidor(usuario["tipo_usuario"]) and tipo_prestador(outro_usuario["tipo_usuario"]):
        prestador_id = int(outro_usuario_id)
        status = buscar_status_servico(user_id, prestador_id)
    elif tipo_prestador(usuario["tipo_usuario"]) and tipo_consumidor(outro_usuario["tipo_usuario"]):
        prestador_id = user_id
        status = buscar_status_servico(outro_usuario_id, prestador_id)
    else:
        return jsonify({"erro": "Esta conversa não faz parte do fluxo de contratação."}), 400

    return jsonify(preparar_status_response(status, usuario, prestador_id)), 200


@chat.route("/chat/liberar-finalizacao", methods=["POST"])
def liberar_finalizacao_servico():
    usuario = get_usuario_logado()

    if not usuario:
        return jsonify({"erro": "Usuário não autenticado"}), 401

    if not tipo_prestador(usuario["tipo_usuario"]):
        return jsonify({"erro": "Apenas o prestador pode liberar a finalização."}), 403

    data = request.json or request.form or {}
    contratante_id = data.get("contratante_id") or data.get("consumidor_id")

    if not contratante_id:
        return jsonify({"erro": "Contratante não informado."}), 400

    prestador_id = int(usuario["id_usuario"])

    if int(contratante_id) == prestador_id:
        return jsonify({"erro": "Você não pode liberar finalização para si mesmo."}), 400

    try:
        if not verificar_conversa_existente(contratante_id, prestador_id):
            return jsonify({"erro": "Não existe conversa entre este contratante e prestador."}), 403

        status = liberar_finalizacao(
            contratante_id,
            prestador_id,
            data.get("valor_servico"),
            data.get("nome_recebedor"),
            data.get("tipo_chave_pix"),
            data.get("chave_pix"),
            data.get("cidade_recebedor"),
            data.get("descricao_pagamento"),
        )
        return jsonify({
            "mensagem": "Finalização liberada para o consumidor.",
            "servico": preparar_status_response(status, usuario, prestador_id),
        }), 200
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        print("Erro ao liberar finalização:", e)
        return jsonify({"erro": str(e)}), 500


@chat.route("/chat/finalizar-servico", methods=["POST"])
def finalizar_servico_chat():
    usuario = get_usuario_logado()

    if not usuario:
        return jsonify({"erro": "Usuário não autenticado"}), 401

    if not tipo_consumidor(usuario["tipo_usuario"]):
        return jsonify({"erro": "Apenas o contratante pode finalizar o serviço."}), 403

    data = request.json or request.form or {}
    prestador_id = data.get("prestador_id")

    if not prestador_id:
        return jsonify({"erro": "Prestador não informado."}), 400

    contratante_id = int(usuario["id_usuario"])

    if int(prestador_id) == contratante_id:
        return jsonify({"erro": "Você não pode finalizar um serviço consigo mesmo."}), 400

    try:
        status = finalizar_servico(contratante_id, prestador_id)
        return jsonify({
            "mensagem": "Serviço finalizado com sucesso.",
            "servico": preparar_status_response(status, usuario, prestador_id),
        }), 200
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        print("Erro ao finalizar serviço:", e)
        return jsonify({"erro": str(e)}), 500
