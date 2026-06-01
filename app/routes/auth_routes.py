import os
import json
import random
import sqlite3
import smtplib
from datetime import datetime, timedelta
from email.message import EmailMessage
from app.utils.upload import salvar_foto
from app.utils.security import hash_senha

from flask import Blueprint, request, jsonify

from app.database.connection import get_connection
from app.services.auth_service import cadastrar_usuario, login_usuario, login_admin

auth = Blueprint("auth", __name__)


def validar_campos_obrigatorios(payload, campos):
    faltantes = [campo for campo in campos if not payload.get(campo)]
    return faltantes


def normalizar_tipo_usuario(tipo):
    aliases = {
        "consumidor": "contratante",
        "contratante": "contratante",
        "cliente": "contratante",
        "prestador": "contratado",
        "profissional": "contratado",
        "contratado": "contratado",
    }

    return aliases.get(str(tipo or "contratante").strip().lower())


def validar_tipo_usuario(tipo):
    return normalizar_tipo_usuario(tipo) in ("contratante", "contratado")


def normalizar_data_nascimento(valor):
    if not valor:
        return None

    valor = str(valor).strip()

    formatos = ("%Y-%m-%d", "%d/%m/%Y")

    for formato in formatos:
        try:
            data = datetime.strptime(valor, formato).date()
        except ValueError:
            continue

        if data > datetime.now().date():
            raise ValueError("A data de nascimento não pode ser futura")

        return data.isoformat()

    raise ValueError("Data de nascimento inválida. Use o formato dd/mm/aaaa.")


@auth.route("/register", methods=["POST"])
def register():
    data = request.form if request.form else (request.json or {})

    foto = request.files.get("foto")
    tipo = normalizar_tipo_usuario(data.get("tipo", "contratante"))

    faltantes = validar_campos_obrigatorios(data, ["nome", "email", "senha"])
    if faltantes:
        return jsonify({"erro": f"Campos obrigatórios faltando: {', '.join(faltantes)}"}), 400

    if not validar_tipo_usuario(tipo):
        return jsonify({"erro": "Tipo de usuário inválido. Use 'contratante' ou 'contratado'"}), 400

    if tipo == "contratado":
        if not data.get("profissao"):
            return jsonify({"erro": "Profissão é obrigatória para trabalhadores"}), 400
        if not foto:
            return jsonify({"erro": "A foto de perfil é obrigatória para trabalhadores"}), 400

    endereco = data.get("endereco")

    if isinstance(endereco, str):
        try:
            endereco = json.loads(endereco)
        except json.JSONDecodeError:
            return jsonify({"erro": "Endereço inválido. Envie JSON válido."}), 400

    if endereco is not None and not isinstance(endereco, dict):
        return jsonify({"erro": "Endereço deve ser um objeto JSON"}), 400

    try:
        caminho_foto = None
        data_nascimento = normalizar_data_nascimento(data.get("data_nascimento"))

        if foto and getattr(foto, 'filename', None):
            caminho_foto = salvar_foto(foto)

        cadastrar_usuario(
            data["nome"],
            data["email"],
            data["senha"],
            tipo,
            data.get("descricao"),
            data.get("telefone"),
            endereco,
            data.get("profissao"),
            caminho_foto,
            data_nascimento
        )

    except sqlite3.IntegrityError:
        return jsonify({"erro": "Este email ja esta cadastrado"}), 409

    except ValueError as e:
        return jsonify({"erro": str(e)}), 400

    except Exception as e:
        print("Erro ao cadastrar usuário:", str(e))
        return jsonify({"erro": "Erro ao criar usuário"}), 500

    return jsonify({"msg": "Usuário criado"}), 201


@auth.route("/login", methods=["POST"])
def login():
    data = request.json or {}

    faltantes = validar_campos_obrigatorios(data, ["email", "senha"])
    if faltantes:
        return jsonify({"erro": f"Campos obrigatórios faltando: {', '.join(faltantes)}"}), 400

    result = login_usuario(data["email"], data["senha"])

    if result:
        return jsonify(result)

    return jsonify({"erro": "Credenciais inválidas"}), 401


@auth.route("/admin/login", methods=["POST"])
def login_admin_route():
    data = request.json or {}

    faltantes = validar_campos_obrigatorios(data, ["email", "senha"])
    if faltantes:
        return jsonify({"erro": f"Campos obrigatórios faltando: {', '.join(faltantes)}"}), 400

    result = login_admin(data["email"], data["senha"])

    if result:
        return jsonify(result)

    return jsonify({"erro": "Acesso negado"}), 403


@auth.route("/admin/create", methods=["POST"])
def create_admin():
    data = request.json or {}

    faltantes = validar_campos_obrigatorios(data, ["email", "senha"])
    if faltantes:
        return jsonify({"erro": f"Campos obrigatórios faltando: {', '.join(faltantes)}"}), 400

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("BEGIN IMMEDIATE")
        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE tipo_usuario = 'admin'")
        admin_count = cursor.fetchone()[0]

        if admin_count > 0:
            conn.rollback()
            return jsonify({"erro": "Admin já existe"}), 403

        senha_hash = hash_senha(data["senha"])
        cursor.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo_usuario) VALUES (?, ?, ?, 'admin')",
            (data.get("nome", "Administrador"), data["email"], senha_hash)
        )

        user_id = cursor.lastrowid
        conn.commit()

    except sqlite3.IntegrityError:
        conn.rollback()
        return jsonify({"erro": "Este email já está cadastrado"}), 409

    except Exception as e:
        conn.rollback()
        print("Erro ao criar admin:", str(e))
        return jsonify({"erro": "Erro ao criar admin"}), 500

    finally:
        conn.close()

    return jsonify({
        "msg": "Admin criado com sucesso",
        "user_id": user_id
    })


@auth.route("/admin/check", methods=["GET"])
def check_admin():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM usuarios WHERE tipo_usuario = 'admin'")
    admin_count = cursor.fetchone()[0]

    conn.close()

    return jsonify({"hasAdmin": admin_count > 0})


def criar_tabela_codigos_verificacao(cursor):
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS codigos_verificacao (
        id_codigo INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL,
        codigo TEXT NOT NULL,
        expiracao DATETIME NOT NULL,
        verificado INTEGER DEFAULT 0
    )
    """)


def criar_tabela_codigos_recuperacao_senha(cursor):
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS codigos_recuperacao_senha (
        id_codigo INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL,
        codigo TEXT NOT NULL,
        expiracao DATETIME NOT NULL,
        verificado INTEGER DEFAULT 0,
        usado INTEGER DEFAULT 0
    )
    """)

    cursor.execute("PRAGMA table_info(codigos_recuperacao_senha)")
    colunas = [coluna[1] for coluna in cursor.fetchall()]

    if "usado" not in colunas:
        cursor.execute("ALTER TABLE codigos_recuperacao_senha ADD COLUMN usado INTEGER DEFAULT 0")


def buscar_usuario_por_email(cursor, email):
    cursor.execute("""
        SELECT id_usuario, email
        FROM usuarios
        WHERE lower(email) = lower(?)
        LIMIT 1
    """, (email,))

    return cursor.fetchone()


def enviar_email_codigo(destinatario, codigo):
    email_remetente = os.getenv("EMAIL_REMETENTE")
    senha_app = os.getenv("SENHA_APP_EMAIL")

    if not email_remetente or not senha_app:
        raise Exception("EMAIL_REMETENTE ou SENHA_APP_EMAIL não configurados")

    mensagem = EmailMessage()
    mensagem["Subject"] = "Código de verificação - ProntoAqui"
    mensagem["From"] = email_remetente
    mensagem["To"] = destinatario
    mensagem.set_content(f"Seu código de verificação é: {codigo}")

    with smtplib.SMTP("smtp.gmail.com", 587, timeout=15) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(email_remetente, senha_app)
        smtp.send_message(mensagem)


@auth.route("/send-code", methods=["POST"])
def enviar_codigo():
    data = request.json or {}
    email = data.get("email")

    if not email:
        return jsonify({"erro": "Email é obrigatório"}), 400

    codigo = str(random.randint(100000, 999999))
    expiracao = datetime.now() + timedelta(minutes=10)

    conn = get_connection()
    cursor = conn.cursor()

    criar_tabela_codigos_verificacao(cursor)

    cursor.execute("""
    INSERT INTO codigos_verificacao (email, codigo, expiracao, verificado)
    VALUES (?, ?, ?, 0)
    """, (email, codigo, expiracao.isoformat()))

    conn.commit()
    conn.close()

    print("Tentando enviar codigo para:", email)
    print("EMAIL_REMETENTE configurado:", bool(os.getenv("EMAIL_REMETENTE")))
    print("SENHA_APP_EMAIL configurada:", bool(os.getenv("SENHA_APP_EMAIL")))

    try:
        enviar_email_codigo(email, codigo)
        print("Email enviado com sucesso para:", email)

        return jsonify({
            "msg": "Código enviado para o email"
        }), 200

    except Exception as e:
        print("Erro ao enviar email:", e)
        print("Código de teste gerado:", codigo)

        return jsonify({
            "msg": "Modo teste: código gerado com sucesso",
            "codigo_teste": codigo
        }), 200

    return jsonify({"msg": "Código enviado para o email"}), 200


@auth.route("/verify-code", methods=["POST"])
def verificar_codigo():
    data = request.json or {}

    email = data.get("email")
    codigo = data.get("codigo")

    if not email or not codigo:
        return jsonify({"erro": "Email e código são obrigatórios"}), 400

    conn = get_connection()
    cursor = conn.cursor()

    criar_tabela_codigos_verificacao(cursor)

    cursor.execute("""
        SELECT id_codigo, expiracao, verificado
        FROM codigos_verificacao
        WHERE email = ? AND codigo = ?
        ORDER BY id_codigo DESC
        LIMIT 1
    """, (email, codigo))

    registro = cursor.fetchone()

    if not registro:
        conn.close()
        return jsonify({"erro": "Código inválido"}), 400

    expiracao = datetime.fromisoformat(registro["expiracao"])

    if datetime.now() > expiracao:
        conn.close()
        return jsonify({"erro": "Código expirado"}), 400

    if registro["verificado"] == 0:
        cursor.execute("""
            UPDATE codigos_verificacao
            SET verificado = 1
            WHERE id_codigo = ?
        """, (registro["id_codigo"],))

        conn.commit()

    conn.close()

    return jsonify({"msg": "Código verificado com sucesso"}), 200


@auth.route("/forgot-password/send-code", methods=["POST"])
def enviar_codigo_recuperacao_senha():
    data = request.json or {}
    email = str(data.get("email") or "").strip()

    if not email:
        return jsonify({"erro": "Email é obrigatório"}), 400

    codigo = str(random.randint(100000, 999999))
    expiracao = datetime.now() + timedelta(minutes=10)

    conn = get_connection()
    cursor = conn.cursor()

    try:
        criar_tabela_codigos_recuperacao_senha(cursor)

        if not buscar_usuario_por_email(cursor, email):
            return jsonify({"erro": "E-mail não encontrado."}), 404

        cursor.execute("""
            INSERT INTO codigos_recuperacao_senha (
                email, codigo, expiracao, verificado, usado
            )
            VALUES (?, ?, ?, 0, 0)
        """, (email, codigo, expiracao.isoformat()))

        conn.commit()

    finally:
        conn.close()

    try:
        enviar_email_codigo(email, codigo)

        return jsonify({
            "msg": "Código enviado para o email"
        }), 200

    except Exception as e:
        print("Erro ao enviar email de recuperação:", e)
        print("Código de recuperação para teste:", codigo)

        return jsonify({
            "msg": "Modo teste: código gerado com sucesso",
            "codigo_teste": codigo
        }), 200


@auth.route("/forgot-password/verify-code", methods=["POST"])
def verificar_codigo_recuperacao_senha():
    data = request.json or {}
    email = str(data.get("email") or "").strip()
    codigo = str(data.get("codigo") or "").strip()

    if not email or not codigo:
        return jsonify({"erro": "Email e código são obrigatórios"}), 400

    conn = get_connection()
    cursor = conn.cursor()

    try:
        criar_tabela_codigos_recuperacao_senha(cursor)

        cursor.execute("""
            SELECT id_codigo, expiracao, usado
            FROM codigos_recuperacao_senha
            WHERE lower(email) = lower(?) AND codigo = ?
            ORDER BY id_codigo DESC
            LIMIT 1
        """, (email, codigo))

        registro = cursor.fetchone()

        if not registro:
            return jsonify({"erro": "Código inválido"}), 400

        if registro["usado"]:
            return jsonify({"erro": "Código já utilizado"}), 400

        expiracao = datetime.fromisoformat(registro["expiracao"])

        if datetime.now() > expiracao:
            return jsonify({"erro": "Código expirado"}), 400

        cursor.execute("""
            UPDATE codigos_recuperacao_senha
            SET verificado = 1
            WHERE id_codigo = ?
        """, (registro["id_codigo"],))

        conn.commit()

    finally:
        conn.close()

    return jsonify({"msg": "Código verificado com sucesso"}), 200


@auth.route("/forgot-password/reset", methods=["POST"])
def redefinir_senha():
    data = request.json or {}
    email = str(data.get("email") or "").strip()
    codigo = str(data.get("codigo") or "").strip()
    nova_senha = str(data.get("nova_senha") or "")

    if not email or not codigo or not nova_senha:
        return jsonify({"erro": "Email, código e nova senha são obrigatórios"}), 400

    if len(nova_senha) < 6:
        return jsonify({"erro": "A nova senha deve ter pelo menos 6 caracteres."}), 400

    conn = get_connection()
    cursor = conn.cursor()

    try:
        criar_tabela_codigos_recuperacao_senha(cursor)

        usuario = buscar_usuario_por_email(cursor, email)

        if not usuario:
            return jsonify({"erro": "E-mail não encontrado."}), 404

        cursor.execute("""
            SELECT id_codigo, expiracao, verificado, usado
            FROM codigos_recuperacao_senha
            WHERE lower(email) = lower(?) AND codigo = ?
            ORDER BY id_codigo DESC
            LIMIT 1
        """, (email, codigo))

        registro = cursor.fetchone()

        if not registro:
            return jsonify({"erro": "Código inválido"}), 400

        if registro["usado"]:
            return jsonify({"erro": "Código já utilizado"}), 400

        if not registro["verificado"]:
            return jsonify({"erro": "Código ainda não verificado"}), 400

        expiracao = datetime.fromisoformat(registro["expiracao"])

        if datetime.now() > expiracao:
            return jsonify({"erro": "Código expirado"}), 400

        senha_hash = hash_senha(nova_senha)

        cursor.execute("""
            UPDATE usuarios
            SET senha = ?
            WHERE id_usuario = ?
        """, (senha_hash, usuario["id_usuario"]))

        cursor.execute("""
            UPDATE codigos_recuperacao_senha
            SET usado = 1
            WHERE id_codigo = ?
        """, (registro["id_codigo"],))

        conn.commit()

    except Exception as e:
        conn.rollback()
        print("Erro ao redefinir senha:", str(e))
        return jsonify({"erro": "Não foi possível alterar a senha."}), 500

    finally:
        conn.close()

    return jsonify({"msg": "Senha alterada com sucesso."}), 200
