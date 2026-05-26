from datetime import datetime
import unicodedata

from app.database.connection import get_connection
from app.utils.geo import calcular_distancia


def normalize_text(text):
    if not text:
        return ""

    nfkd_form = unicodedata.normalize("NFKD", text)

    return "".join([
        c for c in nfkd_form
        if not unicodedata.combining(c)
    ]).lower()


def buscar_trabalhadores_proximos(lat, lon, raio_km=10):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            u.id_usuario,
            u.nome,
            u.latitude,
            u.longitude,
            p.descricao
        FROM usuarios u
        JOIN perfis_trabalhador p ON u.id_usuario = p.usuario_id
        WHERE u.tipo_usuario IN ('contratado', 'prestador')
    """)

    usuarios = cursor.fetchall()
    proximos = []

    for u in usuarios:
        if u["latitude"] and u["longitude"]:
            distancia = calcular_distancia(
                lat,
                lon,
                u["latitude"],
                u["longitude"]
            )

            if distancia <= raio_km:
                proximos.append({
                    "id": u["id_usuario"],
                    "nome": u["nome"],
                    "descricao": u["descricao"] or "",
                    "distancia": round(distancia, 2)
                })

    conn.close()

    return proximos


def buscar_profissionais_por_texto(texto):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            u.id_usuario,
            u.nome,
            u.cidade,
            p.profissao,
            p.descricao,
            u.data_nascimento,
            u.data_criacao
        FROM usuarios u
        JOIN perfis_trabalhador p ON u.id_usuario = p.usuario_id
        WHERE 
            u.tipo_usuario IN ('contratado', 'prestador')
            AND (
            u.nome LIKE ?
            OR p.descricao LIKE ?
            OR p.profissao LIKE ?
            )
    """, (
        f"%{texto}%",
        f"%{texto}%",
        f"%{texto}%"
    ))

    usuarios = cursor.fetchall()
    resultados = []

    for u in usuarios:
        idade = None

        try:
            data_nasc = u["data_nascimento"]

            if data_nasc:
                data_nasc = datetime.fromisoformat(data_nasc)
                idade = datetime.now().year - data_nasc.year
        except Exception:
            idade = None

        resultados.append({
            "id": u["id_usuario"],
            "nome": u["nome"],
            "cidade": u["cidade"] or "Não informado",
            "idade": idade,
            "profissao": u["profissao"] or u["descricao"] or "Não informado",
            "descricao": u["descricao"] or ""
        })

    conn.close()

    return resultados


def buscar_profissionais(query):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            u.id_usuario,
            u.nome,
            u.cidade,
            p.profissao,
            p.descricao
        FROM usuarios u
        JOIN perfis_trabalhador p ON u.id_usuario = p.usuario_id
        WHERE 
            u.tipo_usuario IN ('contratado', 'prestador')
            AND (
            u.nome LIKE ?
            OR p.descricao LIKE ?
            OR u.cidade LIKE ?
            OR p.profissao LIKE ?
            )
    """, (
        f"%{query}%",
        f"%{query}%",
        f"%{query}%",
        f"%{query}%"
    ))

    rows = cursor.fetchall()
    resultados = []

    for row in rows:
        resultados.append({
            "id": row["id_usuario"],
            "nome": row["nome"],
            "profissao": row["profissao"] or "Não informado",
            "cidade": row["cidade"] or "Não informado",
            "descricao": row["descricao"] or ""
        })

    conn.close()

    return resultados


def buscar_profissionais_com_join(query):
    conn = get_connection()
    cursor = conn.cursor()

    normalized_query = normalize_text(query)

    cursor.execute("""
        SELECT 
            u.id_usuario,
            u.nome,
            u.cidade,
            p.profissao,
            p.descricao
        FROM usuarios u
        JOIN perfis_trabalhador p ON u.id_usuario = p.usuario_id
        WHERE u.tipo_usuario IN ('contratado', 'prestador')
    """)

    rows = cursor.fetchall()
    resultados = []

    for row in rows:
        nome_norm = normalize_text(row["nome"])
        profissao_norm = normalize_text(row["profissao"] or "")
        descricao_norm = normalize_text(row["descricao"] or "")
        cidade_norm = normalize_text(row["cidade"] or "")

        if (
            normalized_query in nome_norm
            or normalized_query in profissao_norm
            or normalized_query in descricao_norm
            or normalized_query in cidade_norm
        ):
            resultados.append({
                "id": row["id_usuario"],
                "nome": row["nome"],
                "cidade": row["cidade"] or "Não informado",
                "profissao": row["profissao"] or row["descricao"] or "Não informado",
                "descricao": row["descricao"] or ""
            })

    conn.close()

    return resultados
