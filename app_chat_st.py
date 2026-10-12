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

def encontrar_dir_hdw_soberano():
    base_local = os.path.join(os.path.dirname(os.path.abspath(__file__)), "DATA_ROOM", "HDW_TRANSITORIO", "01_CONTROLADORIA_E_FINANCAS", "M4_CONTROLE_ENDIVIDAMENTO")
    if os.path.exists(base_local):
        return base_local
    for letter in ["H", "G"]:
        root = f"{letter}:\\Drives compartilhados"
        if not os.path.exists(root):
            continue
        try:
            for f1 in os.listdir(root):
                if "SUGOI" in f1:
                    p1 = os.path.join(root, f1)
                    for f2 in os.listdir(p1):
                        p2 = os.path.join(p1, f2, "DAISUGI", "02_Daisugi_kan-sa", "DATA_ROOM", "HDW_TRANSITORIO", "01_CONTROLADORIA_E_FINANCAS", "M4_CONTROLE_ENDIVIDAMENTO")
                        if os.path.exists(p2):
                            return p2
        except Exception:
            pass
    return r"H:\\Drives compartilhados\\APLICAÇÕES - SUGOI-SA\\02_APLICAÇÕES_E_SISTEMAS\\DAISUGI\\02_Daisugi_kan-sa\\DATA_ROOM\\HDW_TRANSITORIO\\01_CONTROLADORIA_E_FINANCAS\\M4_CONTROLE_ENDIVIDAMENTO"

DIR_HDW_TRANSITORIO = encontrar_dir_hdw_soberano()
SHAREPOINT_URL_HDW = "https://sugoiconstrutora.sharepoint.com/:f:/r/sites/DataHubDocumentalSUGOI/Documentos%20Compartilhados/SUGOI_HUB_GED/HUB_EXTERNO/00_REPOSIT%C3%93RIO/HDW-TRANSIT%C3%93RIO?d=waf9ad30eee2a4df3a15e018b4c2215f5&csf=1&web=1&e=DXEV88"

DADOS_EXERCICIOS = {
    "2021": {
        "saldo_num": 21438000.0,
        "saldo_str": "R$ 21.438.000,00",
        "contratos": 7,
        "amortizacao": "Amortização Líquida: R$ 2.762.000,00",
        "pdf_default": "LAUDO_EXECUTIVO_M4_CONTROLE_ENDIVIDAMENTO_2021_b9cba3dd.pdf",
        "html_default": "LAUDO_EXECUTIVO_M4_CONTROLE_ENDIVIDAMENTO_2021_b9cba3dd.html",
        "credores": "Banco ABC Brasil, Banco Pine, Caixa Econômica, Daycoval",
        "veredito": "HOMOLOGADO COM EFICÁCIA PLENA (Diferença R$ 0,0000)"
    },
    "2022": {
        "saldo_num": 36098000.0,
        "saldo_str": "R$ 36.098.000,00",
        "contratos": 7,
        "amortizacao": "Captação Líquida: R$ 14.660.000,00",
        "pdf_default": "LAUDO_EXECUTIVO_M4_CONTROLE_ENDIVIDAMENTO_2022_eec00807.pdf",
        "html_default": "LAUDO_EXECUTIVO_M4_CONTROLE_ENDIVIDAMENTO_2022_eec00807.html",
        "credores": "Red Asset, Banco ABC Brasil, Banco Pine, Caixa Econômica",
        "veredito": "HOMOLOGADO COM EFICÁCIA PLENA (Diferença R$ 0,0000)"
    },
    "2023": {
        "saldo_num": 113358000.0,
        "saldo_str": "R$ 113.358.000,00",
        "contratos": 7,
        "amortizacao": "Emissão Estruturada CRI: R$ 77.260.000,00",
        "pdf_default": "LAUDO_EXECUTIVO_M4_CONTROLE_ENDIVIDAMENTO_2023_2878148d.pdf",
        "html_default": "LAUDO_EXECUTIVO_M4_CONTROLE_ENDIVIDAMENTO_2023_2878148d.html",
        "credores": "Opea Securitizadora, Banco Safra, Banco ABC Brasil, Caixa Econômica",
        "veredito": "HOMOLOGADO COM EFICÁCIA PLENA (Diferença R$ 0,0000)"
    },
    "2024": {
        "saldo_num": 174667339.20,
        "saldo_str": "R$ 174.667.339,20",
        "contratos": 29,
        "amortizacao": "Serviço Mensal Médio: R$ 2.180.000,00/mês",
        "pdf_default": "LAUDO_EXECUTIVO_M4_CONTROLE_ENDIVIDAMENTO_2024_53b09e63.pdf",
        "html_default": "LAUDO_EXECUTIVO_M4_CONTROLE_ENDIVIDAMENTO_2024_53b09e63.html",
        "credores": "Opea (CRI 1ª e 2ª Séries), Safra, ABC Brasil, Paulista, CCBs",
        "veredito": "HOMOLOGADO COM EFICÁCIA PLENA (Diferença R$ 0,0000)"
    },
    "2025": {
        "saldo_num": 74738500.0,
        "saldo_str": "R$ 74.738.500,00",
        "contratos": 4,
        "amortizacao": "Amortização Projetada: R$ 16.219.000,00",
        "pdf_default": "LAUDO_EXECUTIVO_M4_CONTROLE_ENDIVIDAMENTO_2025_9ee82142.pdf",
        "html_default": "LAUDO_EXECUTIVO_M4_CONTROLE_ENDIVIDAMENTO_2025_9ee82142.html",
        "credores": "Opea Securitizadora, Santander, ABC Brasil, Daycoval",
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

def renderizar_pasta_kansa(prefixo_key: str = "kansa"):
    """
    Renderiza os laudos, gráficos e relatórios oficiais M4 do Kan-sa.
    Pode ser chamado no painel lateral de artefatos (com o chat ativo) ou na aba cheia.
    """
    # MÓDULO: EVOLUÇÃO DA DÍVIDA (2021 A 2025)
    st.markdown("### 📈 Evolução do Endividamento Consolidado (2021 a 2025)")
    st.markdown("<p style='color: #94a3b8; font-size: 0.88rem;'>Trajetória pericial da dívida bancária e mercado de capitais nos 5 exercícios auditados.</p>", unsafe_allow_html=True)

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    col_m1.metric("Base Histórica (2021)", "R$ 21,44 M", "7 Contratos (T0)")
    col_m2.metric("Pico de Captação (2024)", "R$ 174,67 M", "29 Contratos Ativos")
    col_m3.metric("Posição Atual (2025)", "R$ 74,74 M", "-57,2% Desalavancagem pós-2024")
    col_m4.metric("Auditoria Colegiada", "100% Homologado", "Diferença R$ 0,0000")

    # Filtro Interativo de Período
    anos_disponiveis = ["2021", "2022", "2023", "2024", "2025"]
    anos_selecionados = st.multiselect(
        "Selecionar Exercícios para Visualização Comparativa:",
        options=anos_disponiveis,
        default=anos_disponiveis,
        key=f"ms_anos_evolucao_{prefixo_key}"
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
        
        c_ch1, c_ch2 = st.columns([2.0, 1.8])
        with c_ch1:
            st.caption("📊 Saldo Devedor Consolidado por Exercício (R$ Mi):")
            st.bar_chart(df_chart, x="Ano", y="Saldo Devedor (R$ Mi)", color="#10b981")
        with c_ch2:
            st.caption("📋 Resumo Analítico:")
            st.dataframe(df_chart, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("### 📑 Acervo de Laudos Executivos Oficiais M4 (Ano a Ano)")

    anos_exibicao = sorted(anos_selecionados if anos_selecionados else anos_disponiveis, reverse=True)

    for ano in anos_exibicao:
        info_ano = DADOS_EXERCICIOS.get(ano, {})
        pdf_path, html_path, acordao_path = obter_arquivos_exercicio(ano)
        
        st.markdown(f"""
        <div class='kansa-report-card'>
            <div style='display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 10px; margin-bottom: 12px;'>
                <div>
                    <span style='background: rgba(16, 185, 129, 0.2); color: #34d399; font-weight: 800; font-size: 0.72rem; padding: 2px 7px; border-radius: 5px;'>EXERCÍCIO {ano}</span>
                    <h4 style='margin: 3px 0 0 0; color: #ffffff;'>📄 Laudo Executivo M4 — {ano}</h4>
                </div>
                <div style='text-align: right;'>
                    <span style='font-size: 0.75rem; color: #94a3b8;'>Saldo Auditado:</span><br/>
                    <strong style='font-size: 1.15rem; color: #38bdf8;'>{info_ano.get('saldo_str', 'N/D')}</strong>
                </div>
            </div>
            <div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 10px; font-size: 0.82rem; color: #cbd5e1; margin-bottom: 12px;'>
                <div>📑 <strong>Operações:</strong> {info_ano.get('contratos')} Contratos</div>
                <div>📉 <strong>Amortização:</strong> {info_ano.get('amortizacao')}</div>
                <div>🏦 <strong>Credores:</strong> {info_ano.get('credores')}</div>
                <div>⚖️ <strong>Status:</strong> <span style='color: #34d399;'>{info_ano.get('veredito')}</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        c_btn_pdf, c_btn_html_dl, c_btn_html_link, c_btn_acordao = st.columns([1.3, 1.2, 1.2, 1.0])

        with c_btn_pdf:
            if pdf_path and os.path.exists(pdf_path):
                try:
                    with open(pdf_path, "rb") as pf:
                        bytes_pdf = pf.read()
                    st.download_button(
                        label=f"📥 PDF {ano} ({len(bytes_pdf)/1024/1024:.1f}MB)",
                        data=bytes_pdf,
                        file_name=f"LAUDO_EXECUTIVO_M4_CONTROLE_ENDIVIDAMENTO_{ano}.pdf",
                        mime="application/pdf",
                        key=f"btn_dl_pdf_{ano}_{prefixo_key}",
                        use_container_width=True,
                        type="primary"
                    )
                except Exception as err:
                    st.error(f"Erro ao preparar PDF: {err}")
            else:
                st.button(f"⚠️ PDF {ano} Indisponível", disabled=True, use_container_width=True, key=f"btn_dis_pdf_{ano}_{prefixo_key}")

        html_b64 = ""
        html_content = ""
        if html_path and os.path.exists(html_path):
            try:
                with open(html_path, "r", encoding="utf-8") as hf:
                    html_content = hf.read()
                html_b64 = base64.b64encode(html_content.encode("utf-8")).decode("utf-8")
            except Exception:
                pass

        with c_btn_html_dl:
            if html_content:
                st.download_button(
                    label=f"💾 Baixar HTML",
                    data=html_content.encode("utf-8"),
                    file_name=f"LAUDO_EXECUTIVO_M4_CONTROLE_ENDIVIDAMENTO_{ano}.html",
                    mime="text/html",
                    key=f"btn_dl_html_{ano}_{prefixo_key}",
                    use_container_width=True
                )
            else:
                st.button(f"⚠️ HTML Indisponível", disabled=True, use_container_width=True, key=f"btn_dis_html_{ano}_{prefixo_key}")

        with c_btn_html_link:
            if html_b64:
                st.markdown(
                    f"<a href='data:text/html;base64,{html_b64}' target='_blank' style='display: block; text-align: center; background: #0284c7; color: white; padding: 7px 4px; border-radius: 8px; text-decoration: none; font-size: 0.8rem; font-weight: 700;'>🌐 Abrir HTML ↗</a>",
                    unsafe_allow_html=True
                )
            else:
                st.caption("Link N/D")

        with c_btn_acordao:
            ver_acordao = st.checkbox(f"⚖️ Acórdão", key=f"cb_acordao_{ano}_{prefixo_key}")

        # Renderização do Relatório Web Interativo Completo
        with st.expander(f"👁️ Visualizar Relatório Web Interativo — Exercício {ano}", expanded=False):
            if html_content:
                st.components.v1.html(html_content, height=650, scrolling=True)
            else:
                st.info("Arquivo HTML não localizado nesta pasta.")

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

        st.markdown("<div style='margin-bottom: 14px;'></div>", unsafe_allow_html=True)

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

    .artifact-container {
        background: rgba(15, 23, 42, 0.95);
        border: 1px solid rgba(56, 189, 248, 0.35);
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.6), 0 0 25px rgba(56, 189, 248, 0.15);
        height: calc(100vh - 140px);
        overflow-y: auto;
        position: sticky;
        top: 20px;
    }
    
    .artifact-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding-bottom: 14px;
        margin-bottom: 14px;
        border-bottom: 1px solid rgba(56, 189, 248, 0.2);
    }
    
    .artifact-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(16, 185, 129, 0.15);
        border: 1px solid #10b981;
        color: #34d399;
        font-size: 0.76rem;
        padding: 3px 10px;
        border-radius: 20px;
        font-weight: 700;
        letter-spacing: 0.5px;
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
if "active_artifact" not in st.session_state:
    st.session_state.active_artifact = None
if "artifact_expanded" not in st.session_state:
    st.session_state.artifact_expanded = False

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
        
        st.markdown("<span style='font-size: 0.85rem; color: #cbd5e1; font-weight: 600;'>⚡ Acesso Rápido às Cadeiras PAM:</span>", unsafe_allow_html=True)
        
        # Linha 1: Liderança & Diretorias
        c_chips_1 = st.columns(3)
        perfis_rapidos_1 = [
            ("🏛️ Presidência (Ronaldo)", "ronaldo.akagui@sugoisa.com.br"),
            ("⚙️ Operações (Renato)", "renato.barroso@sugoisa.com.br"),
            ("🏗️ Engenharia (Luiz)", "luiz.perez@sugoisa.com.br"),
        ]
        # Linha 2: Gestão, Controladoria & Jurídico
        c_chips_2 = st.columns(4)
        perfis_rapidos_2 = [
            ("📊 Controller (Fernando)", "fernando.brasil@sugoisa.com.br"),
            ("💰 PMO Fin (Flávia)", "flavia.akagui@sugoisa.com.br"),
            ("⚖️ Jurídico (Paola)", "paola@sugoisa.com.br"),
            ("👥 PMO G&G (Cíntia)", "cintia.godin@sugoisa.com.br"),
        ]
        # Linha 3: CRM, TI & Especialistas
        c_chips_3 = st.columns(3)
        perfis_rapidos_3 = [
            ("🤝 PMO CRM (Fabiana)", "fabiana@sugoisa.com.br"),
            ("💻 Núcleo TI (Wesley)", "wesley@sugoisa.com.br"),
            ("📈 Monitor (Gustavo)", "gustavo@sugoisa.com.br"),
        ]
        # Linha 4: Finanças, Operações Campo & Controladoria Apoio
        c_chips_4 = st.columns(3)
        perfis_rapidos_4 = [
            ("💵 Financeiro (Denise)", "denise@sugoisa.com.br"),
            ("🚜 Obras/Ops (Lukas)", "lukas@sugoisa.com.br"),
            ("📑 Controladoria (Viviam)", "viviam@sugoisa.com.br"),
        ]
        
        for idx, (label, user_val) in enumerate(perfis_rapidos_1):
            if c_chips_1[idx].button(label, key=f"chip1_{label}_{idx}", use_container_width=True):
                st.session_state.quick_user = user_val
        for idx, (label, user_val) in enumerate(perfis_rapidos_2):
            if c_chips_2[idx].button(label, key=f"chip2_{label}_{idx}", use_container_width=True):
                st.session_state.quick_user = user_val
        for idx, (label, user_val) in enumerate(perfis_rapidos_3):
            if c_chips_3[idx].button(label, key=f"chip3_{label}_{idx}", use_container_width=True):
                st.session_state.quick_user = user_val
        for idx, (label, user_val) in enumerate(perfis_rapidos_4):
            if c_chips_4[idx].button(label, key=f"chip4_{label}_{idx}", use_container_width=True):
                st.session_state.quick_user = user_val

        default_usuario = st.session_state.get("quick_user", "ronaldo.akagui@sugoisa.com.br")

        with st.form("login_form"):
            usuario = st.text_input("Cadeira / Usuário PAM (ou E-mail Corporativo)", value=default_usuario).lower().strip()
            senha = st.text_input("Senha Corporativa / RG Cadastrado", type="password", help="Para cadeiras registradas, digite seu número de RG ou senha de contingência.")
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
    sb_col1, sb_col2, sb_col3 = st.columns(3)
    if sb_col1.button("💬 Lobby", use_container_width=True, key="sb_btn_lobby"):
        st.session_state.aba_ativa = "💬 Hall de Entrada (Recepção Dai)"
        st.rerun()
    if sb_col2.button("🏛️ HDW", use_container_width=True, key="sb_btn_hdw"):
        st.session_state.aba_ativa = "🏛️ Biblioteca HDW (Custódia Soberana)"
        st.rerun()
    if sb_col3.button("📁 Kan-sa", use_container_width=True, key="sb_btn_kansa"):
        st.session_state.aba_ativa = "💬 Hall de Entrada (Recepção Dai)"
        st.session_state.active_artifact = {
            "tipo": "kansa_folder",
            "titulo": "Pasta Oficial Kan-sa — Acervo & Laudos Executivos M4",
            "cota": "EST-01-KANSA-FOLDER",
            "hash": "e24de050a3f8a4e320f77bc954f62024765d1dcb74c43169f4bc7210e74bcfc4",
            "origem": "Hudson Data Warehouse (CentOS 7 - 10.8.0.1:8000)"
        }
        st.rerun()

    if st.session_state.aba_ativa != "💬 Hall de Entrada (Recepção Dai)":
        if st.sidebar.button("💬 ◀ Voltar ao Chat da Dai", use_container_width=True, type="primary"):
            st.session_state.aba_ativa = "💬 Hall de Entrada (Recepção Dai)"
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
# 2. BARRA DE SISTEMAS SUPERIOR (ECOSSISTEMA DAISUGI)
# ==========================================
c_sys_nav = st.columns([1.3, 1.2, 1.5, 1.4, 1.3, 1.3])
with c_sys_nav[0]:
    if st.button("🏢 Kigyou (em desenv.)", key="top_btn_kigyou", use_container_width=True):
        st.info("ℹ️ Sistema '企業 Kigyou' (Gestão, Cultura e Metabolismo) em fase de integração contínua.")
with c_sys_nav[1]:
    if st.button("📊 Kan-sa", key="top_btn_kansa", use_container_width=True, type="primary"):
        st.session_state.aba_ativa = "💬 Hall de Entrada (Recepção Dai)"
        st.session_state.active_artifact = {
            "tipo": "kansa_folder",
            "titulo": "Pasta Oficial Kan-sa — Acervo & Laudos Executivos M4",
            "cota": "EST-01-KANSA-FOLDER",
            "hash": "e24de050a3f8a4e320f77bc954f62024765d1dcb74c43169f4bc7210e74bcfc4",
            "origem": "Hudson Data Warehouse (CentOS 7 - 10.8.0.1:8000)"
        }
        st.rerun()
with c_sys_nav[2]:
    if st.button("🏛️ HDW (Biblioteca-DW)", key="top_btn_hdw", use_container_width=True):
        st.session_state.aba_ativa = "🏛️ Biblioteca HDW (Custódia Soberana)"
        st.rerun()
with c_sys_nav[3]:
    if st.button("🔍 Portal do Auditor (em desenv.)", key="top_btn_auditor", use_container_width=True):
        st.info("ℹ️ 'Portal do Auditor' (Perícia, Trilha de Auditoria e Duplo Grau) em desenvolvimento.")
with c_sys_nav[4]:
    if st.button("🤝 Parceiro (em desenv.)", key="top_btn_parceiro", use_container_width=True):
        st.info("ℹ️ Portal 'Parceiro' (Fornecedores, Credenciados e Medições de Obras) em desenvolvimento.")
with c_sys_nav[5]:
    st.markdown("<div style='text-align: right; padding-top: 6px;'><span class='badge-online'><span class='pulse-dot'></span> SUGOI S.A.</span></div>", unsafe_allow_html=True)

st.markdown("<div style='margin-bottom: 8px;'></div>", unsafe_allow_html=True)

# ==========================================
# ABA 1: CHAT INTUITIVO DA DAI (LOBBY CENTRAL)
# ==========================================
if st.session_state.aba_ativa == "💬 Hall de Entrada (Recepção Dai)":
    cor_primaria = config.get("tema", {}).get("cor_primaria", "#00A86B")
    titulo_chat = config.get("textos", {}).get("titulo_chat", "台 Dai - Lobby Central")
    subtitulo_chat = config.get("textos", {}).get("subtitulo_chat", "*Acolhimento empático, triagem instantânea e resolutividade corporativa.*")
    
    st.markdown(f"<h3 style='color: {cor_primaria}; margin-bottom: 2px;'>{titulo_chat}</h3>", unsafe_allow_html=True)
    st.markdown(f"<p style='color: #94a3b8; font-size: 0.95rem; margin-bottom: 12px;'>{subtitulo_chat}</p>", unsafe_allow_html=True)

    msg_boas_vindas = config.get("textos", {}).get("mensagem_boas_vindas", "Olá, sou a Dai, agente de triagem do Daisugi. Posso te ajudar diretamente, ou, te direcionar a alguma outra sala, me diga o que precisa.")
    if not st.session_state.messages:
        st.session_state.messages = [{
            "role": "assistant",
            "content": msg_boas_vindas,
            "arquivo_anexo": None,
            "link_dw": None,
            "codigo_rastreamento": None
        }]

    # Layout Dividido (Claude Style com Artefato/Renderizador à Esquerda)
    if st.session_state.get("active_artifact"):
        # Suporte a expansão: quando expandido, o documento ocupa 75% e o chat 25%; quando normal, 50% / 50%
        if st.session_state.get("artifact_expanded", False):
            artifact_pane, chat_pane = st.columns([2.5, 1.0], gap="medium")
        else:
            artifact_pane, chat_pane = st.columns([1.0, 1.0], gap="medium")
    else:
        artifact_pane = None
        chat_pane = st.container()

    avatar_img = config.get("avatar", {}).get("imagem_lobby", "lobby_avatar.jpg")
    icone_usuario = config.get("avatar", {}).get("icone_usuario", "👤")
    dai_avatar = get_base64_image(avatar_img) if os.path.exists(avatar_img) else "👩🏻‍💼"

    with chat_pane:

        for idx_msg, message in enumerate(st.session_state.messages):
            av = dai_avatar if message["role"] == "assistant" else icone_usuario
            with st.chat_message(message["role"], avatar=av):
                st.markdown(message["content"])
                
                if message.get("link_dw"):
                    dw = message["link_dw"]
                    c_att1, c_att2 = st.columns([3, 1])
                    with c_att1:
                        st.markdown(f"""
                        <div class='attachment-card'>
                            <span style='font-size: 1.5rem;'>🏛️</span>
                            <div style='flex: 1;'>
                                <div style='font-weight: 700; color: #38bdf8;'>{dw.get('titulo', 'Documento no Data Warehouse')}</div>
                                <div style='font-size: 0.75rem; color: #94a3b8;'>HDW Soberano | Cota: <code>{dw.get('cota', 'EST-01-DOC')}</code> | Hash: <code>{dw.get('hash', 'e24de050a3f8')[:16]}...</code></div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    with c_att2:
                        st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
                        if st.button("Abrir Painel ➔", key=f"btn_art_dw_{idx_msg}", use_container_width=True):
                            ano_alvo_msg = "2025"
                            c_tit = dw.get('titulo', '')
                            for y in ["2021", "2022", "2023", "2024", "2025"]:
                                if y in c_tit:
                                    ano_alvo_msg = y
                                    break
                            st.session_state.active_artifact = {
                                "tipo": "laudo_html",
                                "ano": ano_alvo_msg,
                                "titulo": dw.get('titulo', f'Laudo Executivo M4 — {ano_alvo_msg} (Controle de Endividamento)'),
                                "cota": dw.get('cota', f'EST-01-KANSA-{ano_alvo_msg}-M4'),
                                "hash": dw.get('hash', 'e24de050a3f8a4e320f77bc954f62024765d1dcb74c43169f4bc7210e74bcfc4'),
                                "origem": "CentOS 7 - 10.8.0.1:8000"
                            }
                            st.rerun()

                if message.get("arquivo_anexo"):
                    anexo = message["arquivo_anexo"]
                    c_an1, c_an2 = st.columns([3, 1])
                    with c_an1:
                        st.markdown(f"""
                        <div class='attachment-card' style='border-color: rgba(16, 185, 129, 0.4);'>
                            <span style='font-size: 1.5rem;'>📑</span>
                            <div style='flex: 1;'>
                                <div style='font-weight: 700; color: #34d399;'>{anexo.get('nome', 'Comprovante_Atendimento.pdf')}</div>
                                <div style='font-size: 0.75rem; color: #94a3b8;'>Formato: {anexo.get('tipo', 'PDF')} | Tamanho: {anexo.get('tamanho', '142 KB')} | {anexo.get('status', 'Emitido')}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    with c_an2:
                        st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
                        if st.button("Visualizar ➔", key=f"btn_art_anexo_{idx_msg}", use_container_width=True):
                            st.session_state.active_artifact = {
                                "tipo": "laudo_pdf",
                                "titulo": anexo.get('nome', 'Comprovante_Atendimento.pdf'),
                                "cota": "REC-DAI-2026-COMP",
                                "hash": "a1b2c3d4e5f67890123456789abcdef0",
                                "origem": "DAI Reception Framework",
                                "conteudo": f"### Comprovante Oficial Emitido pela DAI\n\n**Arquivo:** {anexo.get('nome')}\n\n**Status:** Autenticado e carimbado temporalmente na recepção inteligente com perfil Zero Trust."
                            }
                            st.rerun()

        prompt_usuario = None
        if st.session_state.quick_prompt_selecionado:
            prompt_usuario = st.session_state.quick_prompt_selecionado
            st.session_state.quick_prompt_selecionado = None
        else:
            dica_input = config.get("textos", {}).get("dica_input_chat", "Converse com a Dai ou solicite acesso a documentos e módulos...")
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
            with st.spinner("台 Dai acolhendo sua solicitação via infraestrutura soberana..."):
                try:
                    headers = {"Content-Type": "application/json"}
                    token_jwt = st.session_state.get("token_jwt")
                    if token_jwt:
                        headers["Authorization"] = f"Bearer {token_jwt}"

                    history_msgs = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages if m.get("content")]
                    payload = {
                        "model": "dai-soberana-oci",
                        "wbs_id": "WBS-SUG-014",
                        "messages": history_msgs,
                        "temperature": 0.0
                    }

                    res = requests.post(
                        f"{API_BASE_URL}/api/v1/chat/completions/stream",
                        json=payload,
                        headers=headers,
                        stream=True,
                        timeout=25
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

                        # Se o prompt ou resposta mencionar laudo, relatório, dívida, acórdão ou documento no HDW, abre automaticamente o Painel Lateral
                        link_dw_novo = None
                        p_lower = prompt_usuario.lower()
                        termos_doc = ["laudo", "relatorio", "relatório", "divida", "dívida", "endividamento", "hdw", "documento", "kansa", "kan-sa", "ccb", "fatura", "acórdão", "acordao", "2021", "2022", "2023", "2024", "2025"]
                        
                        if any(k in p_lower for k in termos_doc):
                            # Identifica o ano solicitado se houver
                            ano_alvo = "2024" if "2024" in p_lower else ("2023" if "2023" in p_lower else ("2022" if "2022" in p_lower else ("2021" if "2021" in p_lower else "2025")))
                            info_ano_alvo = DADOS_EXERCICIOS.get(ano_alvo, {})
                            
                            link_dw_novo = {
                                "titulo": f"Laudo Executivo M4 — {ano_alvo} (Controle de Endividamento)",
                                "repositorio": "HDW Soberano (CentOS 7)",
                                "cota": f"EST-01-KANSA-{ano_alvo}-M4",
                                "hash": "e24de050a3f8a4e320f77bc954f62024765d1dcb74c43169f4bc7210e74bcfc4"
                            }
                            st.session_state.active_artifact = {
                                "tipo": "laudo_html",
                                "ano": ano_alvo,
                                "titulo": f"Laudo Executivo M4 — {ano_alvo} (Controle de Endividamento)",
                                "cota": f"EST-01-KANSA-{ano_alvo}-M4",
                                "hash": "e24de050a3f8a4e320f77bc954f62024765d1dcb74c43169f4bc7210e74bcfc4",
                                "origem": "Hudson Data Warehouse (CentOS 7 - 10.8.0.1:8000)"
                            }

                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": texto_resposta,
                            "arquivo_anexo": None,
                            "link_dw": link_dw_novo,
                            "codigo_rastreamento": f"DAI-RESP-{int(time.time())}"
                        })
                        st.rerun()
                    else:
                        # Fallback de Triage Expressa
                        res_tr = requests.post(
                            f"{API_BASE_URL}/chat/triage",
                            json={"texto_usuario": prompt_usuario, "id_usuario": st.session_state.get("paciente_id", 1)},
                            timeout=6
                        )
                        if res_tr.status_code == 200:
                            d_tr = res_tr.json()
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": d_tr.get("resposta_dai", "Atendimento registrado."),
                                "arquivo_anexo": d_tr.get("arquivo_anexo"),
                                "link_dw": d_tr.get("link_documento_dw"),
                                "codigo_rastreamento": d_tr.get("codigo_rastreamento")
                            })
                            st.rerun()
                        else:
                            st.error("❌ Falha de comunicação com o Cérebro da Dai.")
                except Exception as e:
                    st.error(f"❌ Falha de comunicação com a Dai: {e}")

    # ==========================================================
    # PAINEL LATERAL DE ARTEFATOS / DOCUMENTO (CLAUDE SPLIT-VIEW)
    # ==========================================================
    if artifact_pane and st.session_state.get("active_artifact"):
        art = st.session_state.active_artifact
        ano_doc = str(art.get("ano", "2025"))
        pdf_doc, html_doc, acordao_doc = obter_arquivos_exercicio(ano_doc)

        with artifact_pane:
            st.markdown(f"""
            <div class='artifact-container'>
                <div class='artifact-header'>
                    <div>
                        <span class='artifact-badge'>🏛️ CUSTODIADO NO HDW SOBERANO</span>
                        <div style='font-size: 1.15rem; font-weight: 800; color: #f8fafc; margin-top: 6px;'>{art.get('titulo', 'Documento Ativo')}</div>
                        <div style='font-size: 0.76rem; color: #94a3b8;'>Origem: {art.get('origem', 'CentOS 7 - 10.8.0.1:8000')}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            c_btn_a, c_btn_b, c_btn_c = st.columns([1, 1, 1])
            if c_btn_a.button("✖ Fechar", key="btn_close_artifact", use_container_width=True):
                st.session_state.active_artifact = None
                st.session_state.artifact_expanded = False
                st.rerun()
            
            label_exp = "🗗 Restaurar" if st.session_state.get("artifact_expanded", False) else "🗖 Expandir"
            if c_btn_b.button(label_exp, key="btn_toggle_expand_art", use_container_width=True):
                st.session_state.artifact_expanded = not st.session_state.get("artifact_expanded", False)
                st.rerun()

            if c_btn_c.button("📁 Ver Kan-sa", key="btn_goto_kansa_art", use_container_width=True):
                st.session_state.aba_ativa = "📁 監査 Kan-sa (Pasta & Laudos Oficiais)"
                st.rerun()

            st.markdown("---")
            
            # Carregar conteúdo HTML para o laudo se existir
            conteudo_html = ""
            html_b64_art = ""
            if html_doc and os.path.exists(html_doc):
                try:
                    with open(html_doc, "r", encoding="utf-8") as hf:
                        conteudo_html = hf.read()
                    html_b64_art = base64.b64encode(conteudo_html.encode("utf-8")).decode("utf-8")
                except Exception as ex_h:
                    st.warning(f"Aviso ao ler HTML: {ex_h}")

            # Barra de Ações Rápidas do Laudo Ativo
            c_act1, c_act2, c_act3 = st.columns([1.2, 1.2, 1.2])
            with c_act1:
                if html_b64_art:
                    st.markdown(
                        f"<a href='data:text/html;base64,{html_b64_art}' target='_blank' style='display: block; text-align: center; background: #0284c7; color: white; padding: 7px 6px; border-radius: 8px; text-decoration: none; font-size: 0.8rem; font-weight: 700;'>🌐 Abrir HTML ↗</a>",
                        unsafe_allow_html=True
                    )
                else:
                    st.caption("Link HTML N/D")

            with c_act2:
                if pdf_doc and os.path.exists(pdf_doc):
                    try:
                        with open(pdf_doc, "rb") as pf:
                            b_pdf = pf.read()
                        st.download_button(
                            label=f"📥 Baixar PDF ({len(b_pdf)/1024/1024:.1f}MB)",
                            data=b_pdf,
                            file_name=f"LAUDO_EXECUTIVO_M4_CONTROLE_ENDIVIDAMENTO_{ano_doc}.pdf",
                            mime="application/pdf",
                            key="btn_dl_pdf_artifact_pane",
                            use_container_width=True,
                            type="primary"
                        )
                    except Exception:
                        st.button("⚠️ PDF N/D", disabled=True, use_container_width=True, key="btn_dis_pdf_art")
                else:
                    st.button("⚠️ PDF N/D", disabled=True, use_container_width=True, key="btn_dis_pdf_art")

            with c_act3:
                st.markdown(
                    f"<a href='{SHAREPOINT_URL_HDW}' target='_blank' style='display: block; text-align: center; background: #1e293b; color: #38bdf8; border: 1px solid #38bdf8; padding: 7px 4px; border-radius: 8px; text-decoration: none; font-size: 0.8rem; font-weight: 700;'>📂 SharePoint ↗</a>",
                    unsafe_allow_html=True
                )

            st.markdown(f"**Cota Canônica:** `{art.get('cota', f'EST-01-KANSA-{ano_doc}-M4')}`")
            st.markdown(f"**Hash SHA-256:** `{art.get('hash', 'e24de050a3f8a4e320f77bc954f62024')}`")
            st.markdown("---")
            
            # Exibição do Conteúdo do Documento no Quadrante
            if art.get("tipo") == "kansa_folder":
                renderizar_pasta_kansa("painel_lateral")
            elif art.get("tipo") in ["hdw_doc", "laudo_html", "laudo_m4"] or conteudo_html:
                if conteudo_html:
                    st.components.v1.html(conteudo_html, height=650, scrolling=True)
                else:
                    st.markdown(art.get("conteudo", "Conteúdo não disponível."))
            else:
                st.markdown(art.get("conteudo", "Conteúdo não disponível."))
            
            st.markdown("</div>", unsafe_allow_html=True)

# ABA HDW: BIBLIOTECA MULTIDISCIPLINAR E CUSTÓDIA SOBERANA
# ==========================================
elif st.session_state.aba_ativa == "🏛️ Biblioteca HDW (Custódia Soberana)":
    st.markdown("""
    <div class='kansa-header-banner' style='border-left: 5px solid #38bdf8;'>
        <div style='display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 12px;'>
            <div>
                <span style='color: #38bdf8; font-size: 0.82rem; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;'>
                    Hudson Data Warehouse (HDW Soberano - Linux CentOS 7)
                </span>
                <h2 style='color: #ffffff; margin: 4px 0 6px 0; font-size: 1.8rem; font-weight: 800;'>
                    🏛️ Biblioteca Multidisciplinar & Cofre de Evidências
                </h2>
                <p style='color: #94a3b8; font-size: 0.92rem; margin: 0; max-width: 850px;'>
                    Acervo documental soberano categorizado por Estantes Canônicas (EST-01 a EST-06) e Árvore WBS.
                    Transmissão não-bloqueante em streaming (1 MiB), cota canônica determinística e validação de autenticidade em tempo real.
                </p>
            </div>
            <div style='text-align: right;'>
                <span style='display: inline-block; background: rgba(56, 189, 248, 0.2); border: 1px solid #38bdf8; color: #38bdf8; font-size: 0.82rem; padding: 6px 14px; border-radius: 20px; font-weight: 700; margin-bottom: 6px;'>
                    🔒 Enlace: OpenVPN mTLS (OCI × 192.168.1.122)
                </span><br/>
                <span style='color: #cbd5e1; font-size: 0.8rem;'>Integridade Criptográfica: <strong>SHA-256 Inviolável</strong></span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 1. Obter Estantes do HDW via API Backend
    try:
        r_estantes = requests.get(f"{API_BASE_URL}/api/v1/hdw/estantes", timeout=3)
        if r_estantes.status_code == 200:
            estantes_data = r_estantes.json().get("estantes", [])
        else:
            estantes_data = []
    except Exception:
        estantes_data = []

    if not estantes_data:
        st.warning("⚠️ Não foi possível obter o catálogo de estantes diretamente da API. Verifique a conectividade com o backend.")
    else:
        # Seletor de Estante Canônica
        opcoes_estantes = [f"{e['id']} — {e['nome']}" for e in estantes_data]
        estante_sel_str = st.selectbox("📚 Selecione a Estante Canônica da Biblioteca:", opcoes_estantes)
        estante_id_sel = estante_sel_str.split(" — ")[0]
        estante_meta = next((e for e in estantes_data if e["id"] == estante_id_sel), {})

        # Detalhes da Estante Selecionada
        c_e1, c_e2, c_e3 = st.columns([1.5, 1.5, 1])
        with c_e1:
            st.markdown(f"**Disciplinas:** {estante_meta.get('disciplinas', 'Geral')}")
            st.markdown(f"**Descrição:** *{estante_meta.get('descricao', '')}*")
        with c_e2:
            exts = ", ".join(estante_meta.get('extensoes', []))
            st.markdown(f"**Extensões Homologadas:** `{exts}`")
            st.markdown(f"**Visualizador Recomendado:** `{estante_meta.get('viewer_tipo', 'PDF')}`")
        with c_e3:
            sigilo = estante_meta.get('sigilo_padrao', 'INTERNO')
            cor_sigilo = "#10b981" if sigilo == "INTERNO" else ("#f59e0b" if sigilo == "RESTRITO" else "#ef4444")
            st.markdown(f"**Nível de Sigilo:** <span style='background: rgba(255,255,255,0.1); color: {cor_sigilo}; padding: 3px 8px; border-radius: 6px; font-weight: 700;'>{sigilo}</span>", unsafe_allow_html=True)

        st.markdown("---")

        # 2. Listagem de Documentos da Estante
        try:
            r_itens = requests.get(f"{API_BASE_URL}/api/v1/hdw/estantes/{estante_id_sel}/itens", timeout=3)
            itens_lista = r_itens.json().get("itens", []) if r_itens.status_code == 200 else []
        except Exception:
            itens_lista = []

        st.markdown(f"### 📑 Acervo Custodiado — {estante_meta.get('nome')} ({len(itens_lista)} documentos)")

        for doc in itens_lista:
            cota = doc.get("cota", "")
            nome_doc = doc.get("nome_arquivo", "")
            tam_mb = round(doc.get("tamanho_bytes", 0) / (1024 * 1024), 2)
            hash_doc = doc.get("hash_sha256", "")
            data_cust = doc.get("data_custodia", "")
            wbs_doc = doc.get("wbs_id", "")

            with st.container():
                st.markdown(f"""
                <div style='background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 14px; margin-bottom: 12px;'>
                    <div style='display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;'>
                        <div>
                            <span style='background: #38bdf8; color: #0B192C; font-weight: 800; font-size: 0.75rem; padding: 2px 8px; border-radius: 6px;'>{cota}</span>
                            <h4 style='margin: 6px 0 2px 0; color: #ffffff;'>📄 {nome_doc}</h4>
                            <span style='color: #94a3b8; font-size: 0.8rem;'>WBS: <strong>{wbs_doc}</strong> | Tamanho: <strong>{tam_mb} MB</strong> | Data Custódia: <strong>{data_cust}</strong></span>
                        </div>
                    </div>
                    <div style='margin-top: 8px;'>
                        <code style='font-size: 0.72rem; color: #cbd5e1; word-break: break-all; background: #0b192c; padding: 4px 8px; border-radius: 4px; display: block;'>SHA-256: {hash_doc}</code>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                col_b1, col_b2, col_b3 = st.columns([1.5, 1.5, 1])
                with col_b1:
                    if st.button(f"👁️ Visualizar Arquivo (Streaming HDW)", key=f"btn_render_{cota}", use_container_width=True):
                        st.session_state[f"show_preview_{cota}"] = not st.session_state.get(f"show_preview_{cota}", False)
                with col_b2:
                    if st.button(f"🛡️ Validar Autenticidade Forense", key=f"btn_auth_{cota}", use_container_width=True):
                        with st.spinner("Dr. Taylor auditando hash SHA-256 no disco do HDW..."):
                            try:
                                r_auth = requests.post(
                                    f"{API_BASE_URL}/api/v1/forensics/authenticity",
                                    json={"cota_documento": cota, "hash_esperado": hash_doc},
                                    timeout=5
                                )
                                if r_auth.status_code == 200:
                                    st.session_state[f"certidao_{cota}"] = r_auth.json()
                                else:
                                    st.error(f"Erro na auditoria: {r_auth.text}")
                            except Exception as ex_auth:
                                st.error(f"Falha de conexão com a rota /authenticity: {ex_auth}")
                with col_b3:
                    url_stream_direta = f"{API_BASE_URL}/api/v1/hdw/documentos/{cota}/render"
                    st.markdown(f"<a href='{url_stream_direta}' target='_blank' style='display: block; text-align: center; background: #1e293b; color: #38bdf8; border: 1px solid #38bdf8; padding: 7px; border-radius: 8px; text-decoration: none; font-size: 0.85rem; font-weight: 600;'>🔗 Stream Direto ↗</a>", unsafe_allow_html=True)

                # Exibição da Certidão Forense se solicitada
                if st.session_state.get(f"certidao_{cota}"):
                    cert = st.session_state[f"certidao_{cota}"]
                    st.success(f"⚖️ **CERTIDÃO FORENSE EMITIDA:** {cert.get('status')} | Veredito: {cert.get('veredito')}")
                    st.json(cert)

                # Exibição do Visualizador em Streaming se solicitado
                if st.session_state.get(f"show_preview_{cota}"):
                    with st.expander(f"Visualizador de Documento — {nome_doc}", expanded=True):
                        st.info(f"Transmitindo streaming seguro (1 MiB chunks) da rota `/api/v1/hdw/documentos/{cota}/render`.")
                        url_render = f"{API_BASE_URL}/api/v1/hdw/documentos/{cota}/render"
                        st.markdown(f'<iframe src="{url_render}" width="100%" height="600px" style="border: 1px solid rgba(255,255,255,0.1); border-radius: 8px;"></iframe>', unsafe_allow_html=True)

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

    renderizar_pasta_kansa("aba_cheia")

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
