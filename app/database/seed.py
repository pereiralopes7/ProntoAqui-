import sqlite3
import os
from datetime import datetime

# Caminho do banco dentro da pasta app
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app_servicos_pro.db")
DB_PATH = os.path.abspath(DB_PATH)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Inserir usuários de exemplo (nome, email, senha, cidade, profissao, idade)
usuarios = [
    # Existentes (idades aproximadas) - emails já existem, pular ou usar novos
    # Adicionar mais para Pedreiro
    ("José Santos", "jose@email.com", "123", "Curitiba", "Pedreiro", 45),
    ("Pedro Oliveira", "pedro@email.com", "123", "Porto Alegre", "Pedreiro", 38),
    ("Roberto Costa", "roberto@email.com", "123", "Recife", "Pedreiro", 50),
    ("Fernando Pereira", "fernando@email.com", "123", "Fortaleza", "Pedreiro", 33),
    
    # Encanador
    ("Lucas Almeida", "lucas@email.com", "123", "Brasília", "Encanador", 29),
    ("Gabriel Rodrigues", "gabriel@email.com", "123", "Manaus", "Encanador", 36),
    ("Rafael Souza", "rafael@email.com", "123", "Belém", "Encanador", 41),
    ("Thiago Lima", "thiago@email.com", "123", "Goiânia", "Encanador", 27),
    
    # Eletricista
    ("Bruno Carvalho", "bruno@email.com", "123", "Natal", "Eletricista", 32),
    ("Eduardo Fernandes", "eduardo@email.com", "123", "João Pessoa", "Eletricista", 39),
    ("Felipe Gomes", "felipe@email.com", "123", "Aracaju", "Eletricista", 44),
    ("Gustavo Barbosa", "gustavo@email.com", "123", "Maceió", "Eletricista", 31),
    
    # Diarista
    ("Carla Mendes", "carla@email.com", "123", "Florianópolis", "Diarista", 25),
    ("Daniela Rocha", "daniela@email.com", "123", "Vitória", "Diarista", 48),
    ("Elaine Nunes", "elaine@email.com", "123", "Campo Grande", "Diarista", 37),
    ("Fabiana Dias", "fabiana@email.com", "123", "Cuiabá", "Diarista", 34),
    
    # Jardineiro (nova, 5)
    ("Henrique Teixeira", "henrique@email.com", "123", "São Paulo", "Jardineiro", 40),
    ("Igor Martins", "igor@email.com", "123", "Rio de Janeiro", "Jardineiro", 26),
    ("Jorge Ribeiro", "jorge@email.com", "123", "Belo Horizonte", "Jardineiro", 43),
    ("Kleber Cardoso", "kleber@email.com", "123", "Salvador", "Jardineiro", 35),
    ("Leandro Pinto", "leandro@email.com", "123", "Curitiba", "Jardineiro", 29),
    
    # Pintor (nova, 5)
    ("Marcos Silva", "marcos2@email.com", "123", "Porto Alegre", "Pintor", 47),
    ("Nelson Oliveira", "nelson@email.com", "123", "Recife", "Pintor", 38),
    ("Otávio Costa", "otavio@email.com", "123", "Fortaleza", "Pintor", 33),
    ("Paulo Pereira", "paulo@email.com", "123", "Brasília", "Pintor", 41),
    ("Ricardo Almeida", "ricardo@email.com", "123", "Manaus", "Pintor", 30),
    
    # Marceneiro (nova, 5)
    ("Sergio Rodrigues", "sergio@email.com", "123", "Belém", "Marceneiro", 52),
    ("Tiago Souza", "tiago2@email.com", "123", "Goiânia", "Marceneiro", 36),
    ("Ulisses Lima", "ulisses@email.com", "123", "Natal", "Marceneiro", 28),
    ("Vinicius Carvalho", "vinicius@email.com", "123", "João Pessoa", "Marceneiro", 45),
    ("Wagner Fernandes", "wagner@email.com", "123", "Aracaju", "Marceneiro", 39),
    
    # Mecânico (nova, 5)
    ("Xavier Gomes", "xavier@email.com", "123", "Maceió", "Mecânico", 42),
    ("Yuri Barbosa", "yuri@email.com", "123", "Florianópolis", "Mecânico", 31),
    ("Zeca Mendes", "zeca@email.com", "123", "Vitória", "Mecânico", 37),
    ("Alberto Rocha", "alberto@email.com", "123", "Campo Grande", "Mecânico", 44),
    ("Bernardo Nunes", "bernardo@email.com", "123", "Cuiabá", "Mecânico", 29),
    
    # Técnico de informática (nova, 5)
    ("Caio Dias", "caio@email.com", "123", "São Paulo", "Técnico de informática", 27),
    ("Diego Teixeira", "diego@email.com", "123", "Rio de Janeiro", "Técnico de informática", 34),
    ("Ernesto Martins", "ernesto@email.com", "123", "Belo Horizonte", "Técnico de informática", 40),
    ("Fábio Ribeiro", "fabio@email.com", "123", "Salvador", "Técnico de informática", 32),
    ("Gilberto Cardoso", "gilberto@email.com", "123", "Curitiba", "Técnico de informática", 38),
    
    # Babá (nova, 5)
    ("Helena Pinto", "helena@email.com", "123", "Porto Alegre", "Babá", 35),
    ("Isabel Silva", "isabel@email.com", "123", "Recife", "Babá", 28),
    ("Júlia Oliveira", "julia@email.com", "123", "Fortaleza", "Babá", 41),
    ("Karla Costa", "karla@email.com", "123", "Brasília", "Babá", 33),
    ("Laura Pereira", "laura@email.com", "123", "Manaus", "Babá", 46),
    
    # Cuidador de idosos (nova, 5)
    ("Mônica Almeida", "monica@email.com", "123", "Belém", "Cuidador de idosos", 39),
    ("Natália Rodrigues", "natalia@email.com", "123", "Goiânia", "Cuidador de idosos", 42),
    ("Olívia Souza", "olivia@email.com", "123", "Natal", "Cuidador de idosos", 30),
    ("Patrícia Lima", "patricia@email.com", "123", "João Pessoa", "Cuidador de idosos", 48),
    ("Quitéria Carvalho", "quiteria@email.com", "123", "Aracaju", "Cuidador de idosos", 36),
    
    # Personal trainer (nova, 5)
    ("Rosa Fernandes", "rosa@email.com", "123", "Maceió", "Personal trainer", 29),
    ("Sônia Gomes", "sonia@email.com", "123", "Florianópolis", "Personal trainer", 35),
    ("Tânia Barbosa", "tania@email.com", "123", "Vitória", "Personal trainer", 32),
    ("Úrsula Mendes", "ursula@email.com", "123", "Campo Grande", "Personal trainer", 40),
    ("Valentina Rocha", "valentina@email.com", "123", "Cuiabá", "Personal trainer", 27),
    
    # Professor particular (nova, 5)
    ("Wanda Nunes", "wanda@email.com", "123", "São Paulo", "Professor particular", 45),
    ("Xênia Dias", "zenia@email.com", "123", "Rio de Janeiro", "Professor particular", 38),
    ("Yasmin Teixeira", "yasmin@email.com", "123", "Belo Horizonte", "Professor particular", 41),
    ("Zilda Martins", "zilda@email.com", "123", "Salvador", "Professor particular", 34),
    ("Adelaide Ribeiro", "adelaide@email.com", "123", "Curitiba", "Professor particular", 50),
    
    # Chaveiro (nova, 5)
    ("Beatriz Cardoso", "beatriz@email.com", "123", "Porto Alegre", "Chaveiro", 37),
    ("Cecília Pinto", "cecilia@email.com", "123", "Recife", "Chaveiro", 31),
    ("Débora Silva", "debora@email.com", "123", "Fortaleza", "Chaveiro", 43),
    ("Elisa Oliveira", "elisa@email.com", "123", "Brasília", "Chaveiro", 28),
    ("Francisca Costa", "francisca@email.com", "123", "Manaus", "Chaveiro", 46),
    
    # Ar-condicionado (nova, 5)
    ("Gabriela Pereira", "gabriela@email.com", "123", "Belém", "Ar-condicionado", 33),
    ("Heloísa Almeida", "heloisa@email.com", "123", "Goiânia", "Ar-condicionado", 39),
    ("Irene Rodrigues", "irene@email.com", "123", "Natal", "Ar-condicionado", 42),
    ("Joana Souza", "joana@email.com", "123", "João Pessoa", "Ar-condicionado", 30),
    ("Lúcia Lima", "lucia@email.com", "123", "Aracaju", "Ar-condicionado", 35),
]

for i, (nome, email, senha, cidade, profissao, idade) in enumerate(usuarios):
    email_unico = f"{email.split('@')[0]}{i+1}@{email.split('@')[1]}"
    # Calcular data_criacao para idade aproximada
    ano_nascimento = datetime.now().year - idade
    data_criacao = f"{ano_nascimento}-01-01 00:00:00"
    
    cursor.execute("INSERT INTO usuarios (nome, email, senha, cidade, data_criacao) VALUES (?, ?, ?, ?, ?)", 
                   (nome, email_unico, senha, cidade, data_criacao))
    user_id = cursor.lastrowid
    cursor.execute("INSERT INTO perfis_trabalhador (usuario_id, descricao) VALUES (?, ?)", (user_id, profissao))

conn.commit()
conn.close()

print("Dados expandidos inseridos!")