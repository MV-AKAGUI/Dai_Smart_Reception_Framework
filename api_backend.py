import os
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import psycopg2
from typing import Optional, Tuple, List, Dict, Any
import hashlib
import time
from daisugi_auth_guard import auth_guard, CORE_DEVELOPERS

app = FastAPI(
    title="Dai Smart Reception API", 
    description="API Enterprise Multi-Tenant para Triagem e Roteamento - Arquitetura Assíncrona & RAG Fuzzy",
    version="1.1.0"
)

# CORS para aceitar conexões do Frontend Web / Mobile / Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicialização de Embeddings com suporte a OLLAMA_HOST em nuvem
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
try:
    from langchain_ollama import OllamaEmbeddings
    embedder = OllamaEmbeddings(model=os.getenv("EMBED_MODEL", "nomic-embed-text"), base_url=OLLAMA_HOST)
except Exception as e:
    embedder = None
    print(f"⚠️ Embedder Ollama inicializado em modo offline/degradado: {e}")

security = HTTPBearer()

# ==========================================
# 0. SIMULAÇÃO DE INFRAESTRUTURA (REDIS & JWT)
# ==========================================

# Simula o banco em memória (Redis) para evitar bater no RAG (Chroma/PgVector) toda hora
REDIS_CACHE_MOCK: Dict[str, dict] = {}

# Middleware RBAC & SoD integrado ao Daisugi_Ecosystem_Cofre-PAM-IGA
def verify_operator_role(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Middleware RBAC & SoD: Valida se o Token possui alçada de Validador/Checker no Cofre PAM/IGA."""
    return auth_guard.require_checker(credentials)

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
    token_jwt: str  # Suporte a RBAC

class TriageRequest(BaseModel):
    id_usuario: int
    texto_usuario: str

class TriageResponse(BaseModel):
    status_fuzzy: bool
    destino: Optional[str] = None
    cliente_destino: Optional[str] = None
    resposta_dai: str
    laudo_final: str
    cache_hit: bool = False

class FeedbackRequest(BaseModel):
    texto_usuario: str
    destino_final: str
    cliente_destino: str
    resolucao_especialista: str
    is_global: bool = False

class FeedbackResponse(BaseModel):
    status: str
    mensagem: str

class QuarentenaRequest(BaseModel):
    hash_id_documento: str
    aprovado: bool
    maker_identity: Optional[str] = None

# ==========================================
# 2. CONFIGURAÇÃO DE BANCO DE DADOS
# ==========================================
def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "memoria_vetorial"),
        user=os.getenv("DB_USER", "admin"),
        password=os.getenv("DB_PASSWORD", "masterkey123"),
        connect_timeout=5
    )

@app.on_event("startup")
def setup_enterprise_database():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS clientes (id VARCHAR(50) PRIMARY KEY, nome TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS usuarios (id SERIAL PRIMARY KEY, login VARCHAR(50) UNIQUE, senha VARCHAR(50), nome TEXT, perfil TEXT);
            CREATE TABLE IF NOT EXISTS usuario_clientes (id_usuario INT REFERENCES usuarios(id), id_cliente VARCHAR(50) REFERENCES clientes(id), PRIMARY KEY (id_usuario, id_cliente));
            CREATE TABLE IF NOT EXISTS salas_dinamicas (id SERIAL PRIMARY KEY, id_cliente VARCHAR(50) REFERENCES clientes(id), nome TEXT, funcao TEXT, cor TEXT);
            CREATE TABLE IF NOT EXISTS memoria_global_daisugi (id SERIAL PRIMARY KEY, texto_original TEXT, resolucao_contexto TEXT, embedding vector(768), destino TEXT, criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        """)

        clientes_iniciais = ['controladoria', 'juridico']
        for c in clientes_iniciais:
            cur.execute(f"INSERT INTO clientes (id, nome) VALUES ('{c}', '{c.capitalize()}') ON CONFLICT DO NOTHING;")
            cur.execute(f"CREATE TABLE IF NOT EXISTS memoria_{c} (id SERIAL PRIMARY KEY, texto_original TEXT, resolucao_contexto TEXT, embedding vector(768), destino TEXT, criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP);")

        cur.execute("""
            INSERT INTO usuarios (id, login, senha, nome, perfil) 
            VALUES (1, 'admin', '123', 'Administrador Operador', 'admin'),
                   (3, 'cliente', '123', 'Cliente Teste', 'cliente'),
                   (4, 'controller', '123', 'Controller Geral (Checker SoD)', 'admin'),
                   (5, 'advogado', '123', 'Advogado Imobiliário', 'admin'),
                   (6, 'engenheiro', '123', 'Engenheiro da Obra (Maker)', 'cliente'),
                   (7, 'diretor', '123', 'Diretor Presidente', 'admin')
            ON CONFLICT (id) DO NOTHING;
        """)
        cur.execute("""
            INSERT INTO usuario_clientes (id_usuario, id_cliente)
            VALUES (1, 'controladoria'), (1, 'juridico'), (3, 'controladoria'),
                   (4, 'controladoria'), (4, 'juridico'), (5, 'juridico'),
                   (6, 'controladoria'), (7, 'controladoria'), (7, 'juridico')
            ON CONFLICT (id_usuario, id_cliente) DO NOTHING;
        """)

        conn.commit()
        cur.close()
        conn.close()
        print("✅ Banco de Dados Multi-Tenant configurado com sucesso.")
    except Exception as e:
        print(f"❌ Erro ao configurar banco de dados: {e}")

# ==========================================
# 3. ROTAS ASSÍNCRONAS E ROTEAMENTO DA DAI
# ==========================================
@app.post("/auth/login", response_model=LoginResponse)
def login(request: LoginRequest):
    u = request.usuario.lower()
    s = request.senha

    # Validação de credenciais de teste para Cadeiras PAM / IGA
    if s != '123':
        raise HTTPException(status_code=401, detail="Credenciais inválidas.")

    if u in [dev.lower() for dev in CORE_DEVELOPERS]:
        dev_token = auth_guard.generate_token({
            "sub": u,
            "role": "core_developer",
            "is_core_developer": True,
            "cadeira_principal": "Core Platform Developer",
            "salas_liberadas": ["Painel Quarentena", "Governança de Travas ERP", "Soberania de Código Core"]
        })
        return LoginResponse(
            autenticado=True, id_usuario=99, nome="Desenvolvedor Soberano Daisugi (Core)", perfil="core_developer",
            salas_liberadas=[
                Sala(nome="Soberania de Código Core", funcao="Acesso Mestre", cor="#8B5CF6"),
                Sala(nome="Painel Quarentena", funcao="Auditoria Total", cor="#EF4444")
            ],
            clientes_acesso=["controladoria", "juridico"],
            token_jwt=dev_token
        )
    elif u == 'controller':
        return LoginResponse(
            autenticado=True, id_usuario=4, nome="Controller Geral (Checker Quarentena)", perfil="admin",
            salas_liberadas=[
                Sala(nome="Painel Quarentena", funcao="Auditoria de CCB e Risco", cor="#EF4444"),
                Sala(nome="Governança de Travas ERP", funcao="Parametrização e SoD", cor="#3B82F6")
            ],
            clientes_acesso=["controladoria", "juridico"],
            token_jwt="token_jwt_operador_secreto"
        )
    elif u == 'advogado':
        return LoginResponse(
            autenticado=True, id_usuario=5, nome="Advogado Imobiliário (Pareceres)", perfil="admin",
            salas_liberadas=[
                Sala(nome="Painel Quarentena", funcao="Análise de Minutas e Risco Legal", cor="#8B5CF6"),
                Sala(nome="Sala Jurídica", funcao="Consultas Imobiliárias", cor="#6366F1")
            ],
            clientes_acesso=["juridico"],
            token_jwt="token_jwt_operador_secreto"
        )
    elif u == 'engenheiro':
        return LoginResponse(
            autenticado=True, id_usuario=6, nome="Engenheiro da Obra (Maker Solicitante)", perfil="cliente",
            salas_liberadas=[
                Sala(nome="Medição e Obras", funcao="Acompanhamento Físico", cor="#10B981")
            ],
            clientes_acesso=["controladoria"],
            token_jwt="token_jwt_cliente_comum"
        )
    elif u == 'diretor':
        return LoginResponse(
            autenticado=True, id_usuario=7, nome="Diretor Presidente (Super-Auditor)", perfil="admin",
            salas_liberadas=[
                Sala(nome="Painel Quarentena", funcao="Alçada Máxima", cor="#EF4444"),
                Sala(nome="Diretoria & Métricas", funcao="Visão Geral Corporativa", cor="#00B4D8")
            ],
            clientes_acesso=["controladoria", "juridico"],
            token_jwt="token_jwt_operador_secreto"
        )
    elif u == 'admin':
        return LoginResponse(
            autenticado=True, id_usuario=1, nome="Administrador Operador", perfil="admin",
            salas_liberadas=[Sala(nome="Painel Quarentena", funcao="Validação de Risco", cor="#EF4444")], 
            clientes_acesso=["controladoria", "juridico"],
            token_jwt="token_jwt_operador_secreto"
        )
    elif u == 'cliente':
        return LoginResponse(
            autenticado=True, id_usuario=3, nome="Cliente Teste", perfil="cliente",
            salas_liberadas=[Sala(nome="Triagem Clínica", funcao="Análise de sintomas", cor="#10b981")], 
            clientes_acesso=["controladoria"],
            token_jwt="token_jwt_cliente_comum"
        )

    raise HTTPException(status_code=401, detail="Credenciais inválidas.")

@app.post("/chat/triage", response_model=TriageResponse)
def triage(request: TriageRequest):
    """Triagem inteligente com proteção de Cache O(1) via Redis para evitar Gargalo no RAG."""
    prompt = request.texto_usuario.strip()
    
    # 1. VERIFICAÇÃO DE CACHE (REDIS) - O(1)
    # Se a mesma dor já foi validada, não consome banco de dados nem LLM.
    hash_prompt = hashlib.md5(prompt.encode()).hexdigest()
    if hash_prompt in REDIS_CACHE_MOCK:
        print(f"⚡ [CACHE HIT] Resposta recuperada do Redis para o hash {hash_prompt}")
        cache_data = REDIS_CACHE_MOCK[hash_prompt]
        return TriageResponse(
            status_fuzzy=False,
            destino=cache_data["destino"],
            cliente_destino=cache_data["cliente_destino"],
            resposta_dai=f"⚡ (Via Cache) Encaminhando para **{cache_data['destino']}** em **{cache_data['cliente_destino']}**.",
            laudo_final="✅ Triagem via Cache Redis O(1).",
            cache_hit=True
        )

    # 2. SE NÃO ESTIVER NO CACHE, EXECUTA O RAG PESADO (PgVector)
    resultado = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id_cliente FROM usuario_clientes WHERE id_usuario = %s", (request.id_usuario,))
        clientes = [row[0] for row in cur.fetchall()]
        
        if not clientes:
            cur.close()
            conn.close()
            return TriageResponse(status_fuzzy=True, resposta_dai="Sem acesso.", laudo_final="❌ Acesso Negado.")

        if embedder:
            try:
                vetor_busca = embedder.embed_query(prompt)
            except Exception as e:
                print(f"⚠️ Embedder Ollama indisponível: {e}")
                vetor_busca = [0.0] * 768
        else:
            vetor_busca = [0.0] * 768

        vetor_str = f"[{','.join(map(str, vetor_busca))}]"
        
        query_parts = [f"(SELECT texto_original, destino, 'Global' as cliente_destino, embedding <-> '{vetor_str}'::vector AS distancia FROM memoria_global_daisugi ORDER BY distancia ASC LIMIT 1)"]
        for c in clientes:
            query_parts.append(f"(SELECT texto_original, destino, '{c}' as cliente_destino, embedding <-> '{vetor_str}'::vector AS distancia FROM memoria_{c} ORDER BY distancia ASC LIMIT 1)")
            
        full_query = " UNION ALL ".join(query_parts) + " ORDER BY distancia ASC LIMIT 1;"
        
        cur.execute(full_query)
        resultado = cur.fetchone()
        cur.close()
        conn.close()
    except Exception as db_err:
        print(f"⚠️ Banco de dados em modo offline/degradado: {db_err}")
        resultado = None

    distancia = resultado[3] if resultado else 999.0
    
    # 3. LÓGICA FUZZY + GRAVAÇÃO EM CACHE SE CERTEZA FOR ALTA
    if resultado and distancia < 0.3:
        destino, cliente_destino = resultado[1], resultado[2]
        
        # Grava no Redis para as próximas chamadas
        REDIS_CACHE_MOCK[hash_prompt] = {"destino": destino, "cliente_destino": cliente_destino}
        
        return TriageResponse(
            status_fuzzy=False, destino=destino, cliente_destino=cliente_destino,
            resposta_dai=f"🔍 Busca RAG concluída. Sala **{destino}** ({cliente_destino}).",
            laudo_final=f"✅ Triagem Concluída.", cache_hit=False
        )
    else:
        # Falso Fuzzy - Pede Refinamento
        return TriageResponse(
            status_fuzzy=True,
            resposta_dai="Para que eu direcione corretamente:\n(i) O QUE você precisa?\n(ii) COMO podemos ajudar?\n(iii) POR QUE é prioridade?",
            laudo_final="⚠️ Triagem Inconclusiva.", cache_hit=False
        )

# ==========================================
# 4. BACKGROUND TASKS E QUARENTENA (RBAC)
# ==========================================

def processar_auditoria_kansa_async(hash_id: str, aprovado: bool):
    """Worker Assíncrono: Finge que está rodando uma auditoria pesada de horas."""
    print(f"🚀 [BACKGROUND TASK] Iniciando auditoria do Kan-sa para Hash {hash_id}... Isso pode demorar.")
    time.sleep(5) # Simula o delay sem travar o Event Loop do FastAPI
    status = "APROVADO" if aprovado else "REJEITADO"
    print(f"✅ [BACKGROUND TASK] Auditoria finalizada. Status: {status}. Hudson notificado via Webhook.")

@app.post("/api/quarentena/validar", status_code=202)
def validar_quarentena(
    request: QuarentenaRequest, 
    bg_tasks: BackgroundTasks, 
    user_payload: Dict[str, Any] = Depends(verify_operator_role)
):
    """
    Rota BLINDADA. Apenas Tokens com Role de Checker/Validador acessam.
    Integrado ao Daisugi_Ecosystem_Cofre-PAM-IGA com proteção contra auto-aprovação SoD (Maker/Checker).
    """
    if request.maker_identity:
        auth_guard.validate_maker_checker(user_payload, request.maker_identity)

    # Joga o processamento da Quarentena para a fila de background
    bg_tasks.add_task(processar_auditoria_kansa_async, request.hash_id_documento, request.aprovado)
    
    # Devolve o status 202 IMEDIATAMENTE (Desacoplamento Temporal)
    return {
        "status_http": 202,
        "message": "Solicitação aceita. O pacote JSON leve foi recebido e o Kan-sa assumiu a tarefa em segundo plano.",
        "hash_processado": request.hash_id_documento,
        "validador_sub": user_payload.get("sub", "mock_user")
    }

@app.post("/auth/handshake")
def auth_handshake(request: LoginRequest):
    """
    Handshake Pré-Lobby da DAI integrado ao Daisugi_Ecosystem_Cofre-PAM-IGA.
    Valida credenciais, emite Token JWT e estabelece canal de confiança.
    """
    return login(request)

@app.get("/api/admin/core-governance")
def get_core_governance_status(dev_payload: Dict[str, Any] = Depends(auth_guard.require_core_developer)):
    """Rota EXCLUSIVA do Desenvolvedor Core da Daisugi (Soberania de Código Akagui)."""
    return {
        "status": "AUTHORIZED",
        "scope": "CORE_DEVELOPER_ONLY",
        "developer": dev_payload.get("sub"),
        "ecosystem": "Daisugi_Ecosystem_Cofre-PAM-IGA",
        "governed_by": "Akagui / Montanha Vermelha",
        "tenants": ["sugoi_sa"]
    }

# ==========================================
# 5. RETROALIMENTAÇÃO & EVOLUÇÃO CONTÍNUA
# ==========================================
@app.post("/triage/learn", response_model=FeedbackResponse)
def aprender_com_triagem(request: FeedbackRequest):
    """
    O Coração da Evolução da Dai.
    Quando o Especialista encerra o chamado e resolve o problema, 
    a interação (texto inicial + resolução do especialista) vira um novo lastro matemático.
    Isso alimenta a tabela isolada do cliente ou global, retroalimentando o RAG e garantindo automação total.
    """
    if not embedder:
        raise HTTPException(status_code=503, detail="Serviço de embedding indisponível para aprendizado.")

    texto_aprendizado = f"Queixa: {request.texto_usuario} | Resolução Prontuário: {request.resolucao_especialista}"
    
    try:
        vetor_novo = embedder.embed_query(texto_aprendizado)
        vetor_str = f"[{','.join(map(str, vetor_novo))}]"
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao vetorizar aprendizado: {str(e)}")
    
    tabela_alvo = "memoria_global_daisugi" if request.is_global else f"memoria_{request.cliente_destino}"
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(f"""
            INSERT INTO {tabela_alvo} (texto_original, resolucao_contexto, destino, embedding)
            VALUES (%s, %s, %s, %s::vector)
        """, (request.texto_usuario, request.resolucao_especialista, request.destino_final, vetor_str))
        conn.commit()
        tipo_memoria = "Global Coletiva" if request.is_global else f"Isolada ({request.cliente_destino})"
        msg = f"A Dai evoluiu. Nova trilha sináptica criada na Memória {tipo_memoria}."
        status = "sucesso"
    except Exception as e:
        conn.rollback()
        status = "erro"
        msg = str(e)
    finally:
        cur.close()
        conn.close()
        
    return FeedbackResponse(status=status, mensagem=msg)

@app.get("/health")
def healthcheck():
    """Healthcheck probe para Docker, Caddy e Oracle OCI Load Balancer."""
    return {
        "status": "HEALTHY",
        "sistema": "Dai Smart Reception API",
        "embedder_ativo": embedder is not None,
        "cache_redis_itens": len(REDIS_CACHE_MOCK),
        "timestamp": time.time()
    }

if __name__ == "__main__":
    import uvicorn
    porta = int(os.getenv("PORT", "8001"))
    uvicorn.run("api_backend:app", host="0.0.0.0", port=porta, reload=False)

