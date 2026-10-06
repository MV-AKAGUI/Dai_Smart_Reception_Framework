import streamlit as st
import os
from PIL import Image
import base64
import json
import requests
import io
import time
from datetime import datetime
import qrcode

# ==========================================
# CONFIGURAÇÃO E CARREGAMENTO
# ==========================================
try:
    with open("config_cliente.json", "r", encoding="utf-8") as f:
        config = json.load(f)
except FileNotFoundError:
    config = {}

API_BASE_URL = os.getenv("DAI_API_URL", "http://localhost:8001")

def get_base64_image(image_path: str) -> str:
    """Converte imagem local para data URI base64."""
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return f"data:image/png;base64,{base64.b64encode(img_file.read()).decode()}"
    return ""

def generate_qr_code_base64(data_text: str) -> str:
    """Gera QR Code nítido em formato Base64 para crachás e comprovantes."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=6,
        border=2,
    )
    qr.add_data(data_text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0B192C", back_color="#10B981")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"

# ==========================================
# CONFIGURAÇÃO DE TELA (LAYOUT WIDE)
# ==========================================
page_title = config.get("empresa", {}).get("nome", "Plataforma Central | Dai")
page_icon = config.get("empresa", {}).get("icone", "👩🏻‍💼")
st.set_page_config(page_title=page_title, page_icon=page_icon, layout="wide")

# ==========================================
# CSS PREMIUM (DAISUGI OMOTENASHI & GLASSMORPHISM)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    
    .stApp {
        background-color: #0B192C !important;
        background-image: 
            radial-gradient(circle at 10% 20%, rgba(16, 185, 129, 0.08) 0%, transparent 40%),
            radial-gradient(circle at 90% 80%, rgba(56, 189, 248, 0.08) 0%, transparent 40%),
            linear-gradient(to right, rgba(30, 41, 59, 0.4) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(30, 41, 59, 0.4) 1px, transparent 1px) !important;
        background-size: auto, auto, 24px 24px, 24px 24px !important;
        color: #f1f5f9 !important;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Otimização Mobile-First: Redução de espaço vertical superior */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 100% !important;
    }

    /* Redução de espaço vertical na barra lateral (Sidebar) */
    section[data-testid="stSidebar"] .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 1rem !important;
    }
    section[data-testid="stSidebar"] hr {
        margin-top: 8px !important;
        margin-bottom: 8px !important;
    }

    /* Cards com Glassmorphism */
    div[data-testid="stForm"], div[data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.75) !important;
        backdrop-filter: blur(14px) !important;
        -webkit-backdrop-filter: blur(14px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 16px !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3) !important;
    }

    /* Caixas dos Sistemas Disponíveis na vertical (Kan-sa, Kigyou, HDW) */
    .sistema-card-box {
        background: rgba(15, 23, 42, 0.85);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 14px;
        padding: 14px;
        margin-bottom: 12px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .sistema-card-box:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.45);
    }
    .sistema-kansa {
        border-left: 4px solid #00A86B;
    }
    .sistema-kigyou {
        border-left: 4px solid #00B4D8;
    }
    .sistema-hdw {
        border-left: 4px solid #F59E0B;
    }

    /* Botões Padrão */
    button[kind="primary"], button[data-testid="baseButton-secondaryFormSubmit"] {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        color: white !important;
        border-radius: 10px !important;
        border: none !important;
        font-weight: 700 !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 14px rgba(16, 185, 129, 0.35) !important;
    }
    button[kind="primary"]:hover, button[data-testid="baseButton-secondaryFormSubmit"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(16, 185, 129, 0.5) !important;
    }

    /* Inputs de Texto */
    input, textarea, .stChatInputContainer {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        color: #f1f5f9 !important;
        border-radius: 10px !important;
    }
    input:focus, textarea:focus {
        border-color: #10b981 !important;
        box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.3) !important;
    }

    /* Chat Messages e Balões */
    .stChatMessage {
        background-color: transparent !important;
        margin-bottom: 12px !important;
    }
    div[data-testid="stChatMessageContent"] {
        background: rgba(30, 41, 59, 0.85) !important;
        backdrop-filter: blur(8px) !important;
        border-radius: 14px !important;
        padding: 14px 18px !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        color: #f8fafc !important;
        line-height: 1.6 !important;
    }

    /* Badges Pulsantes */
    .badge-online {
        display: inline-flex;
        align-items: center;
        background: rgba(16, 185, 129, 0.15);
        border: 1px solid #10b981;
        color: #34d399;
        font-size: 0.8rem;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 600;
    }
    .pulse-dot {
        width: 8px;
        height: 8px;
        background-color: #10b981;
        border-radius: 50%;
        display: inline-block;
        margin-right: 6px;
        box-shadow: 0 0 8px #10b981;
    }

    /* Card de Crachá VIP (Tab de Contexto) */
    .vip-ticket-card {
        background: linear-gradient(145deg, rgba(15, 23, 42, 0.95), rgba(30, 41, 59, 0.85));
        border: 2px solid #10b981;
        border-radius: 20px;
        padding: 24px;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5), 0 0 20px rgba(16, 185, 129, 0.2);
        color: #f8fafc;
        margin-bottom: 20px;
    }

    /* Card de Documento Anexo e DW */
    .attachment-card {
        background: rgba(15, 23, 42, 0.8);
        border: 1px solid rgba(56, 189, 248, 0.4);
        border-radius: 12px;
        padding: 12px 16px;
        margin-top: 10px;
        display: flex;
        align-items: center;
        gap: 12px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# INICIALIZAÇÃO DE ESTADO DE SESSÃO
# ==========================================
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "ticket_atual" not in st.session_state:
    st.session_state.ticket_atual = None
if "anfitriao_notificado" not in st.session_state:
    st.session_state.anfitriao_notificado = {}
if "messages" not in st.session_state:
    st.session_state.messages = []
if "quick_prompt_selecionado" not in st.session_state:
    st.session_state.quick_prompt_selecionado = None

# ==========================================
# 0. TELA DE AUTENTICAÇÃO E PORTARIA (LOGIN)
# ==========================================
if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 2.2, 1])
    with col2:
        st.markdown("<div style='text-align: center; margin-top: 20px;'>", unsafe_allow_html=True)
        logo_path = config.get("avatar", {}).get("imagem_login", "login_avatar.jpg")
        if os.path.exists(logo_path):
            st.image(logo_path, width=130)
            
        cor_primaria = config.get("tema", {}).get("cor_primaria", "#10b981")
        titulo_portaria = config.get("textos", {}).get("titulo_portaria", "🔒 Portaria - Acesso Central")
        subtitulo_portaria = config.get("textos", {}).get("subtitulo_portaria", "*Identifique sua Cadeira PAM para acessar a Recepção Inteligente da Dai*")
        
        st.markdown(f"<h2 style='color: {cor_primaria}; margin-bottom: 4px;'>{titulo_portaria}</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='color: #94a3b8; font-size: 0.95rem;'>{subtitulo_portaria}</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Sugestões Rápidas de Cadeiras PAM (Multi-tenant)
        st.markdown("<span style='font-size: 0.85rem; color: #cbd5e1; font-weight: 600;'>⚡ Acesso Rápido por Cadeira PAM:</span>", unsafe_allow_html=True)
        c_chips = st.columns(4)
        perfis_rapidos = [
            ("Controller", "controller"),
            ("Advogado", "advogado"),
            ("Engenheiro", "engenheiro"),
            ("Diretor", "diretor"),
        ]
        c_chips_2 = st.columns(3)
        perfis_rapidos_2 = [
            ("Admin Geral", "admin"),
            ("Visitante/Cliente", "cliente"),
            ("Dev Core (Akagui)", "montanhavermelha@akagui.com")
        ]
        
        perfil_default = ""
        for idx, (label, user_val) in enumerate(perfis_rapidos):
            if c_chips[idx].button(label, key=f"chip_{user_val}", use_container_width=True):
                st.session_state.quick_user = user_val
        for idx, (label, user_val) in enumerate(perfis_rapidos_2):
            if c_chips_2[idx].button(label, key=f"chip_{user_val}", use_container_width=True):
                st.session_state.quick_user = user_val

        default_usuario = st.session_state.get("quick_user", "controller")

        with st.form("login_form"):
            usuario = st.text_input("Cadeira / Usuário PAM", value=default_usuario).lower().strip()
            senha = st.text_input("Senha de Acesso (Padrão: 123)", type="password", value="123")
            submit_btn = st.form_submit_button("Entrar no Lobby da Dai", use_container_width=True)
            
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
                        
                        # Gera o primeiro ticket de recepção para a sessão
                        cod_tkt = f"TKT-DAI-2026-{usuario[:3].upper()}-{int(time.time()) % 10000}"
                        st.session_state.ticket_atual = {
                            "codigo": cod_tkt,
                            "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                            "usuario": st.session_state.paciente_nome,
                            "perfil": st.session_state.paciente_perfil,
                            "unidades": st.session_state.clientes_acesso,
                            "destino": "Lobby Central (Aguardando Roteamento)",
                            "status": "Check-in Efetuado",
                            "sla": "< 5 min (Imediato)",
                            "qr_b64": generate_qr_code_base64(f"DAISUGI-VERIFIED:{cod_tkt}:{usuario}")
                        }
                        st.rerun()
                    else:
                        st.error("❌ Credenciais inválidas.")
                except requests.exceptions.ConnectionError:
                    st.error(f"❌ Erro de conexão: O Backend da Dai não respondeu em {API_BASE_URL}.")
    
    st.stop()

# ==========================================
# 1. BARRA LATERAL: SESSÃO, PERFIL E MULTI-TENANT
# ==========================================
def checar_status_api(url: str):
    try:
        r = requests.get(f"{url}/health", timeout=2)
        if r.status_code == 200:
            return True, r.json()
    except Exception:
        pass
    return False, {}

with st.sidebar:
    st.markdown("<div style='text-align: center; margin-bottom: 8px;'>", unsafe_allow_html=True)
    avatar_lobby = config.get("avatar", {}).get("imagem_lobby", "lobby_avatar.jpg")
    if os.path.exists(avatar_lobby):
        st.image(avatar_lobby, width=190)
    st.markdown("<h3 style='margin-top: 6px; margin-bottom: 4px;'>台 Dai Smart Reception</h3></div>", unsafe_allow_html=True)
    
    api_online, health_data = checar_status_api(API_BASE_URL)
    if api_online:
        st.markdown("<div class='badge-online'><span class='pulse-dot'></span> Dai Online (Recepção Ativa)</div>", unsafe_allow_html=True)
    else:
        st.markdown("<span style='color: #ef4444; font-weight: 600;'>🔴 Backend Desconectado</span>", unsafe_allow_html=True)

    st.markdown("---")
    termo_usuario = config.get("textos", {}).get("termo_usuario_logado", "Usuário Logado")
    termo_perfil = config.get("textos", {}).get("termo_perfil_acesso", "Perfil de Acesso")
    st.markdown(f"👤 **{termo_usuario}:** {st.session_state.paciente_nome}")
    st.markdown(f"🏷️ **{termo_perfil}:** `{st.session_state.paciente_perfil.upper()}`")
    
    # Exibição dos Clientes/Unidades Autorizados (Multi-tenant)
    st.markdown("🏢 **Unidades / Tenants Autorizados:**")
    unidades = st.session_state.get("clientes_acesso", [])
    if unidades:
        for u in unidades:
            st.markdown(f"- <span style='color: #38bdf8; font-weight: 600;'>{u.capitalize()}</span>", unsafe_allow_html=True)
    else:
        st.caption("Acesso Global Não Restrito")

    if st.session_state.ticket_atual:
        st.markdown("---")
        st.caption("🎫 **Ticket de Atendimento Ativo:**")
        st.code(st.session_state.ticket_atual["codigo"], language="text")

    st.markdown("---")
    if st.button("🚪 Sair do Lobby (Logout)", use_container_width=True):
        st.session_state.autenticado = False
        st.session_state.ticket_atual = None
        st.session_state.messages = []
        st.rerun()

# ==========================================
# 2. ABAS PRINCIPAIS (LOBBY, SALAS E CONTEXTO)
# ==========================================
tab_chat, tab_ficha = st.tabs([
    "💬 Hall de entrada (Recepção)",
    "📋 Seu Contexto (Ingresso/Laudo)"
])

# ----------------------------------------------------
# TAB 1: O CHAT INTUITIVO DA DAI (ESTILO LLM)
# ----------------------------------------------------
with tab_chat:
    cor_primaria = config.get("tema", {}).get("cor_primaria", "#00A86B")
    titulo_chat = config.get("textos", {}).get("titulo_chat", "台 Dai - Lobby Central")
    subtitulo_chat = config.get("textos", {}).get("subtitulo_chat", "*Acolhimento empático, triagem instantânea e resolutividade corporativa.*")
    
    col_chat, col_sistemas = st.columns([2.7, 1.3], gap="medium")
    
    with col_sistemas:
        st.markdown("<h4 style='color: #00A86B; margin-top: 4px; margin-bottom: 12px; font-weight: 700;'>🏛️ Sistemas Disponíveis</h4>", unsafe_allow_html=True)
        
        # Caixa 1: Kan-sa
        st.markdown("""
        <div class='sistema-card-box sistema-kansa'>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <strong style='font-size: 1.05rem; color: #f8fafc;'>監査 Kan-sa</strong>
                <span style='background: rgba(0, 168, 107, 0.2); color: #34d399; font-size: 0.72rem; padding: 2px 8px; border-radius: 12px; font-weight: 700;'>🟢 Online</span>
            </div>
            <p style='color: #94a3b8; font-size: 0.8rem; margin: 6px 0 10px 0; line-height: 1.4;'>
                Auditoria Pericial Contábil Forense, DFP & Reconstituição Histórica do Endividamento.
            </p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Acessar Kan-sa ➔", key="btn_goto_kansa", use_container_width=True):
            st.session_state.quick_prompt_selecionado = "Preciso auditar o endividamento e acessar a esteira pericial do Kan-sa."
            st.rerun()

        # Caixa 2: Kigyou
        st.markdown("""
        <div class='sistema-card-box sistema-kigyou' style='margin-top: 14px;'>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <strong style='font-size: 1.05rem; color: #f8fafc;'>企業 Kigyou</strong>
                <span style='background: rgba(0, 180, 216, 0.2); color: #38bdf8; font-size: 0.72rem; padding: 2px 8px; border-radius: 12px; font-weight: 700;'>🔵 Disponível</span>
            </div>
            <p style='color: #94a3b8; font-size: 0.8rem; margin: 6px 0 10px 0; line-height: 1.4;'>
                Metabolismo Financeiro, Governança & Gestão de Ativos Corporativos.
            </p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Acessar Kigyou", key="btn_goto_kigyou", use_container_width=True):
            st.session_state.quick_prompt_selecionado = "Gostaria de consultar as diretrizes de governança e metabolismo no Kigyou."
            st.rerun()

        # Caixa 3: HDW
        st.markdown("""
        <div class='sistema-card-box sistema-hdw' style='margin-top: 14px;'>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <strong style='font-size: 1.05rem; color: #f8fafc;'>📂 HDW</strong>
                <span style='background: rgba(245, 158, 11, 0.2); color: #fbbf24; font-size: 0.72rem; padding: 2px 8px; border-radius: 12px; font-weight: 700;'>📁 Transitório</span>
            </div>
            <p style='color: #94a3b8; font-size: 0.8rem; margin: 6px 0 10px 0; line-height: 1.4;'>
                Repositório Documental em Nuvem (SharePoint SUGOI HUB GED) & Custódia Digital.
            </p>
            <a href='https://sugoiconstrutora.sharepoint.com/:f:/r/sites/DataHubDocumentalSUGOI/Documentos%20Compartilhados/SUGOI_HUB_GED/HUB_EXTERNO/00_REPOSIT%C3%93RIO/HDW-TRANSIT%C3%93RIO?d=waf9ad30eee2a4df3a15e018b4c2215f5&csf=1&web=1&e=DXEV88' target='_blank' style='display: block; text-align: center; background: rgba(245, 158, 11, 0.2); border: 1px solid #f59e0b; color: #fbbf24; padding: 8px 12px; border-radius: 8px; text-decoration: none; font-size: 0.8rem; font-weight: 700; margin-top: 6px;'>Abrir Pasta HDW ↗</a>
        </div>
        """, unsafe_allow_html=True)

    with col_chat:
        st.markdown(f"<h3 style='color: {cor_primaria}; margin-bottom: 2px;'>{titulo_chat}</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='color: #94a3b8; font-size: 0.95rem; margin-bottom: 12px;'>{subtitulo_chat}</p>", unsafe_allow_html=True)

    # Mensagem inicial de boas-vindas da Dai
    msg_boas_vindas = config.get("textos", {}).get("mensagem_boas_vindas", "Olá, sou a Dai, agente de triagem do Daisugi. Posso te ajudar diretamente, ou, te direcionar a alguma outra sala, me diga o que precisa.")
    if not st.session_state.messages:
        st.session_state.messages = [{
            "role": "assistant",
            "content": msg_boas_vindas,
            "arquivo_anexo": None,
            "link_dw": None,
            "codigo_rastreamento": None
        }]

    # Quick Prompts / Sugestões de Atendimento
    st.markdown("<span style='font-size: 0.85rem; color: #94a3b8; font-weight: 600;'>💡 Sugestões de Atendimento Rápido:</span>", unsafe_allow_html=True)
    qp1, qp2, qp3, qp4 = st.columns(4)
    if qp1.button("💼 Visita Executiva", use_container_width=True):
        st.session_state.quick_prompt_selecionado = "Vim para uma reunião com a Diretoria Financeira para tratar sobre aprovação de novos investimentos."
    if qp2.button("📄 Entregar CCB / Fatura", use_container_width=True):
        st.session_state.quick_prompt_selecionado = "Preciso entregar o borderô da CCB e nota fiscal de medição de obras para validação do Controller."
    if qp3.button("🔍 Consulta no DW", use_container_width=True):
        st.session_state.quick_prompt_selecionado = "Gostaria de localizar o relatório de auditoria e contrato no Data Warehouse do cliente."
    if qp4.button("⚡ Prestador de Serviço", use_container_width=True):
        st.session_state.quick_prompt_selecionado = "Sou prestador de serviço de engenharia civil e necessito de credenciamento para inspeção de segurança."

    avatar_img = config.get("avatar", {}).get("imagem_lobby", "lobby_avatar.jpg")
    icone_usuario = config.get("avatar", {}).get("icone_usuario", "👤")
    dai_avatar = get_base64_image(avatar_img) if os.path.exists(avatar_img) else "👩🏻‍💼"

    # Renderização do histórico de mensagens estilo LLM
    for message in st.session_state.messages:
        av = dai_avatar if message["role"] == "assistant" else icone_usuario
        with st.chat_message(message["role"], avatar=av):
            st.markdown(message["content"])
            
            # Se a mensagem contiver link de documento no Data Warehouse
            if message.get("link_dw"):
                dw = message["link_dw"]
                st.markdown(f"""
                <div class='attachment-card'>
                    <span style='font-size: 1.5rem;'>🏢</span>
                    <div style='flex: 1;'>
                        <div style='font-weight: 700; color: #38bdf8;'>{dw.get('titulo', 'Documento no Data Warehouse')}</div>
                        <div style='font-size: 0.75rem; color: #94a3b8;'>Repositório: {dw.get('repositorio', 'DW Corporativo')} | Hash: <code>{dw.get('hash', '')[:16]}...</code></div>
                    </div>
                    <a href='{dw.get('url', '#')}' target='_blank' style='background: #0284c7; color: white; padding: 6px 12px; border-radius: 8px; text-decoration: none; font-size: 0.8rem; font-weight: 600;'>Acessar DW</a>
                </div>
                """, unsafe_allow_html=True)
                
            # Se a mensagem contiver arquivo anexo
            if message.get("arquivo_anexo"):
                anexo = message["arquivo_anexo"]
                st.markdown(f"""
                <div class='attachment-card' style='border-color: rgba(16, 185, 129, 0.4);'>
                    <span style='font-size: 1.5rem;'>📑</span>
                    <div style='flex: 1;'>
                        <div style='font-weight: 700; color: #34d399;'>{anexo.get('nome', 'Comprovante_Atendimento.pdf')}</div>
                        <div style='font-size: 0.75rem; color: #94a3b8;'>Formato: {anexo.get('tipo', 'PDF')} | Tamanho: {anexo.get('tamanho', '142 KB')} | {anexo.get('status', 'Emitido')}</div>
                    </div>
                    <span style='background: #059669; color: white; padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: 600;'>Gerado ✅</span>
                </div>
                """, unsafe_allow_html=True)

    # Disparo automático se quick prompt foi selecionado
    prompt_usuario = None
    if st.session_state.quick_prompt_selecionado:
        prompt_usuario = st.session_state.quick_prompt_selecionado
        st.session_state.quick_prompt_selecionado = None
    else:
        dica_input = config.get("textos", {}).get("dica_input_chat", "Descreva sua demanda para a Dai...")
        prompt_input = st.chat_input(dica_input)
        if prompt_input:
            prompt_usuario = prompt_input

    if prompt_usuario:
        # Registra a mensagem do usuário
        st.session_state.messages.append({
            "role": "user",
            "content": prompt_usuario,
            "arquivo_anexo": None,
            "link_dw": None
        })
        st.session_state.ultima_queixa = prompt_usuario
        
        with st.chat_message("user", avatar=icone_usuario):
            st.markdown(prompt_usuario)

        with st.chat_message("assistant", avatar=dai_avatar):
            with st.spinner("台 Dai está consultando as regras de acolhimento e o diretório..."):
                try:
                    res = requests.post(
                        f"{API_BASE_URL}/chat/triage",
                        json={
                            "texto_usuario": prompt_usuario,
                            "id_usuario": st.session_state.get("paciente_id", 1)
                        },
                        timeout=5
                    )
                    if res.status_code == 200:
                        dados = res.json()
                        st.session_state.laudo_final = dados.get("laudo_final", "✅ Triagem Concluída.")
                        
                        texto_resposta = dados.get("resposta_dai", "")
                        if dados.get("cache_hit"):
                            texto_resposta = f"⚡ **[Atendimento Expresso — Cache O(1)]**\n\n{texto_resposta}"
                        
                        destino = dados.get("destino")
                        if destino:
                            st.session_state.ultimo_destino = destino
                            
                        cod_rastreio = dados.get("codigo_rastreamento") or st.session_state.ticket_atual.get("codigo")
                        anexo = dados.get("arquivo_anexo")
                        link_dw = dados.get("link_documento_dw")
                        
                        # Atualiza o ticket atual na sessão
                        if st.session_state.ticket_atual:
                            st.session_state.ticket_atual["destino"] = destino or st.session_state.ticket_atual["destino"]
                            st.session_state.ticket_atual["status"] = "Roteamento Definido"
                            if cod_rastreio:
                                st.session_state.ticket_atual["codigo"] = cod_rastreio
                                st.session_state.ticket_atual["qr_b64"] = generate_qr_code_base64(f"DAISUGI-VERIFIED:{cod_rastreio}:{destino}")

                        # Armazena na sessão e recarrega para renderização impecável
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": texto_resposta,
                            "arquivo_anexo": anexo,
                            "link_dw": link_dw,
                            "codigo_rastreamento": cod_rastreio
                        })
                        st.rerun()
                    else:
                        st.error("❌ Erro interno no Cérebro da Dai.")
                except requests.exceptions.ConnectionError:
                    st.error(f"❌ Conexão perdida com o Backend da Dai em {API_BASE_URL}.")

# ----------------------------------------------------
# TAB 3: CONTEXTO, LAUDO E COMPROVANTE VIP (QR CODE)
# ----------------------------------------------------
with tab_ficha:
    st.markdown("### 📋 Seu Contexto de Atendimento & Crachá VIP")
    st.markdown("<p style='color: #94a3b8; font-size: 0.9rem;'>Comprovante oficial de encaminhamento com rastreabilidade criptográfica e validação Kan-sa.</p>", unsafe_allow_html=True)
    
    tkt = st.session_state.ticket_atual
    if tkt:
        col_t1, col_t2 = st.columns([2.5, 1.2])
        with col_t1:
            st.markdown(f"""
            <div class='vip-ticket-card'>
                <div style='display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.15); padding-bottom: 10px; margin-bottom: 14px;'>
                    <div>
                        <span style='font-size: 0.75rem; letter-spacing: 1px; text-transform: uppercase; color: #10b981; font-weight: 800;'>Daisugi Smart Reception Pass</span>
                        <h3 style='margin: 0; color: #ffffff;'>🎫 {tkt.get('codigo')}</h3>
                    </div>
                    <span style='background: #10b981; color: #0B192C; font-weight: 800; font-size: 0.75rem; padding: 4px 10px; border-radius: 6px;'>{tkt.get('status')}</span>
                </div>
                <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 12px; font-size: 0.9rem;'>
                    <div><span style='color: #94a3b8;'>Visitante / Usuário:</span><br/><strong>{tkt.get('usuario')}</strong></div>
                    <div><span style='color: #94a3b8;'>Cadeira PAM:</span><br/><strong>{tkt.get('perfil').upper()}</strong></div>
                    <div><span style='color: #94a3b8;'>Sala Destino:</span><br/><strong style='color: #38bdf8;'>{tkt.get('destino')}</strong></div>
                    <div><span style='color: #94a3b8;'>SLA Estimado:</span><br/><strong>{tkt.get('sla')}</strong></div>
                    <div><span style='color: #94a3b8;'>Check-in Realizado:</span><br/><strong>{tkt.get('timestamp')}</strong></div>
                    <div><span style='color: #94a3b8;'>Auditoria:</span><br/><strong style='color: #34d399;'>Kan-sa Compliant ✅</strong></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        with col_t2:
            st.markdown("<div style='text-align: center; background: rgba(15,23,42,0.85); border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; padding: 16px;'>", unsafe_allow_html=True)
            st.markdown("<span style='font-size: 0.8rem; color: #cbd5e1; font-weight: 700;'>QR Code de Acesso Rápido</span>", unsafe_allow_html=True)
            if tkt.get("qr_b64"):
                st.markdown(f"<img src='{tkt.get('qr_b64')}' style='border-radius: 12px; margin: 10px 0; width: 140px;'/>", unsafe_allow_html=True)
            st.caption("Apresente na catraca física ou ao anfitrião da sala.")
            st.markdown("</div>", unsafe_allow_html=True)

    # Laudo Técnico da Triagem
    st.markdown("---")
    titulo_laudo = config.get("textos", {}).get("titulo_laudo", "Laudo Técnico de Triagem & Roteamento")
    st.markdown(f"### 💊 {titulo_laudo}")
    laudo_vazio = config.get("textos", {}).get("laudo_vazio", "Nenhum laudo emitido ainda. Dialogue com a Dai no Lobby.")
    st.info(st.session_state.get("laudo_final", laudo_vazio))

    # Formulário de Retroalimentação & Aprendizado da Dai
    st.markdown("---")
    st.markdown("### 🧠 Retroalimentação & Aprendizado da Dai (`/triage/learn`)")
    st.caption("Quando um especialista conclui a demanda, esta solução vira sinapse no banco vetorial.")
    
    with st.form("learn_form"):
        queixa_orig = st.text_input("Demanda Original do Usuário", value=st.session_state.get("ultima_queixa", ""))
        sala_destino = st.text_input("Sala / Especialidade Final", value=st.session_state.get("ultimo_destino", "Lobby Central"))
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
