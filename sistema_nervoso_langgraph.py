import os
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama

# ==========================================
# 0. CONFIGURAÇÃO DE HOST E AMBIENTE (OCI / LOCAL)
# ==========================================
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# ==========================================
# 1. ESTADO DO GRAFO (A Ficha do Paciente)
# ==========================================
class PatientState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], "Histórico do chat"]
    assunto: str       # "software", "processos", "fiscal", "jurisprudencia", "financeiro", "juridico", "investigacao"
    alta_medica: bool  # Se True, encerra o ticket e gera o prontuário para a Dai

# ==========================================
# 2. DEFINIÇÃO DOS DOUTORES ESPECIALIZADOS
# ==========================================
# LLM Maestro (Dr. Taylor Code - Llama 3.1)
llm_maestro = ChatOllama(model="llama3.1", base_url=OLLAMA_HOST)

# Consultórios Especializados Oficiais
llm_qwen_coder = ChatOllama(model="qwen2.5-coder:7b", base_url=OLLAMA_HOST)
llm_deepseek_r1 = ChatOllama(model="deepseek-r1:8b", base_url=OLLAMA_HOST)
llm_qwen_fin = ChatOllama(model="qwen2.5", base_url=OLLAMA_HOST)
llm_saul_jur = ChatOllama(model="saullm", base_url=OLLAMA_HOST)
llm_mistral_inv = ChatOllama(model="mistral-nemo", base_url=OLLAMA_HOST)

def doctor_qwen_coder(state: PatientState):
    """Consultório Dr. Qwen Coder: Engenharia de Software, Algoritmos e Python 3.11."""
    prompt = state["messages"][-1].content
    try:
        response = llm_qwen_coder.invoke(f"Você é o Dr. Qwen Coder, Engenheiro de Software Sênior e Especialista Python. Resolva: {prompt}")
        content = response.content
    except Exception as e:
        content = f"Dr. Qwen Coder (Modo Resiliente): Demanda técnica recebida: '{prompt}'. Encaminhando protocolo de engenharia."
    return {"messages": [AIMessage(content=content)], "alta_medica": True}

def doctor_deepseek_r1(state: PatientState):
    """Consultório Dr. DeepSeek-R1: Raciocínio Lógico (CoT), BPMN, POPs e ITs."""
    prompt = state["messages"][-1].content
    try:
        response = llm_deepseek_r1.invoke(f"Você é o Dr. DeepSeek-R1, Especialista em Processos BPMN, POPs e ITs. Analise com cadeia de raciocínio lógico: {prompt}")
        content = response.content
    except Exception as e:
        content = f"Dr. DeepSeek-R1 (Modo Resiliente): Mapeamento de fluxo de processo para: '{prompt}' registrado."
    return {"messages": [AIMessage(content=content)], "alta_medica": True}

def doctor_fiscal(state: PatientState):
    """Consultório Dra. Fiscal: ICMS, PIS/COFINS, SPED e Reforma Tributária."""
    prompt = state["messages"][-1].content
    try:
        response = llm_saul_jur.invoke(f"Você é a Dra. Fiscal, autoridade tributária e contábil em ICMS, PIS/COFINS, SPED e Reforma Tributária. Resolva: {prompt}")
        content = response.content
    except Exception as e:
        content = f"Dra. Fiscal (Modo Resiliente): Parecer tributário preliminar registrado para: '{prompt}'."
    return {"messages": [AIMessage(content=content)], "alta_medica": True}

def doctor_jurisprudencia(state: PatientState):
    """Consultório Dr. Precedente: Jurisprudência, Súmulas STF/STJ, Teses TST e Ementas."""
    prompt = state["messages"][-1].content
    try:
        response = llm_saul_jur.invoke(f"Você é o Dr. Precedente, Especialista em Jurisprudência dos Tribunais Superiores (STF, STJ, TST). Resolva: {prompt}")
        content = response.content
    except Exception as e:
        content = f"Dr. Precedente (Modo Resiliente): Análise de súmulas e teses preliminares para: '{prompt}'."
    return {"messages": [AIMessage(content=content)], "alta_medica": True}

def doctor_qwen(state: PatientState):
    """Consultório Financeiro: Balanços, DREs, FP&A e Modelagem Numérica."""
    prompt = state["messages"][-1].content
    try:
        response = llm_qwen_fin.invoke(f"Você é o Especialista Financeiro Qwen. Resolva: {prompt}")
        content = response.content
    except Exception as e:
        content = f"Especialista Financeiro Qwen (Modo Resiliente): Laudo financeiro para: '{prompt}'."
    return {"messages": [AIMessage(content=content)], "alta_medica": True}

def doctor_saul(state: PatientState):
    """Consultório Jurídico: Contratos, Pareceres e Conformidade Legal."""
    prompt = state["messages"][-1].content
    try:
        response = llm_saul_jur.invoke(f"Você é o Especialista Jurídico SaulLM. Resolva: {prompt}")
        content = response.content
    except Exception as e:
        content = f"Especialista Jurídico SaulLM (Modo Resiliente): Minuta jurídica para: '{prompt}'."
    return {"messages": [AIMessage(content=content)], "alta_medica": True}

def doctor_mistral(state: PatientState):
    """Consultório de Investigação & Auditoria: Lógica Fuzzy e Detecção de Anomalias."""
    prompt = state["messages"][-1].content
    try:
        response = llm_mistral_inv.invoke(f"Você é o Investigador Sistêmico Mistral-Nemo. Busque anomalias e realize auditoria pericial: {prompt}")
        content = response.content
    except Exception as e:
        content = f"Investigador Mistral-Nemo (Modo Resiliente): Varredura pericial de anomalias para: '{prompt}'."
    return {"messages": [AIMessage(content=content)], "alta_medica": True}

# ==========================================
# 3. O ROTEADOR INTELIGENTE (DR. TAYLOR CODE)
# ==========================================
def roteador(state: PatientState) -> str:
    """O Maestro Dr. Taylor (Llama 3.1) decide qual porta médica abrir."""
    if state.get("assunto"):
        assunto = state["assunto"].lower()
        if assunto in ["software", "processos", "fiscal", "jurisprudencia", "financeiro", "juridico", "investigacao"]:
            return assunto

    ultima_mensagem = state["messages"][-1].content
    decision_prompt = f"""
    Você é o Dr. Taylor Code, Maestro da Homeostase e Roteador Central da Clínica Dai.
    Leia a queixa do paciente e responda APENAS com UMA das palavras-chave abaixo:
    - software: se envolver programação, Python, código, bugs, APIs ou engenharia de software
    - processos: se envolver BPMN, fluxogramas, POPs, Instruções de Trabalho (ITs) ou cadeia de valor
    - fiscal: se envolver impostos, ICMS, PIS/COFINS, SPED, notas fiscais ou reforma tributária
    - jurisprudencia: se envolver tribunais superiores, precedentes, súmulas STF/STJ, ementas ou teses
    - financeiro: se envolver balanços, fluxo de caixa, DREs, endividamento ou lucros
    - juridico: se envolver contratos civis, minutas, escrituras ou direito imobiliário
    - investigacao: se envolver auditoria, detecção de anomalias ou fraudes

    Queixa: {ultima_mensagem}
    """
    try:
        resposta = llm_maestro.invoke(decision_prompt).content.strip().lower()
        for rot in ["software", "processos", "fiscal", "jurisprudencia", "financeiro", "juridico"]:
            if rot in resposta:
                return rot
        return "investigacao"
    except Exception:
        # Fallback heurístico inteligente se o Ollama estiver offline
        msg_l = ultima_mensagem.lower()
        if any(w in msg_l for w in ["python", "código", "software", "api", "bug"]): return "software"
        if any(w in msg_l for w in ["bpmn", "pop", "it", "fluxograma", "processo"]): return "processos"
        if any(w in msg_l for w in ["tribut", "imposto", "icms", "pis", "cofins", "sped"]): return "fiscal"
        if any(w in msg_l for w in ["súmula", "jurisprudência", "stf", "stj", "tst"]): return "jurisprudencia"
        if any(w in msg_l for w in ["dre", "balanço", "caixa", "financeir", "lucro"]): return "financeiro"
        if any(w in msg_l for w in ["contrato", "minuta", "cláusula", "jurídic"]): return "juridico"
        return "investigacao"

# ==========================================
# 4. CONSTRUINDO O SISTEMA NERVOSO (GRAFO LANGGRAPH)
# ==========================================
builder = StateGraph(PatientState)

# Adiciona todos os consultórios (Nós)
builder.add_node("software", doctor_qwen_coder)
builder.add_node("processos", doctor_deepseek_r1)
builder.add_node("fiscal", doctor_fiscal)
builder.add_node("jurisprudencia", doctor_jurisprudencia)
builder.add_node("financeiro", doctor_qwen)
builder.add_node("juridico", doctor_saul)
builder.add_node("investigacao", doctor_mistral)

# Define o roteamento dinâmico na entrada
builder.set_conditional_entry_point(
    roteador,
    {
        "software": "software",
        "processos": "processos",
        "fiscal": "fiscal",
        "jurisprudencia": "jurisprudencia",
        "financeiro": "financeiro",
        "juridico": "juridico",
        "investigacao": "investigacao"
    }
)

# Todos os nós convergem para Alta Médica com emissão de prontuário
builder.add_edge("software", END)
builder.add_edge("processos", END)
builder.add_edge("fiscal", END)
builder.add_edge("jurisprudencia", END)
builder.add_edge("financeiro", END)
builder.add_edge("juridico", END)
builder.add_edge("investigacao", END)

# Compila o Sistema Nervoso
sistema_nervoso = builder.compile()

if __name__ == "__main__":
    teste_input = {"messages": [HumanMessage(content="Preciso criar um script em Python 3.11 para validar hashes.")]}
    resultado = sistema_nervoso.invoke(teste_input)
    print("RESPOSTA FINAL DO CORPO CLÍNICO:", resultado["messages"][-1].content)
