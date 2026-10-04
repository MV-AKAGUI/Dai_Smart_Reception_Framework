import os
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama

# ==========================================
# 1. ESTADO DO GRAFO (A Ficha do Paciente)
# ==========================================
class PatientState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], "Historico do chat"]
    assunto: str       # "financeiro", "juridico", "investigacao"
    alta_medica: bool  # Se True, encerra o ticket e gera o prontuário para a Dai

# ==========================================
# 2. DEFINIÇÃO DOS DOUTORES (NÓS)
# ==========================================
# LLM Base: Usaremos o Llama 3.1 como Maestro (por enquanto)
llm_maestro = ChatOllama(model="llama3.1")

def doctor_qwen(state: PatientState):
    """Especialista Financeiro"""
    prompt = state["messages"][-1].content
    # Aqui conectaremos o Qwen no futuro. 
    # Por agora, usamos o LLM disponível como placeholder.
    response = llm_maestro.invoke(f"Você é o Especialista Financeiro Qwen. Resolva: {prompt}")
    
    return {
        "messages": [AIMessage(content=response.content)],
        "alta_medica": True # Marca que o caso foi resolvido
    }

def doctor_saul(state: PatientState):
    """Especialista Jurídico"""
    prompt = state["messages"][-1].content
    response = llm_maestro.invoke(f"Você é o Especialista Jurídico SaulLM. Resolva: {prompt}")
    
    return {
        "messages": [AIMessage(content=response.content)],
        "alta_medica": True
    }

def doctor_mistral(state: PatientState):
    """Especialista Investigador (Nemo)"""
    prompt = state["messages"][-1].content
    response = llm_maestro.invoke(f"Você é o Investigador Mistral-Nemo. Busque anomalias: {prompt}")
    
    return {
        "messages": [AIMessage(content=response.content)],
        "alta_medica": True
    }

# ==========================================
# 3. O ROTEADOR INTELIGENTE (O CORREDOR)
# ==========================================
def roteador(state: PatientState):
    """O Llama 3.1 decide qual porta abrir se a Dai falhar na triagem."""
    # Se a Dai já mandou o assunto preenchido, usamos ele.
    if state.get("assunto"):
        return state["assunto"]
    
    # Se a Dai não sabe, o Llama lê a mensagem e toma a decisão
    ultima_mensagem = state["messages"][-1].content
    decision_prompt = f"""
    Leia a queixa do paciente e responda APENAS com UMA PALAVRA:
    - Se envolver leis, regras ou contratos, responda: juridico
    - Se envolver dinheiro, planilhas ou lucros, responda: financeiro
    - Se envolver pesquisa, anomalias ou dúvidas abertas, responda: investigacao
    
    Queixa: {ultima_mensagem}
    """
    
    # O Llama faz a triagem profunda
    resposta = llm_maestro.invoke(decision_prompt).content.strip().lower()
    
    if "juridico" in resposta: return "juridico"
    elif "financeiro" in resposta: return "financeiro"
    else: return "investigacao"


# ==========================================
# 4. CONSTRUINDO O SISTEMA NERVOSO (GRAFO)
# ==========================================
builder = StateGraph(PatientState)

# Adiciona os consultórios (Nós)
builder.add_node("financeiro", doctor_qwen)
builder.add_node("juridico", doctor_saul)
builder.add_node("investigacao", doctor_mistral)

# Define o roteamento automático a partir da entrada
builder.set_conditional_entry_point(
    roteador,
    {
        "financeiro": "financeiro",
        "juridico": "juridico",
        "investigacao": "investigacao"
    }
)

# Todos terminam na saída (Alta Médica)
builder.add_edge("financeiro", END)
builder.add_edge("juridico", END)
builder.add_edge("investigacao", END)

# Compila o Sistema Nervoso
sistema_nervoso = builder.compile()

# Opcional: print para testar
if __name__ == "__main__":
    teste_input = {"messages": [HumanMessage(content="Quero analisar a DRE deste trimestre.")]}
    resultado = sistema_nervoso.invoke(teste_input)
    print("RESPOSTA FINAL:", resultado["messages"][-1].content)
