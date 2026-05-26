from flask_socketio import emit, join_room
from app.services.chat_json_service import gerar_id_conversa, salvar_mensagem

def register_chat_events(socketio):

    def entrar_na_sala(data):
        try:
            conversa_id = data.get("conversa_id") or data.get("id_conversa")

            if not conversa_id:
                conversa_id = gerar_id_conversa(
                    data.get("remetente_id") or data.get("user1"),
                    data.get("destinatario_id") or data.get("user2"),
                )

            join_room(conversa_id)
            emit("chat_joined", {"conversa_id": conversa_id})
        except Exception as e:
            emit("erro_chat", {"erro": str(e)})

    @socketio.on("join_chat")
    def join_chat(data):
        entrar_na_sala(data or {})

    @socketio.on("entrar_conversa")
    def entrar_conversa(data):
        entrar_na_sala(data or {})

    @socketio.on("entrar_sala")
    def entrar_sala(data):
        entrar_na_sala(data or {})

    @socketio.on("enviar_mensagem")
    def enviar_mensagem(data):
        try:
            id_remetente = int(data.get("id_remetente"))
            id_destinatario = int(data.get("id_destinatario"))
            texto = (data.get("texto") or "").strip()

            mensagem = salvar_mensagem(id_remetente, id_destinatario, texto)
        except Exception as e:
            emit("erro_chat", {"erro": str(e)})
            return

        # Emitir para todos na sala da conversa
        payload = {
            **mensagem,
            "id_conversa": mensagem["conversa_id"],
            "data": mensagem["data_envio"],
        }

        emit("receive_message", payload, room=mensagem["conversa_id"])
        emit("receber_mensagem", payload, room=mensagem["conversa_id"])
        emit("nova_mensagem", payload, room=mensagem["conversa_id"])

    @socketio.on("send_message")
    def send_message(data):
        enviar_mensagem(data or {})
