import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import os
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import psycopg2
from typing import Optional, List, Dict, Any
import hashlib
import time
from daisugi_auth_guard import auth_guard, CORE_DEVELOPERS, validar_segredos_servidor, verificar_senha_soberana

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
    token_jwt: str  # Suporte a RBAC e spec 4.2

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
    codigo_rastreamento: Optional[str] = None
    arquivo_anexo: Optional[Dict[str, Any]] = None
    link_documento_dw: Optional[Dict[str, Any]] = None

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

class ForensicAuthenticityRequest(BaseModel):
    cota_documento: str
    hash_esperado: str

# ==========================================
# 2. CONFIGURAÇÃO DE BANCO DE DADOS
# ==========================================
def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "memoria_vetorial"),
        user=os.getenv("DB_USER", "admin"),
        password=os.environ["DB_PASSWORD"],
        connect_timeout=5
    )

@app.on_event("startup")
def setup_enterprise_database():
    # Fail-Fast Soberano: exige variáveis obrigatórias do cofre (CA-06)
    validar_segredos_servidor()
    
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

        conn.commit()
        cur.close()
        conn.close()
        print("✅ Banco de Dados Multi-Tenant configurado com sucesso.")
    except Exception as e:
        print(f"⚠️ [AVISO] Banco de Dados PostgreSQL local offline (operando em modo desacoplado/cache): {e}")

# ==========================================
# 3. ROTAS ASSÍNCRONAS E ROTEAMENTO DA DAI
# ==========================================
@app.post("/auth/login", response_model=LoginResponse)
def login(request: LoginRequest):
    u = request.usuario.lower().strip()
    s = request.senha.strip() if request.senha else ""

    if not s:
        raise HTTPException(status_code=401, detail="Credenciais inválidas. Acesso restrito à Portaria Soberana DAI.")

    # Acesso Soberano Exclusivo: Ronaldo Akagui (CA-01 a CA-05)
    usuarios_soberanos = {dev.lower() for dev in CORE_DEVELOPERS}
    if u in usuarios_soberanos:
        if verificar_senha_soberana(s):
            dev_token = auth_guard.generate_token({
                "sub": u,
                "role": "core_developer",
                "is_core_developer": True,
                "cadeira_principal": "Core Platform Developer",
                "salas_liberadas": ["Painel Quarentena", "Governança de Travas ERP", "Soberania de Código Core"]
            }, expires_in=28800)
            return LoginResponse(
                autenticado=True,
                id_usuario=99,
                nome="Ronaldo Akagui (Soberania Core)",
                perfil="core_developer",
                salas_liberadas=[
                    Sala(nome="Soberania de Código Core", funcao="Acesso Mestre Akagui", cor="#8B5CF6"),
                    Sala(nome="Painel Quarentena", funcao="Auditoria e Governança", cor="#EF4444"),
                    Sala(nome="Governança de Travas ERP", funcao="Controle de Travas", cor="#F59E0B")
                ],
                clientes_acesso=["presidencia", "controladoria", "financeiro", "operacoes", "engenharia", "gg", "ti"],
                token_jwt=dev_token
            )
        else:
            raise HTTPException(status_code=401, detail="Credenciais inválidas. Acesso restrito à Portaria Soberana DAI.")

    # Bloqueio imediato de qualquer outro usuário (CA-03, CA-04, CA-05)
    raise HTTPException(status_code=401, detail="Credenciais inválidas. Acesso restrito à Portaria Soberana DAI.")

@app.post("/chat/triage", response_model=TriageResponse)
def triage(request: TriageRequest):
    """Triagem inteligente com proteção de Cache O(1) via Redis para evitar Gargalo no RAG."""
    prompt = request.texto_usuario.strip()
    
    # Geração de Código de Rastreamento Único do Atendimento
    random_suffix = hashlib.md5(f"{prompt}_{time.time()}".encode()).hexdigest()[:6].upper()
    codigo_rastreamento = f"TKT-DAI-2026-{random_suffix}"
    
    # Detecção inteligente de demanda documental / Data Warehouse
    link_dw = None
    arquivo_anexo = None
    p_lower = prompt.lower()
    if any(k in p_lower for k in ["ccb", "contrato", "nota", "fatura", "dw", "data warehouse", "documento", "arquivo", "relatorio", "laudo", "comprovante"]):
        link_dw = {
            "titulo": f"Registro de Auditoria DW: Ref. {codigo_rastreamento}",
            "hash": hashlib.sha256(prompt.encode()).hexdigest(),
            "url": f"https://sugoiconstrutora.sharepoint.com/:f:/r/sites/DataHubDocumentalSUGOI/Documentos%20Compartilhados/SUGOI_HUB_GED/HUB_EXTERNO/00_REPOSIT%C3%93RIO/HDW-TRANSIT%C3%93RIO?doc={codigo_rastreamento}",
            "repositorio": "Data Warehouse Corporativo - Partição Fiduciária"
        }
        arquivo_anexo = {
            "nome": f"Comprovante_Atendimento_{codigo_rastreamento}.pdf",
            "tipo": "PDF / Documento Oficial",
            "tamanho": "142 KB",
            "status": "Emitido & Assinado Digitalmente"
        }

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
            resposta_dai=f"⚡ (Via Cache) Olá! Que bom ter você aqui. Já consultei meu diretório instantâneo e encaminhei seu caso para a sala **{cache_data['destino']}** ({cache_data['cliente_destino']}). O anfitrião já pode ser notificado no seu painel.",
            laudo_final=f"✅ Triagem Concluída via Cache O(1) — Roteado para {cache_data['destino']}.",
            cache_hit=True,
            codigo_rastreamento=codigo_rastreamento,
            arquivo_anexo=arquivo_anexo,
            link_documento_dw=link_dw
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
            return TriageResponse(
                status_fuzzy=True,
                resposta_dai="Olá! Identifiquei que seu usuário ainda não possui vinculação às unidades corporativas ativas. Por favor, contate o administrador da recepção.",
                laudo_final="❌ Acesso Não Autorizado às Unidades.",
                codigo_rastreamento=codigo_rastreamento
            )

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
            resposta_dai=f"Perfeito! Compreendi sua solicitação com precisão. Já reservei seu atendimento na sala **{destino}** da unidade **{cliente_destino}**. Seu ticket digital já foi gerado na aba de Contexto e você pode notificar o anfitrião a qualquer momento.",
            laudo_final=f"✅ Triagem Concluída — Encaminhado para {destino} ({cliente_destino}).",
            cache_hit=False,
            codigo_rastreamento=codigo_rastreamento,
            arquivo_anexo=arquivo_anexo,
            link_documento_dw=link_dw
        )
    else:
        # Falso Fuzzy - Pede Refinamento com Empatia
        return TriageResponse(
            status_fuzzy=True,
            resposta_dai="Compreendo sua demanda! Para garantir que eu te encaminhe exatamente para o especialista correto e sem perda de tempo, me conte rapidinho:\n\n1. **O que** você precisa resolver hoje?\n2. **Qual setor** ou pessoa você busca (ex: Financeiro, Jurídico, Obras ou Diretoria)?\n3. Trata-se de entrega de documentos, reunião ou suporte?",
            laudo_final="⚠️ Triagem em Refinamento Assistido (Fuzzy).",
            cache_hit=False,
            codigo_rastreamento=codigo_rastreamento,
            arquivo_anexo=arquivo_anexo,
            link_documento_dw=link_dw
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

# [DESATIVADO NA MISSAO 0b - DECISAO D1: ROTA DESLIGADA (404), CODIGO PRESERVADO]
# @app.post("/api/quarentena/validar", status_code=202)
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

# ==========================================
# 4.1. RECEPTOR DE CALLBACK DO HUDSON DC
# ==========================================
@app.post("/api/webhooks/hudson-callback", status_code=200)
def receber_callback_hudson(payload: Dict[str, Any]):
    """
    Receptor oficial de callbacks assincronos do HUDSON DC:
    - Retorno da resposta do anfitriao (liberacao de catraca na portaria da DAI);
    - Conclusao de laudo pericial da esteira KAN-SA.
    """
    ticket_id = payload.get("ticket_id")
    status = payload.get("status")
    catraca = payload.get("catraca_liberada", False)
    resposta = payload.get("resposta_anfitriao")
    print(f"🔔 [HUDSON CALLBACK] Ticket '{ticket_id}' recebido | Status: {status} | Catraca Liberada: {catraca}")
    return {
        "status": "CALLBACK_PROCESSADO",
        "ticket_id": ticket_id,
        "catraca_liberada": catraca,
        "resposta_anfitriao": resposta
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
# 4.2. ROTAS FORENSES E ENLACE HDC × HDW (DESATIVADAS NA MISSAO 0b - DECISOES D2/D3: 404)
# ==========================================
from hdc_hdw_bridge import hdc_hdw_bridge

# @app.get("/api/v1/hdw/status")
async def get_hdw_status():
    """Consulta o status do enlace e saúde da OpenVPN com o HDW local (CentOS 7)."""
    return await hdc_hdw_bridge.verificar_status_enlace()

# @app.post("/api/v1/forensics/authenticity")
async def verificar_autenticidade(request: ForensicAuthenticityRequest):
    """
    Rota pericial homologada pelo Dr. Taylor:
    Recalcula o hash do documento direto no disco do HDW e confronta com o log imutável de custódia.
    """
    return await hdc_hdw_bridge.validar_autenticidade_forense(
        cota_documento=request.cota_documento,
        hash_esperado=request.hash_esperado
    )

# @app.get("/api/v1/hdw/estantes")
async def listar_estantes_hdw():
    """Retorna as 6 Estantes Canônicas da Biblioteca Multidisciplinar do HDW."""
    return await hdc_hdw_bridge.obter_catalogo_estantes()

# @app.get("/api/v1/hdw/estantes/{estante_id}/itens")
async def listar_itens_estante_hdw(estante_id: str, limit: int = 50):
    """Consulta os itens/documentos custodiados em uma estante do HDW."""
    return await hdc_hdw_bridge.listar_itens_estante(estante_id=estante_id, limite=limit)

# @app.get("/api/v1/hdw/documentos/{cota_documento}/render")
async def renderizar_documento_hdw(cota_documento: str):
    """
    Streaming binário direto do HDW (1 MiB chunks) para renderização no navegador da DAI.
    Preserva a memória RAM do CentOS 7 e garante não-repúdio.
    """
    stream_generator = hdc_hdw_bridge.obter_stream_documento(cota_documento)
    return StreamingResponse(
        stream_generator,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{cota_documento}.pdf"',
            "X-HDW-Cota": cota_documento
        }
    )

# ==========================================
# 4.3. HARNESS & CHAT STREAMING SOBERANO (HDC)
# ==========================================
from hdc_guardrails_harness import hdc_harness, ChatStreamRequest
import json

@app.post("/api/v1/hdc/guardrails/check")
async def check_guardrails(request: ChatStreamRequest, credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))):
    """Auditoria de Guardrails & Pre-Retrieval antes da inferência."""
    user_payload = auth_guard.decode_token(credentials.credentials) if credentials else {}
    usuario_id = user_payload.get("sub", "visitante_anonimo")
    role = user_payload.get("role", "visitante")
    ultimo_prompt = request.messages[-1].get("content", "") if request.messages else ""
    
    verdict = hdc_harness.sanitizar_e_injetar_harness(
        usuario_id=usuario_id,
        wbs_solicitado=request.wbs_id,
        role_usuario=role,
        prompt_usuario=ultimo_prompt
    )
    return verdict.model_dump()

@app.post("/api/v1/chat/completions/stream")
async def chat_completions_stream(request: ChatStreamRequest, credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))):
    """
    Rota Oficial de Streaming SSE do Chat Soberano com Harness.
    Garante Zero Alucinação, Pre-Retrieval e execução a Custo Zero de tokens na nuvem privada OCI.
    """
    user_payload = auth_guard.decode_token(credentials.credentials) if credentials else {}
    usuario_id = user_payload.get("sub", "operador_lobby")
    role = user_payload.get("role", "colaborador")
    ultimo_prompt = request.messages[-1].get("content", "") if request.messages else ""

    verdict = hdc_harness.sanitizar_e_injetar_harness(
        usuario_id=usuario_id,
        wbs_solicitado=request.wbs_id,
        role_usuario=role,
        prompt_usuario=ultimo_prompt
    )

    if not verdict.autorizado:
        async def erro_generator():
            msg_erro = json.dumps({"error": verdict.motivo, "tentativas_restantes": verdict.tentativas_restantes})
            yield f"data: {msg_erro}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(erro_generator(), media_type="text/event-stream")

    stream_gen = hdc_harness.gerar_stream_llm(
        modelo_solicitado=request.model,
        wbs_id=verdict.wbs_autorizado or request.wbs_id,
        nivel_sigilo=verdict.nivel_sigilo,
        mensagens=request.messages
    )
    return StreamingResponse(stream_gen, media_type="text/event-stream")


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
    porta = int(os.getenv("PORT", "8010"))
    uvicorn.run("api_backend:app", host="0.0.0.0", port=porta, reload=False)


