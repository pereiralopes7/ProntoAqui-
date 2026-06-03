from flask import Blueprint, request, jsonify
import jwt
import json
import sqlite3
from datetime import datetime

from app.utils.upload import salvar_foto
from app.database.connection import get_connection
from app.utils.jwt_handler import decodificar_token
from app.services.usuario_service import (
    buscar_trabalhadores_proximos,
    buscar_profissionais_por_texto,
    buscar_profissionais
)

usuario = Blueprint("usuario", __name__)


def get_user_id_from_token():
    auth_header = request.headers.get("Authorization", "")

    if not auth_header.startswith("Bearer "):
        return None

    token = auth_header.replace("Bearer ", "", 1)

    try:
        payload = decodificar_token(token)

        if not payload:
            return None

        return payload.get("user_id")

    except (jwt.PyJWTError, AttributeError):
        return None


def tabela_existe(cursor, nome_tabela):
    cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table' AND name = ?
    """, (nome_tabela,))

    return cursor.fetchone() is not None


def coluna_existe(cursor, tabela, coluna):
    if not tabela_existe(cursor, tabela):
        return False

    cursor.execute(f"PRAGMA table_info({tabela})")
    colunas = [item[1] for item in cursor.fetchall()]

    return coluna in colunas


def adicionar_coluna_se_nao_existir(cursor, tabela, coluna, definicao):
    if not coluna_existe(cursor, tabela, coluna):
        cursor.execute(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {definicao}")


def normalizar_foto(foto_perfil):
    if not foto_perfil:
        return ""

    foto_perfil = str(foto_perfil).strip().replace("\\", "/")

    if not foto_perfil:
        return ""

    if foto_perfil.startswith("http"):
        return foto_perfil

    if foto_perfil.startswith("/uploads/"):
        return foto_perfil

    if foto_perfil.startswith("uploads/"):
        return "/" + foto_perfil

    if foto_perfil.startswith("/"):
        return foto_perfil

    return "/uploads/" + foto_perfil


def normalizar_posicao_foto(valor):
    try:
        valor = int(valor)
    except (TypeError, ValueError):
        return 50

    return max(0, min(100, valor))


def normalizar_data_nascimento(valor):
    if valor is None:
        return None

    valor = str(valor).strip()

    if not valor:
        return None

    for formato in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            data = datetime.strptime(valor, formato).date()
        except ValueError:
            continue

        if data > datetime.now().date():
            raise ValueError("A data de nascimento não pode ser futura")

        return data.isoformat()

    raise ValueError("Data de nascimento inválida. Use o formato dd/mm/aaaa.")


def get_coluna_endereco(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
            nome char(70) NOT NULL,
            email char(50) UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            tipo_usuario TEXT DEFAULT 'contratante',
            telefone char(15),
            cidade varchar(20),
            estado varchar(20),
            latitude REAL,
            longitude REAL,
            foto_perfil TEXT,
            foto_posicao_y INTEGER DEFAULT 50,
            foto_posicao_x INTEGER DEFAULT 50,
            data_nascimento DATE,
            data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("PRAGMA table_info(usuarios)")
    colunas_usuario = [coluna[1] for coluna in cursor.fetchall()]

    colunas_usuarios_obrigatorias = {
        "tipo_usuario": "TEXT DEFAULT 'contratante'",
        "telefone": "char(15)",
        "cidade": "varchar(20)",
        "estado": "varchar(20)",
        "foto_perfil": "TEXT",
        "foto_posicao_y": "INTEGER DEFAULT 50",
        "foto_posicao_x": "INTEGER DEFAULT 50",
        "data_nascimento": "DATE",
    }

    for coluna, definicao in colunas_usuarios_obrigatorias.items():
        if coluna not in colunas_usuario:
            cursor.execute(f"ALTER TABLE usuarios ADD COLUMN {coluna} {definicao}")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS enderecos_usuario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER UNIQUE NOT NULL,
            rua varchar(120),
            numero varchar(20),
            cep varchar(12),
            bairro varchar(80),
            complemento varchar(120),
            ponto_referencia varchar(160),
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id_usuario) ON DELETE CASCADE
        )
    """)

    colunas_endereco_obrigatorias = {
        "usuario_id": "INTEGER",
        "rua": "varchar(120)",
        "numero": "varchar(20)",
        "cep": "varchar(12)",
        "bairro": "varchar(80)",
        "complemento": "varchar(120)",
        "ponto_referencia": "varchar(160)",
    }

    for coluna, definicao in colunas_endereco_obrigatorias.items():
        adicionar_coluna_se_nao_existir(
            cursor,
            "enderecos_usuario",
            coluna,
            definicao
        )

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS perfis_trabalhador (
            id_perfil INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER UNIQUE NOT NULL,
            profissao TEXT,
            descricao TEXT,
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id_usuario) ON DELETE CASCADE
        )
    """)

    cursor.execute("PRAGMA table_info(perfis_trabalhador)")
    colunas_perfil = [coluna[1] for coluna in cursor.fetchall()]

    if "profissao" not in colunas_perfil:
        cursor.execute("ALTER TABLE perfis_trabalhador ADD COLUMN profissao TEXT")

    if "descricao" not in colunas_perfil:
        cursor.execute("ALTER TABLE perfis_trabalhador ADD COLUMN descricao TEXT")


def valor_endereco(endereco, endereco_atual, campo):
    if campo in endereco:
        return endereco.get(campo) or ""

    if endereco_atual:
        return endereco_atual[campo] or ""

    return ""


@usuario.route("/upload-foto/", methods=["POST"])
def upload_foto():
    user_id = get_user_id_from_token()

    if not user_id:
        return jsonify({"erro": "Usuario nao autenticado"}), 401

    foto = request.files.get("foto")

    if not foto:
        return jsonify({"erro": "Nenhuma foto enviada"}), 400

    try:
        caminho = salvar_foto(foto)

        conn = get_connection()
        cursor = conn.cursor()

        get_coluna_endereco(cursor)

        cursor.execute("""
            UPDATE usuarios
            SET foto_perfil = ?
            WHERE id_usuario = ?
        """, (caminho, user_id))

        conn.commit()
        conn.close()

        return jsonify({
            "msg": "Foto salva",
            "foto_perfil": normalizar_foto(caminho)
        }), 200

    except ValueError as e:
        return jsonify({"erro": str(e)}), 400

    except Exception as e:
        print("Erro ao salvar foto:", str(e))
        return jsonify({
            "erro": "Nao foi possivel salvar a foto",
            "detalhe": str(e)
        }), 500


@usuario.route("/usuario/me", methods=["GET"])
def buscar_minha_conta():
    user_id = get_user_id_from_token()

    if not user_id:
        return jsonify({"erro": "Usuario nao autenticado"}), 401

    conn = get_connection()
    cursor = conn.cursor()

    try:
        get_coluna_endereco(cursor)

        cursor.execute("""
            SELECT 
                u.id_usuario,
                u.nome,
                u.email,
                u.telefone,
                u.data_nascimento,
                u.cidade,
                u.estado,
                u.tipo_usuario,
                u.foto_perfil,
                u.foto_posicao_y,
                u.foto_posicao_x,
                e.rua,
                e.numero,
                e.cep,
                e.bairro,
                e.complemento,
                e.ponto_referencia,
                p.profissao,
                p.descricao
            FROM usuarios u
            LEFT JOIN enderecos_usuario e ON e.usuario_id = u.id_usuario
            LEFT JOIN perfis_trabalhador p ON p.usuario_id = u.id_usuario
            WHERE u.id_usuario = ?
        """, (user_id,))

        usuario_logado = cursor.fetchone()
        conn.close()

        if not usuario_logado:
            return jsonify({"erro": "Usuario nao encontrado"}), 404

        return jsonify({
            "id": usuario_logado["id_usuario"],
            "nome": usuario_logado["nome"],
            "email": usuario_logado["email"],
            "telefone": usuario_logado["telefone"] or "",
            "data_nascimento": usuario_logado["data_nascimento"] or "",
            "cidade": usuario_logado["cidade"] or "",
            "estado": usuario_logado["estado"] or "",
            "foto_perfil": normalizar_foto(usuario_logado["foto_perfil"] or ""),
            "foto_posicao_y": usuario_logado["foto_posicao_y"] if usuario_logado["foto_posicao_y"] is not None else 50,
            "foto_posicao_x": usuario_logado["foto_posicao_x"] if usuario_logado["foto_posicao_x"] is not None else 50,
            "tipo": usuario_logado["tipo_usuario"],
            "tipo_usuario": usuario_logado["tipo_usuario"],
            "profissao": usuario_logado["profissao"] or "",
            "descricao": usuario_logado["descricao"] or "",
            "endereco": {
                "rua": usuario_logado["rua"] or "",
                "numero": usuario_logado["numero"] or "",
                "cep": usuario_logado["cep"] or "",
                "bairro": usuario_logado["bairro"] or "",
                "complemento": usuario_logado["complemento"] or "",
                "ponto_referencia": usuario_logado["ponto_referencia"] or ""
            }
        }), 200

    except Exception as e:
        conn.close()
        print("Erro ao buscar conta:", str(e))
        return jsonify({
            "erro": "Nao foi possivel carregar seus dados",
            "detalhe": str(e)
        }), 500


@usuario.route("/usuario/me", methods=["PUT"])
def atualizar_minha_conta():
    user_id = get_user_id_from_token()

    if not user_id:
        return jsonify({"erro": "Usuario nao autenticado"}), 401

    data = request.form if request.form else (request.json or {})
    foto = request.files.get("foto")
    remover_foto = str(data.get("remover_foto", "")).lower() == "true"

    print("FORM:", request.form)
    print("FILES:", request.files)
    print("USER_ID:", user_id)

    conn = get_connection()
    cursor = conn.cursor()

    try:
        get_coluna_endereco(cursor)

        caminho_foto = None

        if foto and foto.filename:
            caminho_foto = salvar_foto(foto)

        cursor.execute("""
            SELECT tipo_usuario
            FROM usuarios
            WHERE id_usuario = ?
        """, (user_id,))

        usuario_atual = cursor.fetchone()

        if not usuario_atual:
            conn.close()
            return jsonify({"erro": "Usuario nao encontrado"}), 404

        tipo_usuario = usuario_atual["tipo_usuario"] or "contratante"

        nome = data.get("nome")
        email = data.get("email")
        telefone = data.get("telefone")
        data_nascimento = data.get("data_nascimento")
        cidade = data.get("cidade")
        estado = data.get("estado")

        campos = []
        valores = []

        if nome is not None:
            campos.append('"nome" = ?')
            valores.append(nome)

        if email is not None:
            campos.append('"email" = ?')
            valores.append(email)

        if telefone is not None:
            campos.append('"telefone" = ?')
            valores.append(telefone)

        if data_nascimento is not None:
            campos.append('"data_nascimento" = ?')
            valores.append(normalizar_data_nascimento(data_nascimento))

        if cidade is not None:
            campos.append('"cidade" = ?')
            valores.append(cidade)

        if estado is not None:
            campos.append('"estado" = ?')
            valores.append(estado)

        if caminho_foto:
            campos.append('"foto_perfil" = ?')
            valores.append(caminho_foto)
        elif remover_foto:
            campos.append('"foto_perfil" = ?')
            valores.append(None)

        if data.get("foto_posicao_y") is not None:
            campos.append('"foto_posicao_y" = ?')
            valores.append(normalizar_posicao_foto(data.get("foto_posicao_y")))

        if data.get("foto_posicao_x") is not None:
            campos.append('"foto_posicao_x" = ?')
            valores.append(normalizar_posicao_foto(data.get("foto_posicao_x")))

        if campos:
            valores.append(user_id)

            cursor.execute(f"""
                UPDATE usuarios
                SET {", ".join(campos)}
                WHERE id_usuario = ?
            """, valores)

        endereco = data.get("endereco") or {}

        if isinstance(endereco, str):
            try:
                endereco = json.loads(endereco)
            except Exception:
                endereco = {}

        if not isinstance(endereco, dict):
            endereco = {}

        campos_endereco_diretos = [
            "rua",
            "numero",
            "cep",
            "bairro",
            "complemento",
            "ponto_referencia",
        ]

        for campo in campos_endereco_diretos:
            if data.get(campo) is not None:
                endereco[campo] = data.get(campo)

        cursor.execute("""
            SELECT rua, numero, cep, bairro, complemento, ponto_referencia
            FROM enderecos_usuario
            WHERE usuario_id = ?
        """, (user_id,))

        endereco_atual = cursor.fetchone()

        endereco_final = {
            campo: valor_endereco(endereco, endereco_atual, campo)
            for campo in campos_endereco_diretos
        }

        if endereco_atual:
            cursor.execute("""
                UPDATE enderecos_usuario
                SET rua = ?,
                    numero = ?,
                    cep = ?,
                    bairro = ?,
                    complemento = ?,
                    ponto_referencia = ?
                WHERE usuario_id = ?
            """, (
                endereco_final["rua"],
                endereco_final["numero"],
                endereco_final["cep"],
                endereco_final["bairro"],
                endereco_final["complemento"],
                endereco_final["ponto_referencia"],
                user_id
            ))
        else:
            cursor.execute("""
                INSERT INTO enderecos_usuario (
                    usuario_id, rua, numero, cep, bairro, complemento, ponto_referencia
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                endereco_final["rua"],
                endereco_final["numero"],
                endereco_final["cep"],
                endereco_final["bairro"],
                endereco_final["complemento"],
                endereco_final["ponto_referencia"]
            ))

        profissao = data.get("profissao")
        descricao = data.get("descricao")

        deve_atualizar_perfil = (
            tipo_usuario in ("contratado", "prestador")
            or bool((profissao or "").strip())
            or bool((descricao or "").strip())
        )

        if deve_atualizar_perfil and (profissao is not None or descricao is not None):
            cursor.execute("""
                SELECT usuario_id
                FROM perfis_trabalhador
                WHERE usuario_id = ?
            """, (user_id,))

            perfil = cursor.fetchone()

            if perfil:
                cursor.execute("""
                    UPDATE perfis_trabalhador
                    SET profissao = ?, descricao = ?
                    WHERE usuario_id = ?
                """, (
                    profissao or "",
                    descricao or "",
                    user_id
                ))
            else:
                cursor.execute("""
                    INSERT INTO perfis_trabalhador (
                        usuario_id, profissao, descricao
                    )
                    VALUES (?, ?, ?)
                """, (
                    user_id,
                    profissao or "",
                    descricao or ""
                ))

        conn.commit()

        cursor.execute("""
            SELECT
                u.id_usuario,
                u.nome,
                u.email,
                u.telefone,
                u.data_nascimento,
                u.cidade,
                u.estado,
                u.tipo_usuario,
                u.foto_perfil,
                u.foto_posicao_y,
                u.foto_posicao_x,
                e.rua,
                e.numero,
                e.cep,
                e.bairro,
                e.complemento,
                e.ponto_referencia,
                p.profissao,
                p.descricao
            FROM usuarios u
            LEFT JOIN enderecos_usuario e ON e.usuario_id = u.id_usuario
            LEFT JOIN perfis_trabalhador p ON p.usuario_id = u.id_usuario
            WHERE u.id_usuario = ?
        """, (user_id,))

        usuario_atualizado = cursor.fetchone()
        foto_normalizada = normalizar_foto(usuario_atualizado["foto_perfil"] or "") if usuario_atualizado else ""
        foto_posicao_y = usuario_atualizado["foto_posicao_y"] if usuario_atualizado and usuario_atualizado["foto_posicao_y"] is not None else 50
        foto_posicao_x = usuario_atualizado["foto_posicao_x"] if usuario_atualizado and usuario_atualizado["foto_posicao_x"] is not None else 50
        data_nascimento_atualizada = ""
        if usuario_atualizado:
            data_nascimento_atualizada = usuario_atualizado["data_nascimento"] or ""

        conn.close()

        usuario_resposta = {}

        if usuario_atualizado:
            usuario_resposta = {
                "id": usuario_atualizado["id_usuario"],
                "id_usuario": usuario_atualizado["id_usuario"],
                "nome": usuario_atualizado["nome"],
                "email": usuario_atualizado["email"],
                "telefone": usuario_atualizado["telefone"] or "",
                "data_nascimento": data_nascimento_atualizada,
                "cidade": usuario_atualizado["cidade"] or "",
                "estado": usuario_atualizado["estado"] or "",
                "foto_perfil": foto_normalizada,
                "foto_posicao_y": foto_posicao_y,
                "foto_posicao_x": foto_posicao_x,
                "tipo": usuario_atualizado["tipo_usuario"],
                "tipo_usuario": usuario_atualizado["tipo_usuario"],
                "profissao": usuario_atualizado["profissao"] or "",
                "descricao": usuario_atualizado["descricao"] or "",
                "endereco": {
                    "rua": usuario_atualizado["rua"] or "",
                    "numero": usuario_atualizado["numero"] or "",
                    "cep": usuario_atualizado["cep"] or "",
                    "bairro": usuario_atualizado["bairro"] or "",
                    "complemento": usuario_atualizado["complemento"] or "",
                    "ponto_referencia": usuario_atualizado["ponto_referencia"] or ""
                }
            }

        return jsonify({
            "mensagem": "Dados atualizados com sucesso.",
            "usuario": usuario_resposta,
            "foto_perfil": foto_normalizada,
            "foto_posicao_y": foto_posicao_y,
            "foto_posicao_x": foto_posicao_x,
            "data_nascimento": data_nascimento_atualizada
        }), 200

    except ValueError as e:
        conn.rollback()
        conn.close()

        return jsonify({"erro": str(e)}), 400

    except sqlite3.IntegrityError:
        conn.rollback()
        conn.close()

        return jsonify({
            "erro": "Este email ja esta cadastrado em outra conta"
        }), 409

    except Exception as e:
        conn.rollback()
        conn.close()

        print("Erro ao atualizar conta:", e)

        return jsonify({"erro": str(e)}), 500


@usuario.route("/usuario/me", methods=["DELETE"])
def apagar_minha_conta():
    user_id = get_user_id_from_token()

    if not user_id:
        return jsonify({"erro": "Usuario nao autenticado"}), 401

    conn = None

    try:
        conn = get_connection()
        conn.execute("PRAGMA busy_timeout = 10000")
        cursor = conn.cursor()
        cursor.execute("BEGIN IMMEDIATE")

        get_coluna_endereco(cursor)

        # Apaga códigos de verificação do email do usuário
        if tabela_existe(cursor, "codigos_verificacao"):
            cursor.execute("""
                DELETE FROM codigos_verificacao
                WHERE email IN (
                    SELECT email FROM usuarios WHERE id_usuario = ?
                )
            """, (user_id,))

        # Mensagens
        if tabela_existe(cursor, "mensagens"):
            if coluna_existe(cursor, "mensagens", "remetente_id") and coluna_existe(cursor, "mensagens", "destinatario_id"):
                cursor.execute("""
                    DELETE FROM mensagens
                    WHERE remetente_id = ? OR destinatario_id = ?
                """, (user_id, user_id))

        # Pagamentos
        if tabela_existe(cursor, "pagamentos"):
            if coluna_existe(cursor, "pagamentos", "pagador_id") and coluna_existe(cursor, "pagamentos", "recebedor_id"):
                cursor.execute("""
                    DELETE FROM pagamentos
                    WHERE pagador_id = ? OR recebedor_id = ?
                """, (user_id, user_id))
            elif coluna_existe(cursor, "pagamentos", "usuario_id"):
                cursor.execute("""
                    DELETE FROM pagamentos
                    WHERE usuario_id = ?
                """, (user_id,))

        # Denuncias
        if tabela_existe(cursor, "denuncias"):
            if coluna_existe(cursor, "denuncias", "denunciante_id") and coluna_existe(cursor, "denuncias", "denunciado_id"):
                cursor.execute("""
                    DELETE FROM denuncias
                    WHERE denunciante_id = ? OR denunciado_id = ?
                """, (user_id, user_id))

        # Propostas relacionadas a serviços do usuário
        if tabela_existe(cursor, "propostas"):
            if coluna_existe(cursor, "propostas", "servico_id") and tabela_existe(cursor, "servicos"):
                if coluna_existe(cursor, "servicos", "contratante_id"):
                    cursor.execute("""
                        DELETE FROM propostas
                        WHERE servico_id IN (
                            SELECT id FROM servicos WHERE contratante_id = ?
                        )
                    """, (user_id,))

                if coluna_existe(cursor, "servicos", "usuario_id"):
                    cursor.execute("""
                        DELETE FROM propostas
                        WHERE servico_id IN (
                            SELECT id FROM servicos WHERE usuario_id = ?
                        )
                    """, (user_id,))

            if coluna_existe(cursor, "propostas", "trabalhador_id"):
                cursor.execute("""
                    DELETE FROM propostas
                    WHERE trabalhador_id = ?
                """, (user_id,))

            if coluna_existe(cursor, "propostas", "prestador_id"):
                cursor.execute("""
                    DELETE FROM propostas
                    WHERE prestador_id = ?
                """, (user_id,))

            if coluna_existe(cursor, "propostas", "usuario_id"):
                cursor.execute("""
                    DELETE FROM propostas
                    WHERE usuario_id = ?
                """, (user_id,))

        # Serviços
        if tabela_existe(cursor, "servicos"):
            if coluna_existe(cursor, "servicos", "contratante_id"):
                cursor.execute("""
                    DELETE FROM servicos
                    WHERE contratante_id = ?
                """, (user_id,))

            if coluna_existe(cursor, "servicos", "usuario_id"):
                cursor.execute("""
                    DELETE FROM servicos
                    WHERE usuario_id = ?
                """, (user_id,))

            if coluna_existe(cursor, "servicos", "prestador_id"):
                cursor.execute("""
                    DELETE FROM servicos
                    WHERE prestador_id = ?
                """, (user_id,))

        # Perfil, endereço e admin
        if tabela_existe(cursor, "perfis_trabalhador"):
            cursor.execute("""
                DELETE FROM perfis_trabalhador
                WHERE usuario_id = ?
            """, (user_id,))

        if tabela_existe(cursor, "enderecos_usuario"):
            cursor.execute("""
                DELETE FROM enderecos_usuario
                WHERE usuario_id = ?
            """, (user_id,))

        if tabela_existe(cursor, "admins"):
            if coluna_existe(cursor, "admins", "usuario_id"):
                cursor.execute("""
                    DELETE FROM admins
                    WHERE usuario_id = ?
                """, (user_id,))

        # Por último, apaga o usuário
        cursor.execute("""
            DELETE FROM usuarios
            WHERE id_usuario = ?
        """, (user_id,))

        conn.commit()

        return jsonify({"msg": "Conta apagada com sucesso"}), 200

    except Exception as e:
        if conn:
            conn.rollback()

        print("Erro ao apagar conta:", str(e))

        return jsonify({
            "erro": "Nao foi possivel apagar a conta",
            "detalhe": str(e)
        }), 500

    finally:
        if conn:
            conn.close()


@usuario.route("/proximos", methods=["GET"])
def proximos():
    lat = float(request.args.get("lat"))
    lon = float(request.args.get("lon"))

    dados = buscar_trabalhadores_proximos(lat, lon)

    return jsonify(dados)


@usuario.route("/search", methods=["GET"])
def search():
    q = request.args.get("q", "")

    if not q:
        return jsonify([])

    dados = buscar_profissionais_por_texto(q)

    return jsonify(dados)


@usuario.route("/buscar_profissionais", methods=["GET"])
def buscar_profissionais_route():
    q = request.args.get("q", "")

    if not q:
        return jsonify([])

    from app.services.usuario_service import buscar_profissionais_com_join

    dados = buscar_profissionais_com_join(q)

    return jsonify(dados)
