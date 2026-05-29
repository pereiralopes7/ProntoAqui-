from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_socketio import SocketIO
import os
from pathlib import Path
import subprocess
import sys

from app.sockets.chat_socket import register_chat_events

from app.routes.auth_routes import auth, register
from app.routes.usuario_routes import usuario
from app.routes.usuario_routes import normalizar_foto
from app.routes.chat_routes import chat
from app.routes.pagamento_routes import pagamento
from app.routes.admin_routes import admin_bp
from app.services.chat_json_service import limpar_mensagens_antigas
from app.services.servico_status_service import carregar_status

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = PROJECT_ROOT / "BrunoDemaze-repo"
UPLOAD_FOLDER_ABSOLUTE = PROJECT_ROOT / "uploads"
UPLOAD_FOLDER_ABSOLUTE.mkdir(parents=True, exist_ok=True)

app = Flask(
    __name__,
    static_folder=None,
    template_folder=str(FRONTEND_DIR),
)
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode=os.environ.get("SOCKETIO_ASYNC_MODE", "threading"),
)


# Inicializar banco de dados automaticamente
def init_database():
    """Inicializa o banco de dados se não existir e popula com dados de teste."""
    from app.database.connection import get_database_path

    db_path = Path(get_database_path())

    # Se o banco não existe, criar e popular
    if not db_path.exists():
        print("[DB] Banco não encontrado. Inicializando...")

        # Executar reset_db.py
        try:
            reset_script = Path(__file__).parent / "reset_db.py"
            print(f"[DB] Executando {reset_script}...")
            subprocess.run(
                [sys.executable, "-m", "app.reset_db"],
                check=True,
                cwd=str(PROJECT_ROOT),
            )
            print("[DB] reset_db.py concluído!")
        except Exception as e:
            print(f"[DB] Erro ao executar reset_db.py: {e}")
            return False

        # Executar seed_db.py
        try:
            seed_script = Path(__file__).parent / "seed_db.py"
            print(f"[DB] Executando {seed_script}...")
            subprocess.run(
                [sys.executable, "-m", "app.seed_db"],
                check=True,
                cwd=str(PROJECT_ROOT),
            )
            print("[DB] seed_db.py concluído!")
        except Exception as e:
            print(f"[DB] Erro ao executar seed_db.py: {e}")
            return False
    else:
        print(f"[DB] Banco encontrado em {db_path}")

    return True


# Inicializar ao iniciar a aplicação
with app.app_context():
    init_database()
    limpar_mensagens_antigas()
    carregar_status()

app.register_blueprint(pagamento)

app.register_blueprint(auth, url_prefix="/auth")
app.add_url_rule("/register", "register_root", register, methods=["POST"])

app.register_blueprint(usuario)

app.register_blueprint(chat)

app.register_blueprint(admin_bp, url_prefix="/admin")

register_chat_events(socketio)

@app.route("/buscar-profissionais", methods=["GET"])
def buscar_profissionais():
    """Busca profissionais por texto na query string."""
    from app.database.connection import get_connection
    from datetime import datetime
    import unicodedata

    try:
        def normalize_text(text):
            if not text:
                return ""

            return "".join(
                c
                for c in unicodedata.normalize("NFD", text)
                if unicodedata.category(c) != "Mn"
            ).lower()

        profissoes_validas = [
            "Pedreiro",
            "Encanador",
            "Eletricista",
            "Diarista",
            "Jardineiro",
            "Pintor",
            "Marceneiro",
            "Mecânico",
            "Técnico de informática",
            "Babá",
            "Cuidador de idosos",
            "Personal trainer",
            "Professor particular",
            "Chaveiro",
            "Ar-condicionado"
        ]

        query = request.args.get("q", "").strip()
        normalized_query = normalize_text(query)
        print(f"[BUSCA] Query recebida: '{query}' | Normalizada: '{normalized_query}'")
        usuario_logado_id = None

        auth_header = request.headers.get("Authorization", "")

        if auth_header.startswith("Bearer "):
            try:
                from app.utils.jwt_handler import decodificar_token

                payload = decodificar_token(auth_header.replace("Bearer ", "", 1))
                usuario_logado_id = payload.get("user_id") if payload else None
            except Exception as e:
                print(f"[BUSCA] Token ignorado: {e}")

        conn = get_connection()
        cursor = conn.cursor()

        sql = """
        SELECT u.id_usuario, u.nome, u.cidade, u.data_nascimento,
               u.foto_perfil, u.foto_posicao_y, p.profissao, p.descricao
        FROM usuarios u
        JOIN perfis_trabalhador p ON u.id_usuario = p.usuario_id
        WHERE u.tipo_usuario IN ('contratado', 'prestador')
        """

        cursor.execute(sql)
        rows = cursor.fetchall()
        print(f"[BUSCA] Total de profissionais no banco: {len(rows)}")

        if len(rows) > 0:
            print(f"[BUSCA] Primeiro registro: {dict(rows[0])}")

        conn.close()

        profissionais = []

        for r in rows:
            if usuario_logado_id and int(r["id_usuario"]) == int(usuario_logado_id):
                continue

            nome = r["nome"] or ""
            profissao = r["profissao"] or "Não informado"
            descricao = r["descricao"] or ""
            cidade = r["cidade"] or ""

            # Limpar nome (remover profissão do final se existir)
            for p in profissoes_validas:
                if nome.lower().endswith(p.lower()):
                    nome = nome[: -len(p)].strip()
                    break

            idade = None
            if r["data_nascimento"]:
                try:
                    data_nasc = datetime.fromisoformat(r["data_nascimento"])
                    idade = datetime.now().year - data_nasc.year
                    if (datetime.now().month, datetime.now().day) < (data_nasc.month, data_nasc.day):
                        idade -= 1
                except ValueError:
                    pass

            search_text = normalize_text(f"{nome} {profissao} {descricao} {cidade}")

            if normalized_query in search_text or not normalized_query:
                profissionais.append({
                    "id": r["id_usuario"],
                    "nome": nome,
                    "profissao": profissao,
                    "descricao": descricao,
                    "cidade": cidade,
                    "idade": idade,
                    "foto_perfil": normalizar_foto(r["foto_perfil"] or ""),
                    "foto_posicao_y": r["foto_posicao_y"] if r["foto_posicao_y"] is not None else 50,
                })

        print(f"[BUSCA] Resultados encontrados: {len(profissionais)}")
        return jsonify(profissionais)

    except Exception as e:
        print(f"[ERRO] Erro ao buscar profissionais: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"erro": str(e)}), 500


@app.route("/")
def serve_index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER_ABSOLUTE, filename)


@app.route("/<path:filename>")
def serve_static(filename):
    """Serve arquivos estáticos (HTML, CSS, JS, imagens, etc)"""
    return send_from_directory(FRONTEND_DIR, filename)


@app.route("/admin/test2", methods=["GET"])
def admin_test():
    return jsonify({"message": "Admin test working!", "status": "ok"})


@app.route("/perfil")
def perfil():
    from app.database.connection import get_connection
    from datetime import date

    user_id = request.args.get("id")
    if not user_id:
        return "ID não fornecido", 400

    def calcular_idade(data_nascimento):
        if not data_nascimento:
            return None

        try:
            nascimento = date.fromisoformat(str(data_nascimento)[:10])
        except ValueError:
            return None

        hoje = date.today()
        idade = hoje.year - nascimento.year

        if (hoje.month, hoje.day) < (nascimento.month, nascimento.day):
            idade -= 1

        return idade if idade >= 0 else None

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        u.id_usuario,
        u.nome,
        u.cidade,
        u.foto_perfil,
        u.foto_posicao_y,
        u.data_nascimento,
        u.tipo_usuario,
        p.profissao,
        p.descricao
    FROM usuarios u
    LEFT JOIN perfis_trabalhador p ON u.id_usuario = p.usuario_id
    WHERE u.id_usuario = ?
      AND u.tipo_usuario IN ('contratado', 'prestador')
    """, (user_id,))

    user = cursor.fetchone()
    # Buscar mensagens da conversa (usando id_usuario como id_conversa)
    # O histórico de mensagens é carregado pelo JavaScript através da rota /historico
    mensagens = []
    conn.close()

    if not user:
        return "Este usuário não é um prestador de serviço.", 404

    profissional = {
        "id": user["id_usuario"],
        "nome": user["nome"],
        "tipo_usuario": user["tipo_usuario"],
        "idade": calcular_idade(user["data_nascimento"]),
        "idade_texto": "",
        "profissao": user["profissao"] or "Profissão não informada",
        "descricao": user["descricao"] or "Descrição não informada",
        "cidade": user["cidade"] or "Não informado",
        "foto_perfil": normalizar_foto(user["foto_perfil"] or ""),
        "foto_posicao_y": user["foto_posicao_y"] if user["foto_posicao_y"] is not None else 50,
    }

    if profissional["idade"] is None:
        profissional["idade_texto"] = "Idade não informada"
    else:
        profissional["idade_texto"] = f"{profissional['idade']} anos"

    profissional["imagem"] = profissional["foto_perfil"] or "/img/default-user.svg"

    return render_template("perfil.html", profissional=profissional, mensagens=mensagens)


if __name__ == "__main__":
    print(app.url_map)
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")
    debug = os.environ.get("FLASK_DEBUG") == "1"
    socketio.run(
        app,
        host=host,
        port=port,
        debug=debug,
        allow_unsafe_werkzeug=True,
    )
