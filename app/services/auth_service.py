from app.database.connection import get_connection
from app.utils.security import hash_senha, verificar_senha
from app.utils.jwt_handler import gerar_token


class EmailDuplicadoError(ValueError):
    pass


class TelefoneDuplicadoError(ValueError):
    pass


def normalizar_email(email):
    return str(email or "").strip().lower()


def normalizar_telefone(telefone):
    telefone = "".join(char for char in str(telefone or "") if char.isdigit())

    if len(telefone) != 11:
        raise ValueError("O telefone deve conter exatamente 11 números.")

    return telefone


def preparar_colunas_usuario(cursor):
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
    colunas = [coluna[1] for coluna in cursor.fetchall()]

    if "tipo_usuario" not in colunas:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN tipo_usuario TEXT DEFAULT 'contratante'")

    if "telefone" not in colunas:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN telefone char(15)")

    if "foto_perfil" not in colunas:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN foto_perfil TEXT")

    if "foto_posicao_y" not in colunas:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN foto_posicao_y INTEGER DEFAULT 50")

    if "foto_posicao_x" not in colunas:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN foto_posicao_x INTEGER DEFAULT 50")

    if "cidade" not in colunas:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN cidade varchar(20)")

    if "estado" not in colunas:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN estado varchar(20)")

    if "data_nascimento" not in colunas:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN data_nascimento DATE")

    endereco_com_acento = "endere\u00e7o"

    if "endereco" in colunas:
        return "endereco"

    if endereco_com_acento in colunas:
        return endereco_com_acento

    return None


def email_ja_cadastrado(cursor, email):
    cursor.execute("""
        SELECT 1
        FROM usuarios
        WHERE lower(trim(email)) = ?
        LIMIT 1
    """, (email,))

    return cursor.fetchone() is not None


def telefone_ja_cadastrado(cursor, telefone):
    cursor.execute("""
        SELECT telefone
        FROM usuarios
        WHERE telefone IS NOT NULL AND trim(telefone) != ''
    """)

    for usuario in cursor.fetchall():
        try:
            telefone_existente = normalizar_telefone(usuario["telefone"])
        except ValueError:
            continue

        if telefone_existente == telefone:
            return True

    return False

def garantir_tabela_endereco(cursor):
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

    cursor.execute("PRAGMA table_info(enderecos_usuario)")
    colunas = [coluna[1] for coluna in cursor.fetchall()]

    colunas_obrigatorias = {
        "usuario_id": "INTEGER",
        "rua": "varchar(120)",
        "numero": "varchar(20)",
        "cep": "varchar(12)",
        "bairro": "varchar(80)",
        "complemento": "varchar(120)",
        "ponto_referencia": "varchar(160)",
    }

    for coluna, definicao in colunas_obrigatorias.items():
        if coluna not in colunas:
            cursor.execute(f"ALTER TABLE enderecos_usuario ADD COLUMN {coluna} {definicao}")

def cadastrar_usuario(
    nome,
    email,
    senha,
    tipo,
    descricao=None,
    telefone=None,
    endereco=None,
    profissao=None,
    caminho_foto=None,
    data_nascimento=None
):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        preparar_colunas_usuario(cursor)
        garantir_tabela_endereco(cursor)

        email = normalizar_email(email)
        telefone = normalizar_telefone(telefone)

        if email_ja_cadastrado(cursor, email):
            raise EmailDuplicadoError("E-mail já cadastrado.")

        if telefone_ja_cadastrado(cursor, telefone):
            raise TelefoneDuplicadoError("Telefone já cadastrado.")

        senha_hash = hash_senha(senha)
        cidade = endereco.get("cidade") if endereco else None
        estado = endereco.get("estado") if endereco else None

        colunas = [
            "nome",
            "email",
            "senha",
            "tipo_usuario",
            "telefone",
            "foto_perfil",
            "cidade",
            "estado",
            "data_nascimento"
        ]
        valores = [
            nome,
            email,
            senha_hash,
            tipo,
            telefone,
            caminho_foto,
            cidade,
            estado,
            data_nascimento
        ]

        placeholders = ", ".join(["?"] * len(colunas))
        colunas_sql = ", ".join([f'"{coluna}"' for coluna in colunas])

        cursor.execute(f"""
            INSERT INTO usuarios ({colunas_sql})
            VALUES ({placeholders})
        """, valores)

        user_id = cursor.lastrowid

        if endereco:
            cursor.execute("""
                INSERT INTO enderecos_usuario (
                    usuario_id, rua, numero, cep, bairro, complemento, ponto_referencia
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                endereco.get("rua"),
                endereco.get("numero"),
                endereco.get("cep"),
                endereco.get("bairro"),
                endereco.get("complemento"),
                endereco.get("ponto_referencia")
            ))

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

        if tipo == "contratado":
            cursor.execute("""
                INSERT INTO perfis_trabalhador (usuario_id, profissao, descricao)
                VALUES (?, ?, ?)
            """, (user_id, profissao, descricao))

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def criar_admin(email, senha, nome="Administrador"):
    """Cria um usuário admin com permissões totais"""
    conn = get_connection()
    cursor = conn.cursor()

    senha_hash = hash_senha(senha)

    cursor.execute("""
    INSERT INTO usuarios (nome, email, senha, tipo_usuario)
    VALUES (?, ?, ?, 'admin')
    """, (nome, email, senha_hash))

    user_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return user_id

def login_usuario(email, senha):
    conn = get_connection()
    cursor = conn.cursor()
    preparar_colunas_usuario(cursor)

    cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
    user = cursor.fetchone()

    if user and verificar_senha(senha, user["senha"]):
        token = gerar_token(user["id_usuario"], user["tipo_usuario"])
        return {
            "token": token,
            "id": user["id_usuario"],
            "tipo": user["tipo_usuario"],
            "nome": user["nome"]
        }

    return None

def login_admin(email, senha):
    conn = get_connection()
    cursor = conn.cursor()
    preparar_colunas_usuario(cursor)

    cursor.execute("""
    SELECT * FROM usuarios WHERE email = ? AND tipo_usuario = 'admin'
    """, (email,))

    admin = cursor.fetchone()

    if admin and verificar_senha(senha, admin["senha"]):
        token = gerar_token(admin["id_usuario"], "admin")

        return {
            "token": token,
            "id": admin["id_usuario"],
            "tipo": "admin",
            "nome": admin["nome"]
        }

    return None
