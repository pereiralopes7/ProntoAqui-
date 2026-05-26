import sqlite3
import os

# Caminho absoluto do banco de dados
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "app_servicos_pro.db")

conn = sqlite3.connect(db_path)
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()

# Criar tabela conversas se não existir
cursor.execute("""
CREATE TABLE IF NOT EXISTS conversas (
    id_conversa INTEGER PRIMARY KEY AUTOINCREMENT,
    id_solicitacao INTEGER,
    FOREIGN KEY(id_solicitacao) REFERENCES servicos(id)
)
""")

# Criar tabela mensagens se não existir
cursor.execute("""
CREATE TABLE IF NOT EXISTS mensagens (
    id_mensagem INTEGER PRIMARY KEY AUTOINCREMENT,
    id_conversa INTEGER,
    id_remetente INTEGER,
    conteudo TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(id_conversa) REFERENCES conversas(id_conversa),
    FOREIGN KEY(id_remetente) REFERENCES usuarios(id_usuario)
)
""")

conn.commit()
conn.close()

print("Tabelas 'conversas' e 'mensagens' criadas ou já existem.")