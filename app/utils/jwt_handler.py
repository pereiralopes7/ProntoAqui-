import jwt
import datetime
import os

SECRET = os.getenv(
    "JWT_SECRET",
    "prontoaqui_dev_secret_change_me_32_chars",
)


def gerar_token(user_id, tipo):
    payload = {
        "user_id": user_id,
        "tipo": tipo,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=5)
    }

    return jwt.encode(payload, SECRET, algorithm="HS256")


def verificar_token(token):
    try:
        return jwt.decode(token, SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None


# Compatibilidade com rotas antigas.
def decodificar_token(token):
    return verificar_token(token)
