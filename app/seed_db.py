import sqlite3
from pathlib import Path
from html import escape

# Usar o mesmo caminho que connection.py
DB_FILENAME = "app_servicos_pro.db"
project_root = Path(__file__).resolve().parent.parent
db_path = project_root / DB_FILENAME
uploads_dir = project_root / "uploads"


def iniciais(nome):
    partes = [parte for parte in (nome or "").split() if parte]

    if not partes:
        return "PA"

    return "".join(parte[0].upper() for parte in partes[:2])


def criar_avatar_exemplo(caminho, nome, profissao, indice):
    paleta = [
        ("#f2c94c", "#6c5ce7"),
        ("#00b894", "#2d3436"),
        ("#0984e3", "#fdcb6e"),
        ("#a29bfe", "#2d3436"),
        ("#e17055", "#ffffff"),
        ("#00cec9", "#2d3436"),
    ]
    cor, cor_secundaria = paleta[indice % len(paleta)]
    texto = escape(iniciais(nome))
    profissao = escape(profissao or "Profissional")
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{cor}"/>
      <stop offset="1" stop-color="{cor_secundaria}"/>
    </linearGradient>
  </defs>
  <rect width="512" height="512" rx="96" fill="url(#bg)"/>
  <circle cx="256" cy="196" r="86" fill="rgba(255,255,255,0.88)"/>
  <path d="M104 438c22-94 84-142 152-142s130 48 152 142" fill="rgba(255,255,255,0.88)"/>
  <text x="256" y="224" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="70" font-weight="700" fill="#222">{texto}</text>
  <text x="256" y="472" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="30" font-weight="700" fill="rgba(255,255,255,0.95)">{profissao}</text>
</svg>
"""
    caminho.write_text(svg, encoding="utf-8")

print(f"[SEED_DB] Conectando ao banco: {db_path}")

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Dados de teste para prestadores
prestadores_data = [
    # Pedreiro
    {
        "nome": "Carlos Silva",
        "email": "carlos.pedreiro@email.com",
        "senha": "123456",
        "cidade": "São Paulo",
        "data_nascimento": "1979-05-15",
        "profissao": "Pedreiro",
        "descricao": "Execução de obras, reformas e alvenaria"
    },
    {
        "nome": "Roberto Mendes",
        "email": "roberto.pedreiro@email.com",
        "senha": "123456",
        "cidade": "Campinas",
        "data_nascimento": "1981-09-22",
        "profissao": "Pedreiro",
        "descricao": "Construção e reparos estruturais"
    },
    # Encanador
    {
        "nome": "João Santos",
        "email": "joao.encanador@email.com",
        "senha": "123456",
        "cidade": "Campinas",
        "data_nascimento": "1985-03-22",
        "profissao": "Encanador",
        "descricao": "Instalação e manutenção hidráulica"
    },
    {
        "nome": "Ricardo Lima",
        "email": "ricardo.encanador@email.com",
        "senha": "123456",
        "cidade": "São Paulo",
        "data_nascimento": "1978-11-14",
        "profissao": "Encanador",
        "descricao": "Desentupimentos e reparos"
    },
    # Eletricista
    {
        "nome": "Maria Oliveira",
        "email": "maria.eletricista@email.com",
        "senha": "123456",
        "cidade": "São Paulo",
        "data_nascimento": "1982-11-10",
        "profissao": "Eletricista",
        "descricao": "Instalações e manutenção elétrica residencial"
    },
    {
        "nome": "Fernanda Costa",
        "email": "fernanda.eletricista@email.com",
        "senha": "123456",
        "cidade": "Rio de Janeiro",
        "data_nascimento": "1989-06-05",
        "profissao": "Eletricista",
        "descricao": "Manutenção elétrica comercial"
    },
    # Diarista
    {
        "nome": "Ana Costa",
        "email": "ana.diarista@email.com",
        "senha": "123456",
        "cidade": "São Paulo",
        "data_nascimento": "1990-07-08",
        "profissao": "Diarista",
        "descricao": "Limpeza e arrumação residencial"
    },
    {
        "nome": "Juliana Pereira",
        "email": "juliana.diarista@email.com",
        "senha": "123456",
        "cidade": "Campinas",
        "data_nascimento": "1992-12-18",
        "profissao": "Diarista",
        "descricao": "Serviços domésticos completos"
    },
    # Jardineiro
    {
        "nome": "Paulo Rodrigues",
        "email": "paulo.jardineiro@email.com",
        "senha": "123456",
        "cidade": "São Paulo",
        "data_nascimento": "1980-04-30",
        "profissao": "Jardineiro",
        "descricao": "Jardinagem e paisagismo"
    },
    {
        "nome": "Gabriel Souza",
        "email": "gabriel.jardineiro@email.com",
        "senha": "123456",
        "cidade": "Rio de Janeiro",
        "data_nascimento": "1987-08-12",
        "profissao": "Jardineiro",
        "descricao": "Manutenção de plantas e poda"
    },
    # Pintor
    {
        "nome": "Pedro Pereira",
        "email": "pedro.pintor@email.com",
        "senha": "123456",
        "cidade": "Campinas",
        "data_nascimento": "1988-12-03",
        "profissao": "Pintor",
        "descricao": "Pintura residencial e comercial"
    },
    {
        "nome": "Thiago Alves",
        "email": "thiago.pintor@email.com",
        "senha": "123456",
        "cidade": "São Paulo",
        "data_nascimento": "1984-02-25",
        "profissao": "Pintor",
        "descricao": "Retoque e pintura completa"
    },
    # Marceneiro
    {
        "nome": "Roberto Ferreira",
        "email": "roberto.marceneiro@email.com",
        "senha": "123456",
        "cidade": "Rio de Janeiro",
        "data_nascimento": "1975-08-20",
        "profissao": "Marceneiro",
        "descricao": "Móveis sob medida e reparos"
    },
    {
        "nome": "Fernanda Lima",
        "email": "fernanda.marceneiro@email.com",
        "senha": "123456",
        "cidade": "Belo Horizonte",
        "data_nascimento": "1987-04-12",
        "profissao": "Marceneiro",
        "descricao": "Construção de armários e portas"
    },
    # Mecânico
    {
        "nome": "Lucas Almeida",
        "email": "lucas.mecanico@email.com",
        "senha": "123456",
        "cidade": "São Paulo",
        "data_nascimento": "1983-09-17",
        "profissao": "Mecânico",
        "descricao": "Manutenção e reparo de automóveis"
    },
    {
        "nome": "Diego Carvalho",
        "email": "diego.mecanico@email.com",
        "senha": "123456",
        "cidade": "Campinas",
        "data_nascimento": "1991-01-09",
        "profissao": "Mecânico",
        "descricao": "Serviços de mecânica geral"
    },
    # Técnico de informática
    {
        "nome": "Bruno Santos",
        "email": "bruno.tecnico@email.com",
        "senha": "123456",
        "cidade": "São Paulo",
        "data_nascimento": "1986-05-14",
        "profissao": "Técnico de informática",
        "descricao": "Suporte técnico e manutenção"
    },
    {
        "nome": "Carla Oliveira",
        "email": "carla.tecnico@email.com",
        "senha": "123456",
        "cidade": "Rio de Janeiro",
        "data_nascimento": "1993-10-28",
        "profissao": "Técnico de informática",
        "descricao": "Consultoria em TI"
    },
    # Babá
    {
        "nome": "Patrícia Rodrigues",
        "email": "patricia.baba@email.com",
        "senha": "123456",
        "cidade": "São Paulo",
        "data_nascimento": "1988-03-07",
        "profissao": "Babá",
        "descricao": "Cuidado infantil responsável"
    },
    {
        "nome": "Sofia Mendes",
        "email": "sofia.baba@email.com",
        "senha": "123456",
        "cidade": "Campinas",
        "data_nascimento": "1995-07-19",
        "profissao": "Babá",
        "descricao": "Educação e diversão infantil"
    },
    # Cuidador de idosos
    {
        "nome": "José Ferreira",
        "email": "jose.cuidador@email.com",
        "senha": "123456",
        "cidade": "São Paulo",
        "data_nascimento": "1979-12-01",
        "profissao": "Cuidador de idosos",
        "descricao": "Atenção 24h com experiência"
    },
    {
        "nome": "Mariana Lima",
        "email": "mariana.cuidador@email.com",
        "senha": "123456",
        "cidade": "Rio de Janeiro",
        "data_nascimento": "1984-06-23",
        "profissao": "Cuidador de idosos",
        "descricao": "Cuidado especializado"
    },
    # Personal trainer
    {
        "nome": "Rafael Costa",
        "email": "rafael.trainer@email.com",
        "senha": "123456",
        "cidade": "São Paulo",
        "data_nascimento": "1982-09-11",
        "profissao": "Personal trainer",
        "descricao": "Treinamento personalizado"
    },
    {
        "nome": "Amanda Pereira",
        "email": "amanda.trainer@email.com",
        "senha": "123456",
        "cidade": "Campinas",
        "data_nascimento": "1990-11-04",
        "profissao": "Personal trainer",
        "descricao": "Fitness e emagrecimento"
    },
    # Professor particular
    {
        "nome": "Eduardo Souza",
        "email": "eduardo.professor@email.com",
        "senha": "123456",
        "cidade": "São Paulo",
        "data_nascimento": "1985-01-16",
        "profissao": "Professor particular",
        "descricao": "Aulas de matemática e português"
    },
    {
        "nome": "Larissa Alves",
        "email": "larissa.professor@email.com",
        "senha": "123456",
        "cidade": "Rio de Janeiro",
        "data_nascimento": "1992-04-08",
        "profissao": "Professor particular",
        "descricao": "Aulas de inglês"
    },
    # Chaveiro
    {
        "nome": "Vinícius Mendes",
        "email": "vinicius.chaveiro@email.com",
        "senha": "123456",
        "cidade": "São Paulo",
        "data_nascimento": "1987-07-30",
        "profissao": "Chaveiro",
        "descricao": "Abertura de portas 24h"
    },
    {
        "nome": "Isabela Carvalho",
        "email": "isabela.chaveiro@email.com",
        "senha": "123456",
        "cidade": "Campinas",
        "data_nascimento": "1994-02-14",
        "profissao": "Chaveiro",
        "descricao": "Cópias de chaves diversas"
    },
    # Ar-condicionado
    {
        "nome": "Gustavo Rodrigues",
        "email": "gustavo.ar@email.com",
        "senha": "123456",
        "cidade": "São Paulo",
        "data_nascimento": "1980-10-05",
        "profissao": "Ar-condicionado",
        "descricao": "Instalação e manutenção"
    },
    {
        "nome": "Camila Santos",
        "email": "camila.ar@email.com",
        "senha": "123456",
        "cidade": "Rio de Janeiro",
        "data_nascimento": "1989-12-27",
        "profissao": "Ar-condicionado",
        "descricao": "Limpeza e revisão de AC"
    }
]

# Usar os prestadores demo profissionais na apresentação.
from app.atualizar_prestadores_demo import PRESTADORES_DEMO

prestadores_data = [
    {
        "nome": prestador["nome"],
        "email": prestador["email"],
        "senha": "123456",
        "cidade": prestador["cidade"],
        "data_nascimento": "1990-01-01",
        "profissao": prestador["profissao"],
        "descricao": prestador["descricao"],
        "foto": prestador["foto"],
    }
    for prestador in PRESTADORES_DEMO
]

# Inserir dados
uploads_dir.mkdir(parents=True, exist_ok=True)

for indice, data in enumerate(prestadores_data, start=1):
    try:
        foto_perfil = data.get("foto")
        if foto_perfil:
            criar_avatar_exemplo(
                project_root / foto_perfil,
                data["nome"],
                data["profissao"],
                indice,
            )

        # Inserir na tabela usuarios
        cursor.execute("""
        INSERT INTO usuarios (nome, email, senha, tipo_usuario, cidade, data_nascimento, foto_perfil)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data["nome"],
            data["email"],
            data["senha"],
            "contratado",
            data["cidade"],
            data["data_nascimento"],
            foto_perfil,
        ))
        
        # Pegar o id_usuario gerado
        usuario_id = cursor.lastrowid
        
        # Inserir na tabela perfis_trabalhador com profissao CORRETAMENTE
        cursor.execute("""
        INSERT INTO perfis_trabalhador (usuario_id, profissao, descricao)
        VALUES (?, ?, ?)
        """, (usuario_id, data["profissao"], data["descricao"]))
    except sqlite3.IntegrityError as e:
        print(f"[SEED_DB] Erro ao inserir {data['nome']}: {e}")

conn.commit()
conn.close()

print(f"[SEED_DB] {len(prestadores_data)} profissionais inseridos com sucesso!")
