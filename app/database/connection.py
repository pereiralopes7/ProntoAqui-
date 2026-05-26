import os
import sqlite3
from pathlib import Path

DB_FILENAME = "app_servicos_pro.db"


def get_database_path():
    """Retorna o caminho absoluto do arquivo SQLite na raiz do projeto."""
    # Caminho: /Users/.../prontoAqui-main 5/app_servicos_pro.db
    project_root = Path(__file__).resolve().parent.parent.parent
    db_path = project_root / DB_FILENAME
    return str(db_path)


def get_connection():
    """Retorna conexão com SQLite com row_factory configurado."""
    db_path = get_database_path()
    
    # Garantir que o diretório existe
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Conectar e configurar
    conn = sqlite3.connect(db_path, timeout=10)
    conn.row_factory = sqlite3.Row  # Permite acessar colunas por nome
    conn.execute("PRAGMA foreign_keys = ON")  # Ativar foreign keys
    
    return conn