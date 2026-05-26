from app.database.connection import get_connection


def garantir_tabela_mensagens(cursor):
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mensagens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        remetente_id INTEGER NOT NULL,
        destinatario_id INTEGER NOT NULL,
        mensagem TEXT NOT NULL,
        imagem TEXT,
        data DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(remetente_id) REFERENCES usuarios(id_usuario),
        FOREIGN KEY(destinatario_id) REFERENCES usuarios(id_usuario)
    )
    """)


def buscar_mensagens(user1, user2):
    if not user1 or not user2:
        return []

    conn = get_connection()
    cursor = conn.cursor()
    garantir_tabela_mensagens(cursor)

    cursor.execute("""
    SELECT id, remetente_id, destinatario_id, mensagem, imagem, data
    FROM mensagens
    WHERE (remetente_id = ? AND destinatario_id = ?)
       OR (remetente_id = ? AND destinatario_id = ?)
    ORDER BY data
    """, (user1, user2, user2, user1))

    msgs = cursor.fetchall()
    conn.close()

    return [dict(m) for m in msgs]


def salvar_mensagem(remetente_id, destinatario_id, texto):
    texto = (texto or "").strip()

    if not texto:
        raise ValueError("Mensagem vazia")

    if int(remetente_id) == int(destinatario_id):
        raise ValueError("Nao e possivel enviar mensagem para si mesmo")

    conn = get_connection()
    cursor = conn.cursor()
    garantir_tabela_mensagens(cursor)

    cursor.execute("""
    INSERT INTO mensagens (remetente_id, destinatario_id, mensagem)
    VALUES (?, ?, ?)
    """, (remetente_id, destinatario_id, texto))

    mensagem_id = cursor.lastrowid
    conn.commit()

    cursor.execute("""
    SELECT id, remetente_id, destinatario_id, mensagem, imagem, data
    FROM mensagens
    WHERE id = ?
    """, (mensagem_id,))

    mensagem = dict(cursor.fetchone())
    conn.close()

    return mensagem
