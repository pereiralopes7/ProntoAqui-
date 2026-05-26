from app.database.connection import get_connection


def garantir_colunas_pagamentos(cursor):
    cursor.execute("PRAGMA table_info(pagamentos)")
    colunas = {row["name"] for row in cursor.fetchall()}

    if "pagador_id" not in colunas:
        cursor.execute("ALTER TABLE pagamentos ADD COLUMN pagador_id INTEGER")

    if "recebedor_id" not in colunas:
        cursor.execute("ALTER TABLE pagamentos ADD COLUMN recebedor_id INTEGER")


def criar_pagamento(servico_id, pagador, recebedor, valor, metodo):
    conn = get_connection()
    cursor = conn.cursor()
    garantir_colunas_pagamentos(cursor)

    cursor.execute("""
    INSERT INTO pagamentos (servico_id, pagador_id, recebedor_id, valor, metodo)
    VALUES (?, ?, ?, ?, ?)
    """, (servico_id, pagador, recebedor, valor, metodo))

    conn.commit()
    conn.close()
