from flask import Blueprint, request, jsonify
from app.database.connection import get_connection

admin_bp = Blueprint("admin_bp", __name__)

@admin_bp.route("/test", methods=["GET"])
def test_admin():
    """Rota de teste para verificar se o admin está funcionando"""
    return jsonify({"message": "Admin routes working!", "status": "ok"})

@admin_bp.route("/usuarios", methods=["GET"])
def get_usuarios():
    """Lista todos os usuários (apenas para admin)"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id, nome, email, tipo_usuario, data_criacao
            FROM usuarios
            ORDER BY data_criacao DESC
        """)
        usuarios = cursor.fetchall()

        return jsonify([dict(row) for row in usuarios])

    except Exception as e:
        return jsonify({"erro": str(e)}), 500
    finally:
        conn.close()

@admin_bp.route("/servicos", methods=["GET"])
def get_servicos_admin():
    """Lista todos os serviços (apenas para admin)"""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT s.*, u.nome as contratante_nome
            FROM servicos s
            LEFT JOIN usuarios u ON s.contratante_id = u.id
            ORDER BY s.id DESC
        """)
        servicos = cursor.fetchall()

        # Debug: verificar se há dados
        print(f"Serviços encontrados: {len(servicos)}")
        for servico in servicos:
            print(f"Serviço: {dict(servico)}")

        return jsonify([dict(row) for row in servicos])

    except Exception as e:
        print(f"Erro na rota /servicos: {str(e)}")
        return jsonify({"erro": str(e)}), 500
    finally:
        if 'conn' in locals():
            conn.close()

@admin_bp.route("/stats", methods=["GET"])
def get_admin_stats():
    """Retorna estatísticas para o dashboard admin"""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Total de usuários por tipo
        cursor.execute("""
            SELECT tipo_usuario, COUNT(*) as total
            FROM usuarios
            GROUP BY tipo_usuario
        """)
        usuarios_por_tipo = cursor.fetchall()
        usuarios_dict = {row[0]: row[1] for row in usuarios_por_tipo}
        total_usuarios = sum(usuarios_dict.values())

        # Total de serviços
        cursor.execute("SELECT COUNT(*) FROM servicos")
        total_servicos = cursor.fetchone()[0]

        # Total de propostas (contratos)
        cursor.execute("SELECT COUNT(*) FROM propostas")
        total_contratos = cursor.fetchone()[0]

        # Total de pagamentos (se existir tabela pagamentos)
        # Por enquanto, vamos usar 0
        total_pagamentos = 0

        return jsonify({
            "usuarios": {
                "total": total_usuarios,
                "cliente": usuarios_dict.get('cliente', 0),
                "contratado": usuarios_dict.get('contratado', 0),
                "admin": usuarios_dict.get('admin', 0)
            },
            "servicos": total_servicos,
            "contratos": total_contratos,
            "pagamentos": total_pagamentos
        })

    except Exception as e:
        print(f"Erro na rota /stats: {str(e)}")
        return jsonify({"erro": str(e)}), 500
    finally:
        if 'conn' in locals():
            conn.close()