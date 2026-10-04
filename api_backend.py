from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
from langchain_ollama import OllamaEmbeddings
from typing import Optional, Tuple, List, Dict
import json

app = FastAPI(title="Dai Smart Reception API", description="API Enterprise Multi-Tenant para Triagem e Roteamento")

embedder = OllamaEmbeddings(model="nomic-embed-text")

# ==========================================
# 1. MODELOS DE DADOS (PYDANTIC)
# ==========================================
class LoginRequest(BaseModel):
    usuario: str
    senha: str

class Sala(BaseModel):
    nome: str
    funcao: str
    cor: str

class LoginResponse(BaseModel):
    autenticado: bool
    id_usuario: int
    nome: str
    perfil: str
    salas_liberadas: List[Sala]
    clientes_acesso: List[str]

class TriageRequest(BaseModel):
    id_usuario: int
    texto_usuario: str

class TriageResponse(BaseModel):
    status_fuzzy: bool
    destino: Optional[str] = None
    cliente_destino: Optional[str] = None
    resposta_dai: str
    laudo_final: str

class FeedbackRequest(BaseModel):
    texto_usuario: str
    destino_final: str
    cliente_destino: str
    resolucao_especialista: str

class FeedbackResponse(BaseModel):
    status: str
    mensagem: str

# ==========================================
# 2. CONFIGURAÇÃO DE BANCO DE DADOS (MULTI-TENANT)
# ==========================================
def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        port="5432",
        database="memoria_vetorial",
        user="admin",
        password="masterkey123"
    )

@app.on_event("startup")
def setup_enterprise_database():
    """Cria a estrutura Multi-Tenant e injeta dados iniciais caso não existam."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        
        # Tabelas Estruturais
        cur.execute("""
            CREATE TABLE IF NOT EXISTS clientes (
                id VARCHAR(50) PRIMARY KEY,
                nome TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                login VARCHAR(50) UNIQUE,
                senha VARCHAR(50),
                nome TEXT,
                perfil TEXT
            );
            CREATE TABLE IF NOT EXISTS usuario_clientes (
                id_usuario INT REFERENCES usuarios(id),
                id_cliente VARCHAR(50) REFERENCES clientes(id),
                PRIMARY KEY (id_usuario, id_cliente)
            );
            CREATE TABLE IF NOT EXISTS salas_dinamicas (
                id SERIAL PRIMARY KEY,
                id_cliente VARCHAR(50) REFERENCES clientes(id),
                nome TEXT,
                funcao TEXT,
                cor TEXT
            );
        """)

        # Criar tabelas físicas isoladas de memória por cliente (Isolamento 1B)
        clientes_iniciais = ['controladoria', 'juridico']
        for c in clientes_iniciais:
            cur.execute(f"INSERT INTO clientes (id, nome) VALUES ('{c}', '{c.capitalize()}') ON CONFLICT DO NOTHING;")
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS memoria_{c} (
                    id SERIAL PRIMARY KEY,
                    texto_original TEXT,
                    resolucao_contexto TEXT,
                    embedding vector(768),
                    destino TEXT,
                    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

        # Mock de dados na subida para simular a base configurada
        cur.execute("INSERT INTO usuarios (login, senha, nome, perfil) VALUES ('maria', '123', 'Maria CEO', 'Diretoria Geral') ON CONFLICT DO NOTHING;")
        cur.execute("INSERT INTO usuarios (login, senha, nome, perfil) VALUES ('joao', '123', 'João Contábil', 'Auditor') ON CONFLICT DO NOTHING;")
        
        # João só vê controladoria. Maria vê ambos.
        cur.execute("INSERT INTO usuario_clientes (id_usuario, id_cliente) VALUES (1, 'controladoria') ON CONFLICT DO NOTHING;")
        cur.execute("INSERT INTO usuario_clientes (id_usuario, id_cliente) VALUES (1, 'juridico') ON CONFLICT DO NOTHING;")
        cur.execute("INSERT INTO usuario_clientes (id_usuario, id_cliente) VALUES (2, 'controladoria') ON CONFLICT DO NOTHING;")

        # Inserindo salas dinâmicas
        cur.execute("INSERT INTO salas_dinamicas (id_cliente, nome, funcao, cor) VALUES ('controladoria', 'Auditoria Fiscal', 'Revisão', 'info') ON CONFLICT DO NOTHING;")
        cur.execute("INSERT INTO salas_dinamicas (id_cliente, nome, funcao, cor) VALUES ('juridico', 'Dr. Saul', 'Contratos Cíveis', 'warning') ON CONFLICT DO NOTHING;")

        conn.commit()
        cur.close()
        conn.close()
        print("✅ Banco de Dados Multi-Tenant configurado com sucesso.")
    except Exception as e:
        print(f"❌ Erro ao configurar banco de dados: {e}")


# ==========================================
# 3. ROTAS E LÓGICA DE NEGÓCIO
# ==========================================
@app.post("/auth/login", response_model=LoginResponse)
def login(request: LoginRequest):
    """Autentica o usuário e busca suas permissões e salas dinâmicas (Item 2B e 3B)."""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT id, nome, perfil FROM usuarios WHERE login = %s AND senha = %s", (request.usuario.lower(), request.senha))
    user = cur.fetchone()
    
    if not user:
        cur.close()
        conn.close()
        raise HTTPException(status_code=401, detail="Credenciais inválidas.")
        
    id_usuario, nome, perfil = user
    
    # Busca clientes permitidos para este usuário
    cur.execute("SELECT id_cliente FROM usuario_clientes WHERE id_usuario = %s", (id_usuario,))
    clientes = [row[0] for row in cur.fetchall()]
    
    if not clientes:
        clientes = []
        
    # Busca as salas disponíveis baseadas nos clientes que ele tem acesso
    salas = []
    if clientes:
        format_strings = ','.join(['%s'] * len(clientes))
        cur.execute(f"SELECT nome, funcao, cor FROM salas_dinamicas WHERE id_cliente IN ({format_strings})", tuple(clientes))
        for row in cur.fetchall():
            salas.append(Sala(nome=row[0], funcao=row[1], cor=row[2]))

    cur.close()
    conn.close()
    
    return LoginResponse(
        autenticado=True,
        id_usuario=id_usuario,
        nome=nome,
        perfil=perfil,
        salas_liberadas=salas,
        clientes_acesso=clientes
    )

@app.post("/chat/triage", response_model=TriageResponse)
def triage(request: TriageRequest):
    """Roteamento simultâneo com Leveza Matemática (RAG) e Validação Fuzzy."""
    prompt = request.texto_usuario.strip()
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # 1. Descobrir quais tabelas o usuário pode acessar (Segurança/Isolamento)
    cur.execute("SELECT id_cliente FROM usuario_clientes WHERE id_usuario = %s", (request.id_usuario,))
    clientes = [row[0] for row in cur.fetchall()]
    
    if not clientes:
        cur.close()
        conn.close()
        return TriageResponse(
            status_fuzzy=True,
            resposta_dai="Você não possui acesso a nenhum domínio ou cliente registrado.",
            laudo_final="❌ Acesso Negado."
        )

    # 2. Busca Matemática RAG (Simultânea via UNION ALL)
    vetor_busca = embedder.embed_query(prompt)
    vetor_str = f"[{','.join(map(str, vetor_busca))}]"
    
    query_parts = []
    for c in clientes:
        # A matemática não sabe origem, ela apenas calcula a distância L2 (<->).
        part = f"(SELECT texto_original, destino, '{c}' as cliente_destino, embedding <-> '{vetor_str}'::vector AS distancia FROM memoria_{c} ORDER BY distancia ASC LIMIT 1)"
        query_parts.append(part)
        
    full_query = " UNION ALL ".join(query_parts) + " ORDER BY distancia ASC LIMIT 1;"
    
    try:
        cur.execute(full_query)
        resultado = cur.fetchone()
    except Exception as e:
        resultado = None # Em caso de tabela vazia ou não existente
        conn.rollback()

    cur.close()
    conn.close()
    
    distancia = resultado[3] if resultado else 999.0
    
    # 3. Lógica Fuzzy de 3 Perguntas (Leveza: Sem LLM se for ambíguo)
    if resultado and distancia < 0.3:
        destino = resultado[1]
        cliente_destino = resultado[2]
        return TriageResponse(
            status_fuzzy=False,
            destino=destino,
            cliente_destino=cliente_destino,
            resposta_dai=f"🔍 Suas métricas são claras. Encaminhando para a Sala **{destino}** do departamento de **{cliente_destino.capitalize()}**.",
            laudo_final=f"✅ Triagem Concluída: Rota {destino} ({cliente_destino})."
        )
    else:
        # Aciona o Protocolo Fuzzy Padrão A (Universal)
        pergunta_refinamento = (
            "Para que eu possa direcionar sua queixa com exatidão, preciso que refine seu pedido:\n"
            "**(i) O QUE** você precisa resolver?\n"
            "**(ii) COMO** espera que a equipe ajude?\n"
            "**(iii) POR QUE** isso é uma prioridade agora?"
        )
        return TriageResponse(
            status_fuzzy=True,
            resposta_dai=pergunta_refinamento,
            laudo_final="⚠️ Triagem Inconclusiva: A Dai acionou o modo Fuzzy solicitando clareza."
        )

@app.post("/triage/learn", response_model=FeedbackResponse)
def aprender_com_triagem(request: FeedbackRequest):
    """
    O Coração da Evolução da Dai.
    Quando o Especialista encerra o chamado e resolve o problema, 
    a interação (texto inicial + resolução do especialista) vira um novo lastro matemático.
    Isso alimenta a tabela isolada do cliente, retroalimentando o RAG e garantindo automação total.
    """
    # 1. Concatenar a dor inicial com a solução do especialista
    texto_aprendizado = f"Queixa: {request.texto_usuario} | Resolução Prontuário: {request.resolucao_especialista}"
    
    # 2. Converter o aprendizado em matemática pura
    vetor_novo = embedder.embed_query(texto_aprendizado)
    vetor_str = f"[{','.join(map(str, vetor_novo))}]"
    
    # 3. Injetar na memória específica daquele Tenant (Lastro de Aprendizado)
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(f"""
            INSERT INTO memoria_{request.cliente_destino} (texto_original, resolucao_contexto, destino, embedding)
            VALUES (%s, %s, %s, %s::vector)
        """, (request.texto_usuario, request.resolucao_especialista, request.destino_final, vetor_str))
        conn.commit()
        status = "sucesso"
        msg = f"A Dai evoluiu. Nova trilha sináptica criada no domínio '{request.cliente_destino}'."
    except Exception as e:
        status = "erro"
        msg = str(e)
        conn.rollback()
    finally:
        cur.close()
        conn.close()
        
    return FeedbackResponse(status=status, mensagem=msg)
