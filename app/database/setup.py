import os
import sqlite3

# Caminho do banco de dados dentro da pasta app
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app_servicos_pro.db")
DB_PATH = os.path.abspath(DB_PATH)

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()

# =========================
# USUÁRIOS
# =========================
cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
    nome char(70) NOT NULL,
    email char(50) UNIQUE NOT NULL,
    senha char(20) NOT NULL,
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



# =========================
# PERFIL ADMIN
# =========================
cursor.execute("""
CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER UNIQUE,
    email char(50) UNIQUE NOT NULL,
    senha varchar(20) NOT NULL,
    nivel_acesso TEXT DEFAULT 'total',
    ativo INTEGER DEFAULT 1,
    data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(usuario_id) REFERENCES usuarios(id_usuario) ON DELETE CASCADE
)
""")

# =========================
# ENDERECOS DOS USUARIOS
# =========================
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

# =========================
# PERFIL TRABALHADOR
# =========================
cursor.execute("""
CREATE TABLE IF NOT EXISTS perfis_trabalhador (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER UNIQUE,
    descricao varchar(400),
    experiencia varchar(400),
    formacao varchar(400),
    certificados TEXT,
    avaliacao_media REAL DEFAULT 0,
    total_avaliacoes INTEGER DEFAULT 0,
    ranking_score REAL DEFAULT 0,
    FOREIGN KEY(usuario_id) REFERENCES usuarios(id_usuario)
)
""")

# =========================
# SERVIÇOS
# =========================
cursor.execute("""
CREATE TABLE IF NOT EXISTS servicos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contratante_id INTEGER,
    titulo varchar(20),
    descricao varchar(400),
    cidade varchar(20),
    estado varchar(20),
    latitude REAL,
    longitude REAL,
    status TEXT DEFAULT 'aberto',
    FOREIGN KEY(contratante_id) REFERENCES usuarios(id_usuario)
)
""")

# =========================
# PROPOSTAS
# =========================
cursor.execute("""
CREATE TABLE IF NOT EXISTS propostas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    servico_id INTEGER,
    trabalhador_id INTEGER,
    valor REAL,
    status varchar(100) DEFAULT 'enviada',
    FOREIGN KEY(servico_id) REFERENCES servicos(id),
    FOREIGN KEY(trabalhador_id) REFERENCES usuarios(id_usuario)
)
""")

# =========================
# MENSAGENS
# =========================
cursor.execute("""
CREATE TABLE IF NOT EXISTS mensagens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    remetente_id INTEGER,
    destinatario_id INTEGER,
    mensagem varchar(500),
    imagem TEXT,
    data DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(remetente_id) REFERENCES usuarios(id_usuario),
    FOREIGN KEY(destinatario_id) REFERENCES usuarios(id_usuario)
)
""")

# =========================
# PAGAMENTOS
# =========================
cursor.execute("""
CREATE TABLE IF NOT EXISTS pagamentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    servico_id INTEGER,
    pagador_id INTEGER,
    recebedor_id INTEGER,
    valor REAL,
    metodo TEXT,
    status varchar(100) DEFAULT 'pendente',
    data DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(servico_id) REFERENCES servicos(id),
    FOREIGN KEY(pagador_id) REFERENCES usuarios(id_usuario),
    FOREIGN KEY(recebedor_id) REFERENCES usuarios(id_usuario)
)
""")

# =========================
# DENÚNCIAS
# =========================
cursor.execute("""
CREATE TABLE IF NOT EXISTS denuncias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    denunciante_id INTEGER,
    denunciado_id INTEGER,
    motivo varchar(300),
    descricao varchar(300),
    status varchar(100) DEFAULT 'pendente',
    data DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(denunciante_id) REFERENCES usuarios(id_usuario),
    FOREIGN KEY(denunciado_id) REFERENCES usuarios(id_usuario)
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS codigos_verificacao (
    id_codigo INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    codigo TEXT NOT NULL,
    expiracao DATETIME NOT NULL,
    verificado INTEGER DEFAULT 0
)
""")

conn.commit()

cursor.execute("PRAGMA table_info(usuarios)")
colunas_usuarios = [coluna[1] for coluna in cursor.fetchall()]

if "tipo_usuario" not in colunas_usuarios:
    cursor.execute("ALTER TABLE usuarios ADD COLUMN tipo_usuario TEXT DEFAULT 'contratante'")

if "foto_posicao_y" not in colunas_usuarios:
    cursor.execute("ALTER TABLE usuarios ADD COLUMN foto_posicao_y INTEGER DEFAULT 50")

if "foto_posicao_x" not in colunas_usuarios:
    cursor.execute("ALTER TABLE usuarios ADD COLUMN foto_posicao_x INTEGER DEFAULT 50")

conn.commit()
conn.close()

print("Banco criado com sucesso!")
