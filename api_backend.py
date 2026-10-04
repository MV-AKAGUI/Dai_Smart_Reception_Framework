from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
from langchain_ollama import OllamaEmbeddings
from typing import Optional, Tuple

app = FastAPI(title="Dai Smart Reception API", description="API-First Backend para Roteamento Inteligente e Triagem")

# ==========================================
# 0. DADOS MOCKADOS E CONFIGURAÇÃO
# ==========================================
MOCK_USERS = {
    "admin": {"senha": "123", "perfil": "Diretoria", "nome": "Ronaldo"},
    "dev": {"senha": "123", "perfil": "Desenvolvimento", "nome": "Engenheiro"},
    "cliente": {"senha": "123", "perfil": "Cliente B2B", "nome": "Parceiro Daisugi"}
}

embedder = OllamaEmbeddings(model="nomic-embed-text")

# ==========================================
# 1. MODELOS DE DADOS (PYDANTIC)
# ==========================================
class LoginRequest(BaseModel):
    usuario: str
    senha: str

class LoginResponse(BaseModel):
    autenticado: bool
    nome: Optional[str] = None
    perfil: Optional[str] = None
    mensagem: str

class TriageRequest(BaseModel):
    texto_usuario: str

class TriageResponse(BaseModel):
    status_fuzzy: bool # Se True, caiu na ambiguidade e precisa das 3 perguntas
    destino: Optional[str] = None
    resposta_dai: str
    laudo_final: str

# ==========================================
# 2. FUNÇÕES DE BANCO DE DADOS E MEMÓRIA
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
def setup_dai_memory():
    """Inicia a homeostase do banco de dados na subida da API."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS dai_memoria (
                id SERIAL PRIMARY KEY,
                texto_original TEXT,
                embedding vector(768),
                acao_tipo TEXT,
                destino TEXT,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Banco de Dados e Vector Extension configurados com sucesso.")
    except Exception as e:
        print(f"❌ Erro ao configurar banco de dados: {e}")

def buscar_na_memoria(texto: str) -> Tuple[Optional[tuple], list]:
    vetor_busca = embedder.embed_query(texto)
    vetor_str = f"[{','.join(map(str, vetor_busca))}]"
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT texto_original, acao_tipo, destino, embedding <-> %s::vector AS distancia
        FROM dai_memoria
        ORDER BY distancia ASC
        LIMIT 1;
    """, (vetor_str,))
    
    resultado = cur.fetchone()
    cur.close()
    conn.close()
    return resultado, vetor_busca

# ==========================================
# 3. ENDPOINTS DA API
# ==========================================
@app.post("/auth/login", response_model=LoginResponse)
def login(request: LoginRequest):
    """Endpoint responsável pela Autenticação e injeção do Perfil de Acesso."""
    usuario = request.usuario.lower()
    
    if usuario in MOCK_USERS and MOCK_USERS[usuario]["senha"] == request.senha:
        return LoginResponse(
            autenticado=True,
            nome=MOCK_USERS[usuario]["nome"],
            perfil=MOCK_USERS[usuario]["perfil"],
            mensagem="Autenticação bem-sucedida."
        )
    
    raise HTTPException(status_code=401, detail="Credenciais inválidas.")

@app.post("/chat/triage", response_model=TriageResponse)
def triage(request: TriageRequest):
    """
    Endpoint principal da Dai. Recebe uma queixa, calcula os embeddings, 
    busca a similaridade matemática e decide se roteia (Fast-Track) 
    ou se faz perguntas de refinamento (Fuzzy).
    """
    prompt = request.texto_usuario.strip()
    
    if prompt.lower() == "/auditoria":
        return TriageResponse(
            status_fuzzy=False,
            resposta_dai="🤫 Extraindo registros da mente vetorial...",
            laudo_final="🕵️ Auditoria interna acionada. Imprimindo logs no console."
        )

    # 1. Geração de Vetor e Busca no RAG
    resultado, vetor = buscar_na_memoria(prompt)
    distancia = resultado[3] if resultado else 999.0
    
    # 2. Tomada de Decisão (Threshold < 0.3)
    if resultado and distancia < 0.3:
        destino = resultado[2]
        return TriageResponse(
            status_fuzzy=False,
            destino=destino,
            resposta_dai=f"🔍 Suas métricas são claras. Encaminhando para o **{destino}**...",
            laudo_final=f"✅ Triagem Concluída: Rota identificada para {destino}."
        )
    else:
        # Lógica Fuzzy Acionada
        pergunta_refinamento = (
            "Para que eu possa direcionar sua queixa para o corredor correto, preciso que refine seu pedido:\n"
            "**(i) O QUE** você precisa resolver?\n"
            "**(ii) COMO** espera que a equipe ajude?\n"
            "**(iii) POR QUE** isso é uma prioridade agora?"
        )
        return TriageResponse(
            status_fuzzy=True,
            destino=None,
            resposta_dai=pergunta_refinamento,
            laudo_final="⚠️ Pendente: A Dai solicitou mais clareza ao paciente antes de acionar os especialistas."
        )

if __name__ == "__main__":
    import uvicorn
    # Executa o servidor na porta 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
