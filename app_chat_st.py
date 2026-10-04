import streamlit as st
import os
from PIL import Image
import base64
import json
import requests

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

# INJEÇÃO DE CSS PREMIUM (BRAND DAISUGI)
st.markdown("""
<style>
    /* Fontes Globais */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"]  {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    
    /* Fundo Escuro Premium */
    .stApp {
        background-color: #0B192C !important;
        background-image: 
            linear-gradient(to right, rgba(30, 41, 59, 0.6) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(30, 41, 59, 0.6) 1px, transparent 1px) !important;
        background-size: 20px 20px !important;
        color: #f1f5f9 !important;
    }

    /* Ocultar menus padrões do Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Cards e Elementos com Glassmorphism */
    div[data-testid="stForm"], div[data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.7) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 16px !important;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1) !important;
        color: #f1f5f9 !important;
    }

    /* Textos Base */
    h1, h2, h3, h4, h5, h6, p, span, div {
        color: #f1f5f9;
    }

    /* Botões */
    button[kind="primary"], button[data-testid="baseButton-secondaryFormSubmit"] {
        background-color: #10b981 !important; /* Emerald 500 */
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: 700 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 10px rgba(16, 185, 129, 0.3) !important;
    }
    button[kind="primary"]:hover, button[data-testid="baseButton-secondaryFormSubmit"]:hover {
        background-color: #059669 !important; /* Emerald 600 */
        transform: translateY(-2px) !important;
    }

    /* Inputs de Texto */
    input, textarea, .stChatInputContainer {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        color: #f1f5f9 !important;
        border-radius: 8px !important;
    }
    input:focus, textarea:focus {
        border-color: #10b981 !important;
        box-shadow: 0 0 0 1px #10b981 !important;
    }

    /* Alertas Sucesso/Aviso/Info */
    .stAlert {
        border-radius: 12px !important;
        border: none !important;
    }
    div[data-testid="stNotificationSuccess"], div[data-testid="stAlert"] > div:has(svg[aria-label="success"]) {
        background-color: rgba(16, 185, 129, 0.15) !important;
        border-left: 4px solid #10b981 !important;
        color: #d1fae5 !important;
    }
    div[data-testid="stNotificationWarning"], div[data-testid="stAlert"] > div:has(svg[aria-label="warning"]) {
        background-color: rgba(245, 158, 11, 0.15) !important;
        border-left: 4px solid #f59e0b !important;
        color: #fef3c7 !important;
    }
    div[data-testid="stNotificationInfo"], div[data-testid="stAlert"] > div:has(svg[aria-label="info"]) {
        background-color: rgba(56, 189, 248, 0.15) !important;
        border-left: 4px solid #38bdf8 !important;
        color: #e0f2fe !important;
    }
    
    /* Área de Chat (Dai) */
    .stChatMessage {
        background-color: transparent !important;
    }
    div[data-testid="stChatMessageContent"] {
        background-color: #1e293b !important;
        border-radius: 12px !important;
        padding: 12px 16px !important;
        border: 1px solid #334155 !important;
    }
</style>
""", unsafe_allow_html=True)


# ==========================================
# 0. TELA DE AUTENTICAÇÃO (LOGIN)
# ==========================================
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

API_BASE_URL = "http://localhost:8000"

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
                try:
                    res = requests.post(f"{API_BASE_URL}/auth/login", json={"usuario": usuario, "senha": senha})
                    if res.status_code == 200:
                        dados = res.json()
                        st.session_state.autenticado = True
                        st.session_state.paciente_nome = dados["nome"]
                        st.session_state.paciente_perfil = dados["perfil"]
                        st.rerun()
                    else:
                        st.error("❌ Credenciais inválidas.")
                except requests.exceptions.ConnectionError:
                    st.error("❌ Erro: O Backend da Dai não está rodando. Inicie a API primeiro.")
    
    # Se não autenticado, paramos o código aqui
    st.stop()

# ==========================================
# 1. COMUNICAÇÃO COM O CÉREBRO DA DAI (API)
# ==========================================
# Toda a lógica de RAG, Embeddings e PostgreSQL foi migrada para o api_backend.py

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
            
            try:
                # Chama a API de Triagem
                res = requests.post(f"{API_BASE_URL}/chat/triage", json={"texto_usuario": prompt})
                if res.status_code == 200:
                    dados = res.json()
                    st.session_state.laudo_final = dados["laudo_final"]
                    st.markdown(dados["resposta_dai"])
                    st.session_state.messages.append({"role": "assistant", "content": dados["resposta_dai"]})
                    st.rerun() # Atualiza a tela para mostrar o laudo na direita
                else:
                    st.error("❌ Erro interno na Mente Vetorial da Dai.")
            except requests.exceptions.ConnectionError:
                st.error("❌ Conexão perdida com o Backend da Dai.")
