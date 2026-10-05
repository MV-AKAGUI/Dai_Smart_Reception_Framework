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

API_BASE_URL = os.getenv("DAI_API_URL", "http://localhost:8001")

if not st.session_state.autenticado:
    # Mostramos o Avatar na portaria também para dar boas-vindas
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        logo_path = config.get("avatar", {}).get("imagem_login", "Dai_Avatar_Brand.jpg")
        if os.path.exists(logo_path):
            st.image(logo_path, width=150)
            
        cor_primaria = config.get("tema", {}).get("cor_primaria", "#00B4D8")
        titulo_portaria = config.get("textos", {}).get("titulo_portaria", "🔒 Portaria - Daisugi")
        subtitulo_portaria = config.get("textos", {}).get("subtitulo_portaria", "*Por favor, identifique-se antes de acessar nosso Lobby*")
        
        st.markdown(f"<h1 style='color: {cor_primaria};'>{titulo_portaria}</h1>", unsafe_allow_html=True)
        st.markdown(f"{subtitulo_portaria}")
        
        with st.form("login_form"):
            usuario = st.text_input("Cadeira / Usuário PAM (Ex: controller, advogado, engenheiro, diretor, admin, cliente)").lower()
            senha = st.text_input("Senha (Dica: 123)", type="password")
            submit_btn = st.form_submit_button("Entrar no Lobby")
            
            if submit_btn:
                try:
                    res = requests.post(f"{API_BASE_URL}/auth/login", json={"usuario": usuario, "senha": senha}, timeout=5)
                    if res.status_code == 200:
                        dados = res.json()
                        st.session_state.autenticado = True
                        st.session_state.paciente_id = dados.get("id_usuario", 1)
                        st.session_state.paciente_nome = dados.get("nome", "Usuário")
                        st.session_state.paciente_perfil = dados.get("perfil", "Desconhecido")
                        st.session_state.salas_liberadas = dados.get("salas_liberadas", [])
                        st.session_state.clientes_acesso = dados.get("clientes_acesso", [])
                        st.session_state.token_jwt = dados.get("token_jwt", "")
                        st.rerun()
                    else:
                        st.error("❌ Credenciais inválidas.")
                except requests.exceptions.ConnectionError:
                    st.error(f"❌ Erro de conexão: O Backend da Dai não respondeu em {API_BASE_URL}.")
    
    # Se não autenticado, paramos o código aqui
    st.stop()

# ==========================================
# 1. COMUNICAÇÃO COM O CÉREBRO DA DAI (API)
# ==========================================
# Toda a lógica de RAG, Embeddings e PostgreSQL foi migrada para o api_backend.py

# ==========================================
# 3. INTERFACE DA CLÍNICA
# ==========================================

# Verificação de Saúde da API para feedback visual na Barra Lateral
def checar_status_api(url: str):
    try:
        r = requests.get(f"{url}/health", timeout=2)
        if r.status_code == 200:
            return True, r.json()
    except Exception:
        pass
    return False, {}

# Barra Lateral: Identidade, Perfil e Status do Sistema
with st.sidebar:
    api_online, health_data = checar_status_api(API_BASE_URL)
    if api_online:
        st.success("🟢 **API Dai:** Conectada")
    else:
        st.error("🔴 **API Dai:** Desconectada")

    termo_usuario = config.get("textos", {}).get("termo_usuario_logado", "Usuário Logado")
    termo_perfil = config.get("textos", {}).get("termo_perfil_acesso", "Perfil de Acesso")
    st.markdown(f"👤 **{termo_usuario}:** {st.session_state.paciente_nome}")
    st.markdown(f"🏷️ **{termo_perfil}:** {st.session_state.paciente_perfil}")
    if st.button("Sair (Logout)"):
        st.session_state.autenticado = False
        st.rerun()

# Mobile-First: Substituição de Colunas por Abas (Tabs) interativas
tab_chat, tab_salas, tab_ficha = st.tabs(["💬 Lobby (Recepção)", "🚪 Salas e Corredores", "📋 Seu Contexto (Ticket/Laudo)"])

# ----------------------------------------------------
# TAB 1: A RECEPÇÃO (CHAT DA DAI)
# ----------------------------------------------------
with tab_chat:
    titulo_chat = config.get("textos", {}).get("titulo_chat", "台 Dai - Triagem e Roteamento")
    subtitulo_chat = config.get("textos", {}).get("subtitulo_chat", "*A Recepção Inteligente baseada em Equilibrio, Memória e Sentido.*")
    cor_primaria = config.get("tema", {}).get("cor_primaria", "#00B4D8")
    cor_secundaria = config.get("tema", {}).get("cor_secundaria", "#00A86B")
    
    st.markdown(f"<h3 style='color: {cor_primaria};'>{titulo_chat}</h3>", unsafe_allow_html=True)
    st.markdown(f"<span style='color: {cor_secundaria};'>{subtitulo_chat}</span>", unsafe_allow_html=True)

    msg_boas_vindas = config.get("textos", {}).get("mensagem_boas_vindas", "Olá, sou a Dai. O que te trouxe até aqui? Como posso te ajudar?")
    if "messages" not in st.session_state or st.session_state.messages[0]["content"] != msg_boas_vindas:
        st.session_state.messages = [{"role": "assistant", "content": msg_boas_vindas}]

    # Carrega o avatar via Base64
    avatar_img = config.get("avatar", {}).get("imagem_lobby", "Dai_Avatar.png")
    avatar_emoji = config.get("avatar", {}).get("emoji", "👩🏻‍💼")
    icone_usuario = config.get("avatar", {}).get("icone_usuario", "👤")
    
    if os.path.exists(avatar_img):
        dai_avatar = get_base64_image(avatar_img)
    else:
        dai_avatar = avatar_emoji

    # Renderiza o histórico de mensagens
    for message in st.session_state.messages:
        avatar = dai_avatar if message["role"] == "assistant" else icone_usuario
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

    # Input do usuário
    dica_input = config.get("textos", {}).get("dica_input_chat", "Diga sua queixa à Dai...")
    if prompt := st.chat_input(dica_input):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.ultima_queixa = prompt
        with st.chat_message("user", avatar=icone_usuario):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar=dai_avatar):
            try:
                res = requests.post(f"{API_BASE_URL}/chat/triage", json={
                    "texto_usuario": prompt,
                    "id_usuario": st.session_state.get("paciente_id", 1)
                }, timeout=5)
                if res.status_code == 200:
                    dados = res.json()
                    st.session_state.laudo_final = dados["laudo_final"]
                    
                    texto_resposta = dados["resposta_dai"]
                    if dados.get("cache_hit"):
                        texto_resposta = f"⚡ **[Cache Redis O(1) Hit]**\n\n{texto_resposta}"
                    
                    if dados.get("destino"):
                        st.session_state.ultimo_destino = dados["destino"]

                    st.markdown(texto_resposta)
                    st.session_state.messages.append({"role": "assistant", "content": texto_resposta})
                    st.rerun()
                else:
                    st.error("❌ Erro interno na Mente Vetorial da Dai.")
            except requests.exceptions.ConnectionError:
                st.error(f"❌ Conexão perdida com o Backend da Dai em {API_BASE_URL}.")

# ----------------------------------------------------
# TAB 2: O CORREDOR E SALAS
# ----------------------------------------------------
with tab_salas:
    titulo_corredor = config.get("textos", {}).get("titulo_corredor", "Corredor de")
    st.markdown(f"### 🚪 {titulo_corredor} {st.session_state.paciente_perfil}")
    
    col_s1, col_s2 = st.columns(2)
    salas = st.session_state.get("salas_liberadas", [])
    
    if not salas:
        st.warning("Nenhuma sala liberada para este perfil.")
    else:
        cores = [st.info, st.warning, st.success, st.error]
        for i, sala in enumerate(salas):
            col = col_s1 if i % 2 == 0 else col_s2
            with col:
                nome_sala = sala.get('nome', sala) if isinstance(sala, dict) else str(sala)
                funcao_sala = sala.get('funcao', '') if isinstance(sala, dict) else ''
                cores[i % len(cores)](f"🚪 **{nome_sala}**\n\n_{funcao_sala}_\n\n`🟢 Online`")

    # Módulo Especial de Quarentena para Operadores / Admin (Integração Kan-sa)
    if st.session_state.paciente_perfil == "admin":
        st.markdown("---")
        st.markdown("### 🛡️ Painel de Quarentena & Desacoplamento Assíncrono (Kan-sa / Hudson)")
        st.caption("Acesso restrito: Validação de documentos em lote sem travamento de tela (HTTP 202 Accepted).")
        
        with st.form("quarentena_form"):
            hash_doc = st.text_input("Hash SHA-256 do Documento / CCB", value="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
            decisao = st.selectbox("Parecer do Operador", ["Aprovar e Liberar para Kan-sa", "Rejeitar Documento"])
            submit_quarentena = st.form_submit_button("Despachar Auditoria em Background")
            
            if submit_quarentena:
                aprovado_bool = "Aprovar" in decisao
                headers = {"Authorization": f"Bearer {st.session_state.get('token_jwt', '')}"}
                try:
                    res = requests.post(
                        f"{API_BASE_URL}/api/quarentena/validar",
                        headers=headers,
                        json={"hash_id_documento": hash_doc, "aprovado": aprovado_bool},
                        timeout=5
                    )
                    if res.status_code == 202:
                        retorno = res.json()
                        st.success(f"✅ **HTTP 202 Accepted**: {retorno.get('message')}")
                        st.info(f"🆔 **Hash em processamento:** `{retorno.get('hash_processado')}`")
                    else:
                        st.error(f"❌ Erro {res.status_code}: {res.text}")
                except Exception as e:
                    st.error(f"❌ Falha de comunicação com a API: {e}")

# ----------------------------------------------------
# TAB 3: FICHA E LAUDO FINAL
# ----------------------------------------------------
with tab_ficha:
    titulo_ficha = config.get("textos", {}).get("titulo_ficha", "Contexto do Usuário (Ticket)")
    label_historico = config.get("textos", {}).get("label_historico", "Histórico de Interações e Demandas Anteriores:")
    valor_historico_padrao = config.get("textos", {}).get("valor_historico_padrao", "Nenhuma demanda pendente registrada.\n\nAguardando triagem no Lobby...")
    
    st.markdown(f"### 📋 {titulo_ficha}")
    st.text_area(label_historico, value=valor_historico_padrao, height=100, disabled=True)
    
    st.markdown("---")
    
    titulo_laudo = config.get("textos", {}).get("titulo_laudo", "Laudo de Triagem / Roteamento")
    st.markdown(f"### 💊 {titulo_laudo}")
    
    laudo_vazio = config.get("textos", {}).get("laudo_vazio", "Nenhum roteamento emitido ainda. Fale com a Dai na aba do Lobby.")
    laudo_texto = st.session_state.get("laudo_final", laudo_vazio)
    st.success(laudo_texto)

    # Formulário de Aprendizado Contínuo para Especialistas
    st.markdown("---")
    st.markdown("### 🧠 Retroalimentação & Aprendizado da Dai (`/triage/learn`)")
    st.caption("Quando um especialista conclui a demanda, esta solução vira sinapse no banco vetorial.")
    
    with st.form("learn_form"):
        queixa_orig = st.text_input("Queixa Original do Usuário", value=st.session_state.get("ultima_queixa", ""))
        sala_destino = st.text_input("Sala / Especialidade Final", value=st.session_state.get("ultimo_destino", "Sala Suporte"))
        resolucao_esp = st.text_area("Resolução do Especialista (Prontuário)", placeholder="Descreva como o problema foi solucionado com exatidão...")
        is_global = st.checkbox("Tornar Conhecimento Global (Beneficia todos os clientes)", value=False)
        cliente_alvo = st.text_input("Identificador do Cliente", value="controladoria")
        
        btn_ensinar = st.form_submit_button("Gravar na Memória da Dai")
        if btn_ensinar:
            if not resolucao_esp or not queixa_orig:
                st.warning("Preencha a queixa e a resolução para registrar a evolução.")
            else:
                try:
                    res_learn = requests.post(
                        f"{API_BASE_URL}/triage/learn",
                        json={
                            "texto_usuario": queixa_orig,
                            "destino_final": sala_destino,
                            "cliente_destino": cliente_alvo,
                            "resolucao_especialista": resolucao_esp,
                            "is_global": is_global
                        },
                        timeout=5
                    )
                    if res_learn.status_code == 200:
                        st.success(res_learn.json().get("mensagem", "Evolução gravada!"))
                    else:
                        st.error(f"❌ Erro ao salvar aprendizado: {res_learn.text}")
                except Exception as e:
                    st.error(f"❌ Falha de conexão: {e}")

