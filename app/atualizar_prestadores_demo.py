import argparse

from app.database.connection import get_connection


PRESTADORES_DEMO = [
    {
        "email": "teste.prestador.1779802797@email.com",
        "nome": "Lucas",
        "profissao": "Técnico de informática",
        "cidade": "Campinas",
        "descricao": "Manutenção de computadores, instalação de programas e suporte técnico.",
        "foto": None,
    },
    {
        "email": "perfil.contratado.1779803666.False@email.com",
        "nome": "Rafael",
        "profissao": "Eletricista",
        "cidade": "São Paulo",
        "descricao": "Instalações elétricas residenciais, troca de tomadas e manutenção preventiva.",
        "foto": None,
    },
    {
        "email": "perfil.publico.1779804216@email.com",
        "nome": "Bruno",
        "profissao": "Pintor",
        "cidade": "Indaiatuba",
        "descricao": "Pintura residencial, acabamento em paredes e pequenos reparos.",
        "foto": None,
    },
    {
        "email": "prestador.1779804883@email.com",
        "nome": "Marcos",
        "profissao": "Encanador",
        "cidade": "Campinas",
        "descricao": "Conserto de vazamentos, troca de torneiras e instalação hidráulica.",
        "foto": None,
    },
    {
        "email": "data.perfil.1779805972@email.com",
        "nome": "Felipe",
        "profissao": "Jardineiro",
        "cidade": "São Paulo",
        "descricao": "Manutenção de jardins, poda de plantas e limpeza de áreas externas.",
        "foto": None,
    },
    {
        "email": "chat.provider.1779806692@email.com",
        "nome": "André",
        "profissao": "Marceneiro",
        "cidade": "Campinas",
        "descricao": "Montagem de móveis, ajustes em portas e pequenos reparos em madeira.",
        "foto": None,
    },
]


def buscar_usuarios(conn):
    emails = [prestador["email"] for prestador in PRESTADORES_DEMO]
    placeholders = ",".join("?" for _ in emails)
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT
            u.id_usuario,
            u.nome,
            u.email,
            u.tipo_usuario,
            u.cidade,
            u.foto_perfil,
            p.profissao,
            p.descricao
        FROM usuarios u
        LEFT JOIN perfis_trabalhador p ON p.usuario_id = u.id_usuario
        WHERE u.email IN ({placeholders})
        ORDER BY u.id_usuario
        """,
        emails,
    )
    return cursor.fetchall()


def main():
    parser = argparse.ArgumentParser(
        description="Atualiza somente os prestadores demo/laranjas usados na apresentação."
    )
    parser.add_argument("--apply", action="store_true", help="Aplica as alterações no banco.")
    args = parser.parse_args()

    conn = get_connection()
    usuarios = buscar_usuarios(conn)
    demo_por_email = {prestador["email"]: prestador for prestador in PRESTADORES_DEMO}

    print("Prestadores demo encontrados para atualização:")

    for usuario in usuarios:
        novo = demo_por_email[usuario["email"]]
        print(
            f"- id={usuario['id_usuario']} | nome atual={usuario['nome']} | "
            f"email={usuario['email']} | tipo={usuario['tipo_usuario']} | "
            f"profissão atual={usuario['profissao']} | foto atual={usuario['foto_perfil']} | "
            f"novo nome={novo['nome']} | nova profissão={novo['profissao']} | "
            "nova foto=None (usa foto padrão)"
        )

    bloqueados = [
        usuario for usuario in usuarios
        if usuario["tipo_usuario"] not in ("contratado", "prestador")
    ]

    if bloqueados:
        print("Nenhum usuário foi alterado: a lista contém usuário que não é prestador.")
        conn.close()
        return

    if not args.apply:
        print("Modo simulação: rode novamente com --apply para aplicar.")
        conn.close()
        return

    cursor = conn.cursor()

    for usuario in usuarios:
        novo = demo_por_email[usuario["email"]]

        cursor.execute(
            """
            UPDATE usuarios
            SET nome = ?, cidade = ?, foto_perfil = NULL
            WHERE id_usuario = ?
              AND email = ?
              AND tipo_usuario IN ('contratado', 'prestador')
            """,
            (
                novo["nome"],
                novo["cidade"],
                usuario["id_usuario"],
                usuario["email"],
            ),
        )
        cursor.execute(
            """
            UPDATE perfis_trabalhador
            SET profissao = ?, descricao = ?
            WHERE usuario_id = ?
            """,
            (novo["profissao"], novo["descricao"], usuario["id_usuario"]),
        )

    conn.commit()
    conn.close()
    print(f"{len(usuarios)} prestadores demo atualizados com sucesso.")


if __name__ == "__main__":
    main()
