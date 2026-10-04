# Status Oficial: Projeto Arquiteto Neural (Ferramentas, Fuzzy & Harness)
*Documento vivo atualizado com a Filosofia de Homeostase Computacional (Privacidade e Processamento Local)*

Este documento detalha o estágio atual de todas as aplicações e conceitos abordados no nosso roadmap, listando o que está rodando, o que está isolado e o que falta conectar.

---

## 1. 🧠 Inteligência Artificial (Os "Doutores" e o Roteador)
* **Ferramentas Básicas Instaladas no `.venv`:** `langgraph`, `langchain`, `langchain-ollama`, `docling`, `rapidfuzz`.
* **Ferramenta de IA:** Ollama (Servidor Local de LLMs).
* **Status de Instalação:** 🟢 100% Instalado e Funcional nos bastidores.
* **Componentes Baixados:**
  - **Llama 3.1:** O Cérebro Generalista e "Maestro" do roteamento.
  - **SaulLM (O Dr. Jurídico):** Especialista em leis, contratos e jargões do direito.
  - **Qwen 2.5 (O Especialista Financeiro):** Analista de balanços, DREs, FP&A e números empresariais.
  - **Mistral-Nemo (O Investigador):** Visão sistêmica, faro investigativo e cruzamento de informações.
  - **Nomic-Embed-Text:** O tradutor silencioso que gera embeddings vetoriais.

## 2. 🎨 Orquestração Frontend e Chat (O Rosto)
* **Dify (Porta 80):** 🟢 Rodando estavelmente via Docker. Interface no-code de testes de workflow e repositório inicial da persona do Dr. Taylor Code.
* **Streamlit (Porta 8001):** 🟢 Servidor ativo rodando `app_chat_st.py`.
* **Comunicação:** 🔴 "Casca Vazia". O campo de texto no Streamlit existe, mas não processa a mensagem até o LangGraph ser programado.

## 3. 🔀 Roteamento Lógico (O Sistema Nervoso e Lógica Fuzzy)
* **Status:** 🟡 A biblioteca base do LangGraph e o motor de Lógica Fuzzy (`rapidfuzz`) foram 100% instalados.
* **O que falta:** Precisamos escrever as regras do LangGraph para que ele intercepte a mensagem do Streamlit e decida de forma flexível: *"É sobre finanças? Envie para o Qwen. É sobre processo? Envie para o Dr. Saul."*

## 4. 🗄️ Memória de Longo Prazo e RAG (O Cofre de Arquivos)
* **Ferramentas:** PostgreSQL + extensão `pgvector` (via Docker na porta 5432).
* **Status de Instalação:** 🟢 100% Instalado e Rodando.
* **Comunicação:** 🔴 Banco vazio e isolado.
* **O que falta:** Escrever o script que pega seus PDFs locais, usa o *Docling* para ler o texto, transforma em vetores com o *Nomic* e salva dentro do *Postgres*.

## 5. 🛠️ Microserviços de Extração e Integração (Os "Braços e Olhos")
*Todos rodando de forma isolada em contêineres Docker, respeitando a Homeostase Computacional.*
* **PaddleOCR (A porta 8000):** O nosso "Olho" para extrair textos de Notas Fiscais e imagens escaneadas. 🟢 Instalado e Estável (Bug de colapso de memória resolvido com injeção de `libgomp1`).
* **SearXNG (A porta 8080):** O "Buscador Anônimo". Permite pesquisar na internet sem vazar dados. 🟢 Instalado.
* **n8n (A porta 5678):** A nossa "Secretária de Automação", para integrar com e-mails, webhooks, etc. 🟢 Instalado.

## 6. 🏭 Engenharia de Software e CI/CD (O Gerente da Fábrica)
* **Ferramenta:** Harness Open Source / Gitness (via Docker na porta 3000).
* **Status de Instalação:** 🟢 100% Instalado.
* **Comunicação:** 🟡 Operando como "Cofre de Código" independente no momento. Onde nossos códigos do VSCode estão indo com segurança.

---

## 🎯 Conclusão e Ordem de Ação
Toda a infraestrutura, bibliotecas de fundação (`langchain-ollama`, `rapidfuzz`) e o maquinário de "Hardware simulado" (Docker, Bancos, Modelos, UI, Dify) foi **montada com sucesso e está operante. Nenhum alerta vermelho.**

**Próxima Tarefa Lógica:**
1. **(Ação Imediata)** Escrever a lógica do LangGraph no arquivo `app_chat_st.py` para os especialistas ganharem voz no chat.
