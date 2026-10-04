import streamlit as st
import psycopg2
from langchain_ollama import OllamaEmbeddings
import os
from PIL import Image
import base64
import json

# Carregar configuração do cliente
try:
    with open("config_cliente.json", "r", encoding="utf-8") as f:
        config = json.load(f)
except FileNotFoundError:
    config = {}

def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return f"data:image/png;base64,{base64.b64encode(img_file.read()).decode()}"

# ==========================================
# CONFIGURAÇÃO DE TELA (LAYOUT WIDE)
# ==========================================
page_title = config.get("empresa", {}).get("nome", "Clínica Neural | Dai")
page_icon = config.get("empresa", {}).get("icone", "👩🏻‍💼")
st.set_page_config(page_title=page_title, page_icon=page_icon, layout="wide")

# ==========================================
# 0. TELA DE AUTENTICAÇÃO (LOGIN)
# ==========================================
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

# Banco de dados Mock para testes de Perfil
MOCK_USERS = {
    "admin": {"senha": "123", "perfil": "Diretoria", "nome": "Ronaldo"},
    "dev": {"senha": "123", "perfil": "Desenvolvimento", "nome": "Engenheiro"},
    "cliente": {"senha": "123", "perfil": "Cliente B2B", "nome": "Parceiro Daisugi"}
}

if not st.session_state.autenticado:
    # Mostramos o Avatar na portaria também para dar boas-vindas
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        logo_path = config.get("empresa", {}).get("logo", "Dai_Avatar.png")
        if os.path.exists(logo_path):
            st.image(logo_path, width=150)
            
        cor_primaria = config.get("tema", {}).get("cor_primaria", "#00B4D8")
        titulo_portaria = config.get("textos", {}).get("titulo_portaria", "🔒 Portaria - Daisugi")
        subtitulo_portaria = config.get("textos", {}).get("subtitulo_portaria", "*Por favor, identifique-se antes de acessar nosso Lobby*")
        
        st.markdown(f"<h1 style='color: {cor_primaria};'>{titulo_portaria}</h1>", unsafe_allow_html=True)
        st.markdown(f"{subtitulo_portaria}")
        
        with st.form("login_form"):
            usuario = st.text_input("Usuário (Dica: admin, dev, cliente)").lower()
            senha = st.text_input("Senha (Dica: 123)", type="password")
            submit_btn = st.form_submit_button("Entrar no Lobby")
            
            if submit_btn:
                if usuario in MOCK_USERS and MOCK_USERS[usuario]["senha"] == senha:
                    st.session_state.autenticado = True
                    st.session_state.paciente_nome = MOCK_USERS[usuario]["nome"]
                    st.session_state.paciente_perfil = MOCK_USERS[usuario]["perfil"]
                    st.rerun()
                else:
                    st.error("❌ Credenciais inválidas.")
    
    # Se não autenticado, paramos o código aqui
    st.stop()

# ==========================================
# 1. CONEXÃO COM O RAG (O Cérebro da Dai)
# ==========================================
def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        port="5432",
        database="memoria_vetorial",
        user="admin",
        password="masterkey123"
    )

def setup_dai_memory():
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
    except Exception as e:
        st.error(f"Erro na homeostase do banco de dados: {e}")

setup_dai_memory()

@st.cache_resource
def get_embeddings_model():
    return OllamaEmbeddings(model="nomic-embed-text")

embedder = get_embeddings_model()

def buscar_na_memoria(texto):
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
# 3. INTERFACE DA CLÍNICA
# ==========================================

# Botão de Logout no topo da barra lateral
with st.sidebar:
    termo_usuario = config.get("textos", {}).get("termo_usuario_logado", "Usuário Logado")
    termo_perfil = config.get("textos", {}).get("termo_perfil_acesso", "Perfil de Acesso")
    st.markdown(f"👤 **{termo_usuario}:** {st.session_state.paciente_nome}")
    st.markdown(f"🏷️ **{termo_perfil}:** {st.session_state.paciente_perfil}")
    if st.button("Sair (Logout)"):
        st.session_state.autenticado = False
        st.rerun()

col_chat, col_salas = st.columns([6, 4])

# ----------------------------------------------------
# LADO DIREITO: O CORREDOR E PRONTUÁRIOS
# ----------------------------------------------------
with col_salas:
    titulo_corredor = config.get("textos", {}).get("titulo_corredor", "Corredor de")
    st.markdown(f"### 🚪 {titulo_corredor} {st.session_state.paciente_perfil}")
    
    # Renderiza as portas dependendo do perfil do usuário
    col_s1, col_s2 = st.columns(2)
    
    if st.session_state.paciente_perfil == "Desenvolvimento":
        with col_s1:
            st.success("💻 Dr. Taylor Code (Orquestrador)\n\n`🟢 Online`")
            st.info("⚙️ DevOps (Infra)\n\n`🟢 Online`")
        with col_s2:
            st.warning("🐛 Caçador de Bugs (QA)\n\n`🟢 Online`")
            
    elif st.session_state.paciente_perfil == "Cliente B2B":
        with col_s1:
            st.info("📈 Dr. Qwen (Consultoria)\n\n`🟢 Online`")
        with col_s2:
            st.warning("⚖️ Dr. Saul (Contratos)\n\n`🟢 Online`")
            
    else: # Diretoria / Admin vê tudo
        with col_s1:
            st.info("📈 Dr. Qwen (Finanças)\n\n`🟢 Online`")
            st.error("🔍 Mistral (Investigador)\n\n`🟢 Online`")
        with col_s2:
            st.warning("⚖️ Dr. Saul (Jurídico)\n\n`🟢 Online`")
            st.success("🧠 Llama 3.1 (Maestro)\n\n`🟢 Online`")
    
    st.markdown("---")
    
    # FICHA DO PACIENTE
    titulo_ficha = config.get("textos", {}).get("titulo_ficha", "Ficha do Paciente (Prontuário)")
    label_historico = config.get("textos", {}).get("label_historico", "Histórico Clínico e Queixas Anteriores:")
    valor_historico_padrao = config.get("textos", {}).get("valor_historico_padrao", "Nenhum histórico grave registrado hoje.\\n\\nAguardando triagem...")
    
    st.markdown(f"### 📋 {titulo_ficha}")
    st.text_area(label_historico, value=valor_historico_padrao, height=100, disabled=True)
    
    # RESULTADO / LAUDO FINAL
    titulo_laudo = config.get("textos", {}).get("titulo_laudo", "Laudo de Triagem / Diagnóstico")
    st.markdown(f"### 💊 {titulo_laudo}")
    
    # Checa se existe um laudo guardado na sessao
    laudo_vazio = config.get("textos", {}).get("laudo_vazio", "Nenhum laudo emitido ainda. Fale com a Dai à esquerda.")
    laudo_texto = st.session_state.get("laudo_final", laudo_vazio)
    st.success(laudo_texto)


# ----------------------------------------------------
# LADO ESQUERDO: A RECEPÇÃO (CHAT DA DAI)
# ----------------------------------------------------
with col_chat:
    titulo_chat = config.get("textos", {}).get("titulo_chat", "台 Dai - Triagem e Roteamento")
    subtitulo_chat = config.get("textos", {}).get("subtitulo_chat", "*A Recepção Inteligente baseada em Equilibrio, Memória e Sentido.*")
    cor_primaria = config.get("tema", {}).get("cor_primaria", "#00B4D8")
    cor_secundaria = config.get("tema", {}).get("cor_secundaria", "#00A86B")
    
    st.markdown(f"<h3 style='color: {cor_primaria};'>{titulo_chat}</h3>", unsafe_allow_html=True)
    st.markdown(f"<span style='color: {cor_secundaria};'>{subtitulo_chat}</span>", unsafe_allow_html=True)

    msg_boas_vindas = config.get("textos", {}).get("mensagem_boas_vindas", "Olá, sou a Dai. O que te trouxe até aqui? Como posso te ajudar?")
    if "messages" not in st.session_state or st.session_state.messages[0]["content"] != msg_boas_vindas:
        st.session_state.messages = [{"role": "assistant", "content": msg_boas_vindas}]

    # Carrega a imagem via Base64 (Método à prova de falhas)
    avatar_img = config.get("avatar", {}).get("imagem", "Dai_Avatar.png")
    avatar_emoji = config.get("avatar", {}).get("emoji", "👩🏻‍💼")
    icone_usuario = config.get("avatar", {}).get("icone_usuario", "👤")
    
    if os.path.exists(avatar_img):
        dai_avatar = get_base64_image(avatar_img)
    else:
        dai_avatar = avatar_emoji

    # Renderiza o histórico
    for message in st.session_state.messages:
        avatar = dai_avatar if message["role"] == "assistant" else icone_usuario
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

    # Input do usuário
    dica_input = config.get("textos", {}).get("dica_input_chat", "Diga sua queixa à Dai...")
    if prompt := st.chat_input(dica_input):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar=icone_usuario):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar=dai_avatar):
            if prompt.strip().lower() == "/auditoria":
                st.session_state.laudo_final = "🕵️ Auditoria interna acionada. Imprimindo logs no console."
                st.markdown("🤫 Extraindo registros da mente vetorial...")
                st.session_state.messages.append({"role": "assistant", "content": "🤫 Extraindo registros da mente vetorial..."})
                st.rerun()
            
            resultado, vetor = buscar_na_memoria(prompt)
            distancia = resultado[3] if resultado else 999.0
            
            if resultado and distancia < 0.3:
                destino = resultado[2]
                resposta_dai = f"🔍 Suas métricas são claras. Encaminhando para o **{destino}**..."
                st.session_state.laudo_final = f"✅ Triagem Concluída: Rota identificada para {destino}."
                st.markdown(resposta_dai)
                st.session_state.messages.append({"role": "assistant", "content": resposta_dai})
                st.rerun() # Atualiza a tela para mostrar o laudo na direita
            else:
                resposta_dai = (
                    "Para que eu possa direcionar sua queixa para o corredor correto, preciso que refine seu pedido:\n"
                    "**(i) O QUE** você precisa resolver?\n"
                    "**(ii) COMO** espera que a equipe ajude?\n"
                    "**(iii) POR QUE** isso é uma prioridade agora?"
                )
                st.session_state.laudo_final = "⚠️ Pendente: A Dai solicitou mais clareza ao paciente antes de acionar os especialistas."
                st.markdown(resposta_dai)
                st.session_state.messages.append({"role": "assistant", "content": resposta_dai})
                st.rerun() # Atualiza o painel direito
