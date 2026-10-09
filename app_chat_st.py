import streamlit as st
import os
from PIL import Image
import base64
import json
import requests
import io
import time
import subprocess
from datetime import datetime
try:
    import qrcode
except ImportError:
    qrcode = None
try:
    import pandas as pd
except ImportError:
    pd = None

# ==========================================
# CONFIGURAÇÃO E CARREGAMENTO
# ==========================================
try:
    with open("config_cliente.json", "r", encoding="utf-8") as f:
        config = json.load(f)
except FileNotFoundError:
    config = {}

API_BASE_URL = os.getenv("DAI_API_URL", "http://localhost:8001")

DIR_HDW_TRANSITORIO = r"H:\Drives compartilhados\APLICAÇÕES - SUGOI-SA\02_APLICAÇÕES_E_SISTEMAS\DAISUGI\02_Daisugi_kan-sa\DATA_ROOM\HDW_TRANSITORIO\01_CONTROLADORIA_E_FINANCAS\M4_CONTROLE_ENDIVIDAMENTO"
SHAREPOINT_URL_HDW = "https://sugoiconstrutora.sharepoint.com/:f:/r/sites/DataHubDocumentalSUGOI/Documentos%20Compartilhados/SUGOI_HUB_GED/HUB_EXTERNO/00_REPOSIT%C3%93RIO/HDW-TRANSIT%C3%93RIO?d=waf9ad30eee2a4df3a15e018b4c2215f5&csf=1&web=1&e=DXEV88"

DADOS_EXERCICIOS = {
    "2025": {
        "saldo_num": 74738500.0,
        "saldo_str": "R$ 74.738.500,00",
        "contratos": 4,
        "amortizacao": "R$ 16.219.000,00",
        "pdf_default": "LAUDO_EXECUTIVO_M4_CONTROLE_ENDIVIDAMENTO_2025_9ee82142.pdf",
        "html_default": "LAUDO_EXECUTIVO_M4_CONTROLE_ENDIVIDAMENTO_2025_9ee82142.html",
        "credores": "Banco Daycoval, Banco Sofisa, CRI Habitasec, CRI True",
        "veredito": "HOMOLOGADO COM EFICÁCIA PLENA (Diferença R$ 0,0000)"
    },
    "2024": {
        "saldo_num": 90957500.0,
        "saldo_str": "R$ 90.957.500,00",
        "contratos": 5,
        "amortizacao": "R$ 23.331.167,00",
        "pdf_default": "LAUDO_EXECUTIVO_M4_CONTROLE_ENDIVIDAMENTO_2024_7b63dd77.pdf",
        "html_default": "LAUDO_EXECUTIVO_M4_CONTROLE_ENDIVIDAMENTO_2024_7b63dd77.html",
        "credores": "Daycoval, Sofisa, Habitasec, True, CCB Fiança",
        "veredito": "HOMOLOGADO COM EFICÁCIA PLENA (Diferença R$ 0,0000)"
    },
    "2023": {
        "saldo_num": 114288667.0,
        "saldo_str": "R$ 114.288.667,00",
        "contratos": 6,
        "amortizacao": "R$ 24.511.333,00",
        "pdf_default": "LAUDO_EXECUTIVO_M4_CONTROLE_ENDIVIDAMENTO_2023_2878148d.pdf",
        "html_default": "LAUDO_EXECUTIVO_M4_CONTROLE_ENDIVIDAMENTO_2023_2878148d.html",
        "credores": "Daycoval, Sofisa, Habitasec, True, Safra, Santander",
        "veredito": "HOMOLOGADO COM EFICÁCIA PLENA (Diferença R$ 0,0000)"
    },
    "2022": {
        "saldo_num": 138800000.0,
        "saldo_str": "R$ 138.800.000,00",
        "contratos": 7,
        "amortizacao": "R$ 26.650.000,00",
        "pdf_default": "LAUDO_EXECUTIVO_M4_CONTROLE_ENDIVIDAMENTO_2022_eec00807.pdf",
        "html_default": "LAUDO_EXECUTIVO_M4_CONTROLE_ENDIVIDAMENTO_2022_eec00807.html",
        "credores": "Daycoval, Sofisa, Habitasec, True, Safra, Santander, CCB Capital de Giro",
        "veredito": "HOMOLOGADO COM EFICÁCIA PLENA (Diferença R$ 0,0000)"
    },
    "2021": {
        "saldo_num": 165450000.0,
        "saldo_str": "R$ 165.450.000,00",
        "contratos": 8,
        "amortizacao": "Base Inicial de Partida",
        "pdf_default": "LAUDO_EXECUTIVO_M4_CONTROLE_ENDIVIDAMENTO_2021_b9cba3dd.pdf",
        "html_default": "LAUDO_EXECUTIVO_M4_CONTROLE_ENDIVIDAMENTO_2021_b9cba3dd.html",
        "credores": "Daycoval, Sofisa, Habitasec, True, Safra, Santander, Itaú, Bradesco",
        "veredito": "HOMOLOGADO COM EFICÁCIA PLENA (Diferença R$ 0,0000)"
    }
}

def obter_arquivos_exercicio(ano: str):
    info = DADOS_EXERCICIOS.get(ano, {})
    pasta_pdf = os.path.join(DIR_HDW_TRANSITORIO, ano, "01_PDF_EXECUTIVO")
    pasta_html = os.path.join(DIR_HDW_TRANSITORIO, ano, "02_HTML_INTERATIVO")
    pasta_acordao = os.path.join(DIR_HDW_TRANSITORIO, ano, "06_REVISAO_COLEGIADO")
    
    pdf_path = None
    if info.get("pdf_default"):
        p_ideal = os.path.join(pasta_pdf, info["pdf_default"])
        if os.path.exists(p_ideal):
            pdf_path = p_ideal
    if not pdf_path and os.path.exists(pasta_pdf):
        pdfs = [os.path.join(pasta_pdf, f) for f in os.listdir(pasta_pdf) if f.endswith(".pdf") and "M4" in f]
        if pdfs:
            pdf_path = max(pdfs, key=os.path.getmtime)
            
    html_path = None
    if info.get("html_default"):
        h_ideal = os.path.join(pasta_html, info["html_default"])
        if os.path.exists(h_ideal):
            html_path = h_ideal
    if not html_path and os.path.exists(pasta_html):
        htmls = [os.path.join(pasta_html, f) for f in os.listdir(pasta_html) if f.endswith(".html") and "M4" in f]
        if htmls:
            html_path = max(htmls, key=os.path.getmtime)
            
    acordao_path = os.path.join(pasta_acordao, f"ACORDAO_COLEGIADO_DUPLO_GRAU_{ano}.md")
    if not os.path.exists(acordao_path):
        acordao_path = None
        
    return pdf_path, html_path, acordao_path

def get_base64_image(image_path: str) -> str:
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return f"data:image/png;base64,{base64.b64encode(img_file.read()).decode()}"
    return ""

def generate_qr_code_base64(data_text: str) -> str:
    if qrcode is None:
        return ""
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

    .block-container {
        padding-top: 0.8rem !important;
        padding-bottom: 2rem !important;
        padding-left: 1.2rem !important;
        padding-right: 1.2rem !important;
        max-width: 100% !important;
    }

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

    /* Navegação Principal em Pílulas */
    div[data-testid="stRadio"] > div {
        flex-direction: row;
        gap: 10px;
        background: rgba(15, 23, 42, 0.6);
        padding: 6px;
        border-radius: 14px;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }
    div[data-testid="stRadio"] label {
        background: rgba(30, 41, 59, 0.7) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 10px !important;
        padding: 8px 18px !important;
        color: #e2e8f0 !important;
        font-weight: 700 !important;
        cursor: pointer !important;
        transition: all 0.25s ease !important;
    }
    div[data-testid="stRadio"] label:hover {
        background: rgba(16, 185, 129, 0.2) !important;
        border-color: #10b981 !important;
        color: #34d399 !important;
    }

    /* Caixas dos Sistemas Disponíveis */
    .sistema-card-box {
        background: rgba(15, 23, 42, 0.85);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 14px;
        padding: 14px;
        margin-bottom: 10px;
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

    /* Cards de Relatórios e Auditoria */
    .kansa-report-card {
        background: linear-gradient(145deg, rgba(15, 23, 42, 0.95), rgba(30, 41, 59, 0.88));
        border: 1px solid rgba(16, 185, 129, 0.35);
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 16px;
        box-shadow: 0 6px 24px rgba(0, 0, 0, 0.4);
    }
    .kansa-header-banner {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(6, 78, 59, 0.5) 100%);
        border: 1px solid rgba(16, 185, 129, 0.4);
        border-radius: 16px;
        padding: 22px;
        margin-bottom: 20px;
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

    input, textarea, .stChatInputContainer {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        color: #f1f5f9 !important;
        border-radius: 10px !important;
    }

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

    .vip-ticket-card {
        background: linear-gradient(145deg, rgba(15, 23, 42, 0.95), rgba(30, 41, 59, 0.85));
        border: 2px solid #10b981;
        border-radius: 20px;
        padding: 24px;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5), 0 0 20px rgba(16, 185, 129, 0.2);
        color: #f8fafc;
        margin-bottom: 20px;
    }

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
if "aba_ativa" not in st.session_state:
    st.session_state.aba_ativa = "💬 Hall de Entrada (Recepção Dai)"
if "ano_foco_kansa" not in st.session_state:
    st.session_state.ano_foco_kansa = "2025"

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
        
        st.markdown("<span style='font-size: 0.85rem; color: #cbd5e1; font-weight: 600;'>⚡ Acesso Rápido por Setor:</span>", unsafe_allow_html=True)
        c_chips_1 = st.columns(4)
        perfis_rapidos_1 = [
            ("Presidência", "ronaldo.akagui@sugoisa.com.br"),
            ("G&G", "cintia.godin@sugoisa.com.br"),
            ("Controladoria", "flavia.akagui@sugoisa.com.br"),
            ("Financeiro", "flavia.akagui@sugoisa.com.br"),
        ]
        c_chips_2 = st.columns(3)
        perfis_rapidos_2 = [
            ("Operações", "renato.barroso@sugoisa.com.br"),
            ("Engenharia", "luiz.perez@sugoisa.com.br"),
            ("Núcleo Técnico", "ti@sugoisa.com.br"),
        ]
        
        for idx, (label, user_val) in enumerate(perfis_rapidos_1):
            if c_chips_1[idx].button(label, key=f"chip1_{label}_{idx}", use_container_width=True):
                st.session_state.quick_user = user_val
        for idx, (label, user_val) in enumerate(perfis_rapidos_2):
            if c_chips_2[idx].button(label, key=f"chip2_{label}_{idx}", use_container_width=True):
                st.session_state.quick_user = user_val

        default_usuario = st.session_state.get("quick_user", "ronaldo.akagui@sugoisa.com.br")

        with st.form("login_form"):
            usuario = st.text_input("Cadeira / Usuário PAM", value=default_usuario).lower().strip()
            senha = st.text_input("Senha Corporativa / Credencial PAM", type="password")
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
# 1. BARRA LATERAL: SESSÃO, PERFIL E NAVEGAÇÃO
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
    
    st.markdown("🏢 **Unidades / Tenants Autorizados:**")
    unidades = st.session_state.get("clientes_acesso", [])
    if unidades:
        for u in unidades:
            st.markdown(f"- <span style='color: #38bdf8; font-weight: 600;'>{u.capitalize()}</span>", unsafe_allow_html=True)
    else:
        st.caption("Acesso Global Não Restrito")

    st.markdown("---")
    st.markdown("🧭 **Acesso Rápido:**")
    sb_col1, sb_col2 = st.columns(2)
    if sb_col1.button("💬 Lobby", use_container_width=True, key="sb_btn_lobby"):
        st.session_state.aba_ativa = "💬 Hall de Entrada (Recepção Dai)"
        st.rerun()
    if sb_col2.button("📁 Kan-sa", use_container_width=True, key="sb_btn_kansa"):
        st.session_state.aba_ativa = "📁 監査 Kan-sa (Pasta & Laudos Oficiais)"
        st.rerun()

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
# 2. SELETOR DE ABAS PRINCIPAIS (COM ESTADO)
# ==========================================
OPCOES_ABAS = [
    "💬 Hall de Entrada (Recepção Dai)",
    "📁 監査 Kan-sa (Pasta & Laudos Oficiais)",
    "📋 Seu Contexto & Crachá VIP"
]

if st.session_state.aba_ativa not in OPCOES_ABAS:
    st.session_state.aba_ativa = OPCOES_ABAS[0]

c_nav_left, c_nav_right = st.columns([3.4, 0.6])
with c_nav_left:
    idx_tab = OPCOES_ABAS.index(st.session_state.aba_ativa)
    nova_aba = st.radio(
        "Navegação",
        OPCOES_ABAS,
        index=idx_tab,
        horizontal=True,
        label_visibility="collapsed",
        key="main_nav_radio"
    )
    if nova_aba != st.session_state.aba_ativa:
        st.session_state.aba_ativa = nova_aba
        st.rerun()

with c_nav_right:
    st.markdown("<div style='text-align: right; padding-top: 6px;'><span class='badge-online'><span class='pulse-dot'></span> SUGOI S.A.</span></div>", unsafe_allow_html=True)

st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

# ==========================================
# ABA 1: CHAT INTUITIVO DA DAI (LOBBY CENTRAL)
# ==========================================
if st.session_state.aba_ativa == "💬 Hall de Entrada (Recepção Dai)":
    cor_primaria = config.get("tema", {}).get("cor_primaria", "#00A86B")
    titulo_chat = config.get("textos", {}).get("titulo_chat", "台 Dai - Lobby Central")
    subtitulo_chat = config.get("textos", {}).get("subtitulo_chat", "*Acolhimento empático, triagem instantânea e resolutividade corporativa.*")
    
    col_chat, col_sistemas = st.columns([2.7, 1.3], gap="medium")
    
    with col_sistemas:
        st.markdown("<h4 style='color: #00A86B; margin-top: 4px; margin-bottom: 12px; font-weight: 700;'>🏛️ Sistemas Disponíveis</h4>", unsafe_allow_html=True)
        
        # 1. Kigyou (Primeiro - Gestão, Planejamento, Cultura e Relacionamento)
        st.markdown("""
        <div class='sistema-card-box sistema-kigyou'>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <strong style='font-size: 1.05rem; color: #f8fafc;'>企業 Kigyou</strong>
                <span style='background: rgba(0, 180, 216, 0.2); color: #38bdf8; font-size: 0.72rem; padding: 2px 8px; border-radius: 12px; font-weight: 700;'>🔵 Disponível</span>
            </div>
            <p style='color: #94a3b8; font-size: 0.8rem; margin: 6px 0 10px 0; line-height: 1.4;'>
                Gestão, Planejamento, Cultura e Relacionamento
            </p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Acessar Kigyou", key="btn_goto_kigyou", use_container_width=True):
            st.session_state.quick_prompt_selecionado = "Gostaria de consultar as diretrizes de governança e metabolismo no Kigyou."
            st.rerun()

        # 2. Kan-sa (Segundo - Controladoria, FP&A e Auditoria)
        st.markdown("""
        <div class='sistema-card-box sistema-kansa' style='margin-top: 14px;'>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <strong style='font-size: 1.05rem; color: #f8fafc;'>監査 Kan-sa</strong>
                <span style='background: rgba(0, 168, 107, 0.2); color: #34d399; font-size: 0.72rem; padding: 2px 8px; border-radius: 12px; font-weight: 700;'>🟢 Online</span>
            </div>
            <p style='color: #94a3b8; font-size: 0.8rem; margin: 6px 0 10px 0; line-height: 1.4;'>
                Controladoria, FP&A e Auditoria
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("📂 Acessar Pasta do Kan-sa ➔", key="btn_goto_kansa", use_container_width=True, type="primary"):
            st.session_state.aba_ativa = "📁 監査 Kan-sa (Pasta & Laudos Oficiais)"
            st.rerun()

        # Botões Rápidos no Card do Kan-sa
        c_kbtn1, c_kbtn2 = st.columns(2)
        if c_kbtn1.button("📥 Laudo 2025", key="btn_quick_pdf_2025", use_container_width=True):
            st.session_state.aba_ativa = "📁 監査 Kan-sa (Pasta & Laudos Oficiais)"
            st.session_state.ano_foco_kansa = "2025"
            st.rerun()
            
        c_kbtn2.markdown(f"<a href='{SHAREPOINT_URL_HDW}' target='_blank' style='display: block; text-align: center; background: #0284c7; color: white; padding: 7px 4px; border-radius: 8px; text-decoration: none; font-size: 0.78rem; font-weight: 700;'>🌐 SharePoint ↗</a>", unsafe_allow_html=True)

    with col_chat:
        st.markdown(f"<h3 style='color: {cor_primaria}; margin-bottom: 2px;'>{titulo_chat}</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='color: #94a3b8; font-size: 0.95rem; margin-bottom: 12px;'>{subtitulo_chat}</p>", unsafe_allow_html=True)

        # Seletor do Modo HDC Harness
        c_mode1, c_mode2 = st.columns([1.5, 2.5])
        modo_hdc = c_mode1.toggle("🛡️ HDC Harness (LLM OCI)", value=st.session_state.get("modo_hdc_ativo", True), help="Ativa o Harness de Segurança, Pre-Retrieval e Modelos Soberanos a Custo Zero")
        st.session_state.modo_hdc_ativo = modo_hdc

        if modo_hdc:
            modelo_llm = c_mode2.selectbox(
                "Modelo Soberano (Zero Token OCI):",
                ["🦙 Meta Llama 3.1 8B (Geral)", "🌐 Qwen 2.5 7B (Coder/Processos)", "🔬 DeepSeek R1 (Raciocínio Lógico)"],
                index=0,
                label_visibility="collapsed"
            )
            modelo_id_map = {
                "🦙 Meta Llama 3.1 8B (Geral)": "llama-3.1",
                "🌐 Qwen 2.5 7B (Coder/Processos)": "qwen-2.5",
                "🔬 DeepSeek R1 (Raciocínio Lógico)": "deepseek"
            }
            st.session_state.modelo_hdc_selecionado = modelo_id_map[modelo_llm]

    msg_boas_vindas = config.get("textos", {}).get("mensagem_boas_vindas", "Olá, sou a Dai, agente de triagem do Daisugi. Posso te ajudar diretamente, ou, te direcionar a alguma outra sala, me diga o que precisa.")
    if not st.session_state.messages:
        st.session_state.messages = [{
            "role": "assistant",
            "content": msg_boas_vindas,
            "arquivo_anexo": None,
            "link_dw": None,
            "codigo_rastreamento": None
        }]

    st.markdown("<span style='font-size: 0.85rem; color: #94a3b8; font-weight: 600;'>💡 Sugestões de Atendimento Rápido:</span>", unsafe_allow_html=True)
    qp1, qp2, qp3, qp4 = st.columns(4)
    if qp1.button("💼 Visita Executiva (em desenvolvimento)", use_container_width=True):
        st.info("ℹ️ Atendimento Rápido: 'Visita Executiva' em desenvolvimento.")
    if qp2.button("📄 Entregar CCB / Fatura (em desenvolvimento)", use_container_width=True):
        st.info("ℹ️ Atendimento Rápido: 'Entregar CCB / Fatura' em desenvolvimento.")
    if qp3.button("🔍 Consulta no DW (em desenvolvimento)", use_container_width=True):
        st.info("ℹ️ Atendimento Rápido: 'Consulta no DW' em desenvolvimento.")
    if qp4.button("⚡ Prestador de Serviço (em desenvolvimento)", use_container_width=True):
        st.info("ℹ️ Atendimento Rápido: 'Prestador de Serviço' em desenvolvimento.")

    avatar_img = config.get("avatar", {}).get("imagem_lobby", "lobby_avatar.jpg")
    icone_usuario = config.get("avatar", {}).get("icone_usuario", "👤")
    dai_avatar = get_base64_image(avatar_img) if os.path.exists(avatar_img) else "👩🏻‍💼"

    for message in st.session_state.messages:
        av = dai_avatar if message["role"] == "assistant" else icone_usuario
        with st.chat_message(message["role"], avatar=av):
            st.markdown(message["content"])
            
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
            if st.session_state.get("modo_hdc_ativo", True):
                modelo_ativo = st.session_state.get("modelo_hdc_selecionado", "llama-3.1")
                with st.spinner(f"🛡️ HDC Harness processando inferência com modelo soberano ({modelo_ativo})..."):
                    try:
                        headers = {"Content-Type": "application/json"}
                        token_jwt = st.session_state.get("token_jwt")
                        if token_jwt:
                            headers["Authorization"] = f"Bearer {token_jwt}"

                        history_msgs = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages if m.get("content")]
                        payload = {
                            "model": modelo_ativo,
                            "wbs_id": "WBS-SUG-014",
                            "messages": history_msgs,
                            "temperature": 0.0
                        }

                        res = requests.post(
                            f"{API_BASE_URL}/api/v1/chat/completions/stream",
                            json=payload,
                            headers=headers,
                            stream=True,
                            timeout=20
                        )
                        if res.status_code == 200:
                            texto_resposta = ""
                            placeholder = st.empty()
                            for line in res.iter_lines():
                                if line:
                                    line_str = line.decode('utf-8')
                                    if line_str.startswith("data: "):
                                        chunk_str = line_str.replace("data: ", "").strip()
                                        if chunk_str == "[DONE]":
                                            break
                                        try:
                                            chunk_data = json.loads(chunk_str)
                                            if "error" in chunk_data:
                                                texto_resposta = f"⛔ **[Harness Bloqueio]** {chunk_data['error']}"
                                                placeholder.markdown(texto_resposta)
                                                break
                                            delta = chunk_data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                            texto_resposta += delta
                                            placeholder.markdown(texto_resposta)
                                        except Exception:
                                            pass

                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": texto_resposta,
                                "arquivo_anexo": None,
                                "link_dw": None,
                                "codigo_rastreamento": f"HDC-HARNESS-{int(time.time())}"
                            })
                            st.rerun()
                        else:
                            st.error(f"❌ Erro no HDC Gateway: HTTP {res.status_code}")
                    except Exception as e:
                        st.error(f"❌ Falha de comunicação com o HDC Harness: {e}")
            else:
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
                            
                            if st.session_state.ticket_atual:
                                st.session_state.ticket_atual["destino"] = destino or st.session_state.ticket_atual["destino"]
                                st.session_state.ticket_atual["status"] = "Roteamento Definido"
                                if cod_rastreio:
                                    st.session_state.ticket_atual["codigo"] = cod_rastreio
                                    st.session_state.ticket_atual["qr_b64"] = generate_qr_code_base64(f"DAISUGI-VERIFIED:{cod_rastreio}:{destino}")

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

# ==========================================
# ABA 2: PASTA DO KAN-SA E LAUDOS OFICIAIS
# ==========================================
elif st.session_state.aba_ativa == "📁 監査 Kan-sa (Pasta & Laudos Oficiais)":
    # Banner Cabeçalho
    st.markdown("""
    <div class='kansa-header-banner'>
        <div style='display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 12px;'>
            <div>
                <span style='color: #10b981; font-size: 0.82rem; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;'>
                    Daisugi Controladoria & Auditoria Forense
                </span>
                <h2 style='color: #ffffff; margin: 4px 0 6px 0; font-size: 1.8rem; font-weight: 800;'>
                    🏛️ 監査 Kan-sa — Repositório de Laudos Executivos M4
                </h2>
                <p style='color: #94a3b8; font-size: 0.92rem; margin: 0; max-width: 800px;'>
                    Módulo de Controle Mensal de Endividamento Bancário & Mercado de Capitais. Todos os exercícios certificados com Duplo Grau de Revisão Colegiada e sem cortes de página A4.
                </p>
            </div>
            <div style='text-align: right;'>
                <span style='display: inline-block; background: rgba(16, 185, 129, 0.2); border: 1px solid #10b981; color: #34d399; font-size: 0.82rem; padding: 6px 14px; border-radius: 20px; font-weight: 700; margin-bottom: 6px;'>
                    ✅ Duplo Grau de Revisão: Homologado
                </span><br/>
                <span style='color: #cbd5e1; font-size: 0.8rem;'>Tolerância Pericial: <strong>R$ 0,0000</strong></span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Barra de Repositórios e Pastas
    c_pasta1, c_pasta2 = st.columns([2.2, 1.8])
    with c_pasta1:
        st.markdown(f"""
        <div style='background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 12px; padding: 14px 18px;'>
            <div style='font-size: 0.8rem; color: #38bdf8; font-weight: 700; text-transform: uppercase;'>📂 Caminho no Servidor Local / Drive SUGOI:</div>
            <code style='display: block; background: #0f172a; color: #f1f5f9; padding: 6px 10px; border-radius: 8px; margin: 6px 0; font-size: 0.78rem; word-break: break-all;'>
                {DIR_HDW_TRANSITORIO}
            </code>
            <div style='display: flex; gap: 10px; margin-top: 10px;'>
                <a href='{SHAREPOINT_URL_HDW}' target='_blank' style='display: inline-flex; align-items: center; background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%); color: white; padding: 8px 16px; border-radius: 8px; text-decoration: none; font-size: 0.85rem; font-weight: 700; box-shadow: 0 4px 12px rgba(2, 132, 199, 0.3);'>
                    🌐 Abrir Pasta no SharePoint Online (HDW-TRANSITÓRIO) ↗
                </a>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with c_pasta2:
        st.markdown("<div style='background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 12px; padding: 14px 18px;'>", unsafe_allow_html=True)
        st.markdown("<div style='font-size: 0.8rem; color: #34d399; font-weight: 700; text-transform: uppercase;'>💻 Ações no Servidor Local:</div>", unsafe_allow_html=True)
        st.caption("Dispare a abertura de janela na estação de trabalho local:")
        if st.button("📂 Abrir Pasta no Windows Explorer Local", use_container_width=True, key="btn_win_explorer"):
            try:
                subprocess.Popen(f'explorer.exe "{DIR_HDW_TRANSITORIO}"')
                st.success("📂 Pasta aberta no Windows Explorer!")
            except Exception as e:
                st.info(f"Caminho local acessível em: {DIR_HDW_TRANSITORIO}")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")

    # MÓDULO: EVOLUÇÃO DA DÍVIDA (2021 A 2025)
    st.markdown("### 📈 Evolução do Endividamento Consolidado (2021 a 2025)")
    st.markdown("<p style='color: #94a3b8; font-size: 0.9rem;'>Trajetória pericial da dívida bancária e mercado de capitais ao longo dos 5 exercícios auditados.</p>", unsafe_allow_html=True)

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    col_m1.metric("Dívida Inicial (2021)", "R$ 165,45 M", "8 Contratos")
    col_m2.metric("Dívida Atual (2025)", "R$ 74,74 M", "-54,8% Desalavancagem")
    col_m3.metric("Total Amortizado", "R$ 90,71 M", "4 Operações Quitadas")
    col_m4.metric("Auditoria Colegiada", "100% Homologado", "Diferença R$ 0,00")

    # Filtro Interativo de Período
    anos_disponiveis = ["2021", "2022", "2023", "2024", "2025"]
    anos_selecionados = st.multiselect(
        "Selecionar Exercícios para Visualização Comparativa:",
        options=anos_disponiveis,
        default=anos_disponiveis,
        key="ms_anos_evolucao"
    )

    if anos_selecionados and pd is not None:
        dados_df = []
        for a in sorted(anos_selecionados):
            info_a = DADOS_EXERCICIOS.get(a, {})
            dados_df.append({
                "Ano": a,
                "Saldo Devedor (R$ Mi)": round(info_a.get("saldo_num", 0.0) / 1000000, 2),
                "Contratos Ativos": info_a.get("contratos", 0),
                "Amortização": info_a.get("amortizacao", "-")
            })
        df_chart = pd.DataFrame(dados_df)
        
        c_ch1, c_ch2 = st.columns([2.2, 1.8])
        with c_ch1:
            st.caption("📊 Saldo Devedor Consolidado por Exercício (R$ Milhões):")
            st.bar_chart(df_chart, x="Ano", y="Saldo Devedor (R$ Mi)", color="#10b981")
        with c_ch2:
            st.caption("📋 Resumo Comparativo Analítico:")
            st.dataframe(df_chart, use_container_width=True, hide_index=True)

    st.markdown("---")

    # ACERVO DOS LAUDOS EXECUTIVOS COM BOTÕES DIRETOS
    st.markdown("### 📑 Acervo de Laudos Executivos Oficiais M4 (Ano a Ano)")
    st.markdown("<p style='color: #94a3b8; font-size: 0.9rem;'>Clique para baixar o PDF Oficial sem cortes pronto para assinatura ou visualizar o relatório interativo web e o acórdão colegiado.</p>", unsafe_allow_html=True)

    anos_exibicao = sorted(anos_selecionados if anos_selecionados else anos_disponiveis, reverse=True)

    for ano in anos_exibicao:
        info_ano = DADOS_EXERCICIOS.get(ano, {})
        pdf_path, html_path, acordao_path = obter_arquivos_exercicio(ano)
        
        st.markdown(f"""
        <div class='kansa-report-card'>
            <div style='display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 12px; margin-bottom: 14px;'>
                <div>
                    <span style='background: rgba(16, 185, 129, 0.2); color: #34d399; font-weight: 800; font-size: 0.75rem; padding: 3px 8px; border-radius: 6px;'>EXERCÍCIO {ano}</span>
                    <h3 style='margin: 4px 0 0 0; color: #ffffff;'>📄 Laudo Executivo M4 — {ano}</h3>
                </div>
                <div style='text-align: right;'>
                    <span style='font-size: 0.8rem; color: #94a3b8;'>Saldo Auditado:</span><br/>
                    <strong style='font-size: 1.25rem; color: #38bdf8;'>{info_ano.get('saldo_str', 'N/D')}</strong>
                </div>
            </div>
            <div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; font-size: 0.85rem; color: #cbd5e1; margin-bottom: 16px;'>
                <div>📑 <strong>Operações:</strong> {info_ano.get('contratos')} Contratos Ativos</div>
                <div>📉 <strong>Amortização Anual:</strong> {info_ano.get('amortizacao')}</div>
                <div>🏦 <strong>Credores:</strong> {info_ano.get('credores')}</div>
                <div>⚖️ <strong>Status Colegiado:</strong> <span style='color: #34d399;'>{info_ano.get('veredito')}</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        c_btn_pdf, c_btn_html, c_btn_acordao = st.columns([1.5, 1.3, 1.2])

        # 1. BOTÃO DOWNLOAD PDF OFICIAL
        with c_btn_pdf:
            if pdf_path and os.path.exists(pdf_path):
                try:
                    with open(pdf_path, "rb") as pf:
                        bytes_pdf = pf.read()
                    st.download_button(
                        label=f"📥 Baixar PDF Oficial {ano} ({len(bytes_pdf)/1024/1024:.1f} MB)",
                        data=bytes_pdf,
                        file_name=f"LAUDO_EXECUTIVO_M4_CONTROLE_ENDIVIDAMENTO_{ano}.pdf",
                        mime="application/pdf",
                        key=f"btn_dl_pdf_{ano}",
                        use_container_width=True,
                        type="primary"
                    )
                except Exception as err:
                    st.error(f"Erro ao preparar PDF: {err}")
            else:
                st.button(f"⚠️ PDF {ano} Indisponível", disabled=True, use_container_width=True, key=f"btn_dis_pdf_{ano}")

        # 2. BOTÃO VISUALIZAR HTML
        with c_btn_html:
            if html_path and os.path.exists(html_path):
                try:
                    with open(html_path, "rb") as hf:
                        bytes_html = hf.read()
                    st.download_button(
                        label=f"💾 Baixar HTML Interativo {ano}",
                        data=bytes_html,
                        file_name=f"LAUDO_EXECUTIVO_M4_CONTROLE_ENDIVIDAMENTO_{ano}.html",
                        mime="text/html",
                        key=f"btn_dl_html_{ano}",
                        use_container_width=True
                    )
                except Exception as err:
                    st.error(f"Erro ao ler HTML: {err}")
            else:
                st.button(f"⚠️ HTML {ano} Indisponível", disabled=True, use_container_width=True, key=f"btn_dis_html_{ano}")

        # 3. ACÓRDÃO COLEGIADO
        with c_btn_acordao:
            ver_acordao = st.checkbox(f"⚖️ Ver Acórdão {ano}", key=f"cb_acordao_{ano}")

        # Exibição do HTML dentro de Expander
        with st.expander(f"👁️ Visualizar Relatório Web Interativo Completo — {ano}", expanded=False):
            if html_path and os.path.exists(html_path):
                try:
                    with open(html_path, "r", encoding="utf-8") as hf:
                        html_content = hf.read()
                    st.components.v1.html(html_content, height=650, scrolling=True)
                except Exception as e:
                    st.error(f"Falha ao carregar HTML: {e}")
            else:
                st.info("Arquivo HTML não localizado nesta pasta.")

        # Exibição do Acórdão
        if ver_acordao:
            st.markdown(f"#### ⚖️ Acórdão de Julgamento — Revisão do Colegiado ({ano})")
            if acordao_path and os.path.exists(acordao_path):
                try:
                    with open(acordao_path, "r", encoding="utf-8") as af:
                        texto_acordao = af.read()
                    st.markdown(texto_acordao)
                except Exception as e:
                    st.error(f"Erro ao abrir Acórdão: {e}")
            else:
                st.info(f"Acórdão registrado nos autos do exercício {ano}. Veredito homologado com eficácia plena e diferença R$ 0,0000.")

        st.markdown("<div style='margin-bottom: 18px;'></div>", unsafe_allow_html=True)

# ==========================================
# ABA 3: SEU CONTEXTO, CRACHÁ VIP E FEEDBACK
# ==========================================
elif st.session_state.aba_ativa == "📋 Seu Contexto & Crachá VIP":
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

    st.markdown("---")
    titulo_laudo = config.get("textos", {}).get("titulo_laudo", "Laudo Técnico de Triagem & Roteamento")
    st.markdown(f"### 💊 {titulo_laudo}")
    laudo_vazio = config.get("textos", {}).get("laudo_vazio", "Nenhum laudo emitido ainda. Dialogue com a Dai no Lobby.")
    st.info(st.session_state.get("laudo_final", laudo_vazio))

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
