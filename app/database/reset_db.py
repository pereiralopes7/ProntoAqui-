import sqlite3
from pathlib import Path

# Usar o mesmo caminho que connection.py
DB_FILENAME = "app_servicos_pro.db"
project_root = Path(__file__).resolve().parent.parent
db_path = project_root / DB_FILENAME

print(f"[RESET_DB] Caminho do banco: {db_path}")

# Garantir que o diretório existe
db_path.parent.mkdir(parents=True, exist_ok=True)

# Apagar o banco se existir
if db_path.exists():
    db_path.unlink()
    print(f"[RESET_DB] Banco anterior removido.")

# Executar o setup para recriar as tabelas
conn = sqlite3.connect(str(db_path))
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
# ENDEREÇOS DOS USUÁRIOS
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
# PERFIL TRABALHADOR
# =========================
cursor.execute("""
CREATE TABLE IF NOT EXISTS perfis_trabalhador (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER UNIQUE,
    profissao varchar(120),
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

# Garante que a coluna profissao exista
cursor.execute("PRAGMA table_info(perfis_trabalhador)")
columns = [row[1] for row in cursor.fetchall()]
if "profissao" not in columns:
    cursor.execute("ALTER TABLE perfis_trabalhador ADD COLUMN profissao TEXT")

conn.commit()
print("[RESET_DB] Tabelas criadas com sucesso!")

# =========================
# SERVIÇOS
# =========================
cursor.execute("""
CREATE TABLE IF NOT EXISTS servicos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contratante_id INTEGER,
    prestador_id INTEGER,
    descricao TEXT,
    valor REAL,
    status TEXT DEFAULT 'pendente',
    data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
    data_conclusao DATETIME,
    FOREIGN KEY(contratante_id) REFERENCES usuarios(id_usuario),
    FOREIGN KEY(prestador_id) REFERENCES usuarios(id_usuario)
)
""")

# =========================
# CHAT
# =========================
cursor.execute("""
CREATE TABLE IF NOT EXISTS chat (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    servico_id INTEGER,
    remetente_id INTEGER,
    destinatario_id INTEGER,
    mensagem TEXT,
    data_envio DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(servico_id) REFERENCES servicos(id),
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
    valor REAL,
    metodo TEXT,
    status TEXT DEFAULT 'pendente',
    data_pagamento DATETIME,
    FOREIGN KEY(servico_id) REFERENCES servicos(id)
)
""")

# =========================
# EMAIL DE CONFIRMAÇÃO
# =========================
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
conn.close()

print("Banco de dados recriado com sucesso!")
