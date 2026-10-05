# Status Oficial: Projeto Arquiteto Neural (Ferramentas, Fuzzy & Harness)
*Documento vivo atualizado com a Filosofia de Homeostase Computacional (Privacidade e Processamento Local)*

Este documento detalha o estágio atual de todas as aplicações e conceitos abordados no nosso roadmap, listando o que está rodando, o que está isolado e o que está operacional.

---

## 1. 🧠 Inteligência Artificial (Corpo Clínico Especializado & LLMs)
* **Ambiente de Execução:** Python 3.11.9 Oficial via `uv` (Sem conflitos de C-extensions).
* **Bibliotecas Base Operacionais no `.venv`:** `langgraph` (v1.2), `langchain` (v1.4), `langchain-ollama` (v1.1), `docling` (v2.133), `rapidfuzz` (v3.14.6), `scikit-learn` (v1.9.1), `chromadb` (v1.5.9), `torch` (v2.14.1+cpu).
* **Servidor Local de LLMs:** Ollama v0.35.1 (Porta 11434 - 100% Offline e Privado).
* **Modelos Oficiais Instalados e Ativos:**
  - **Llama 3.1 (4.9 GB):** O Maestro da Homeostase (**Dr. Taylor Code** - Roteador Central).
  - **DeepSeek-R1 8B (5.2 GB):** Especialista em Raciocínio Lógico (Chain-of-Thought), BPMN, fluxogramas, POPs, ITs e Workflows corporativos.
  - **Qwen 2.5 Coder 7B (4.7 GB):** Engenheiro de Software sênior, especialista em algoritmos complexos, refatoração e Python.
  - **SaulLM (4.4 GB):** O Dr. Jurídico (Contratos, conformidade e base legal).
  - **Qwen 2.5 (4.7 GB):** O Especialista Financeiro (Balanços, DREs, FP&A e modelagem numérica).
  - **Mistral-Nemo (7.1 GB):** O Investigador Sistêmico (Detecção de anomalias, lógica fuzzy e auditoria).
  - **Nomic-Embed-Text (274 MB):** Tradutor de embeddings vetoriais (768 dimensões) para o RAG.

## 2. 🎨 Orquestração Frontend e Chat (O Rosto)
* **Dify (Porta 80):** 🟢 Repositório clonado e configurado via Docker para testes de workflow no-code.
* **Streamlit (Porta 8001):** 🟢 Interface web visual ativa rodando `app_chat_st.py` com suporte à autenticação, corredor médico e triagem.
* **Comunicação:** 🟢 Integrado com roteamento de queixas e prontuário médico em tempo real.

## 3. 🔀 Roteamento Lógico (O Sistema Nervoso e Lógica Fuzzy)
* **Status:** 🟢 **100% Operacional.**
* **Implementação:** Arquivo `sistema_nervoso_langgraph.py` com grafo de estados (`PatientState`), nós especializados (`doctor_qwen`, `doctor_saul`, `doctor_mistral`) e roteador condicional com desfecho em Alta Médica (`alta_medica: True`).
* **Lógica Fuzzy:** Biblioteca `rapidfuzz` ativa para tolerância a ruídos em cadastros e nomes de fornecedores.

## 4. 🗄️ Memória de Longo Prazo e RAG (O Hipocampo)
* **Ferramentas:** PostgreSQL + extensão `pgvector` (via Docker na porta 5432) e ChromaDB local (v1.5.9).
* **Status de Instalação:** 🟢 Bancos configurados e drivers nativos (`psycopg2-binary`, `chromadb`) operacionais no Python 3.11.9.
* **Pipeline RAG:** Extrator *Docling* lendo documentos brutos + *Nomic-Embed-Text* gerando vetores + tabelas `dai_memoria` com cálculo de distância vetorial `<->`.

## 5. 🛠️ Microserviços de Extração e Integração (Os "Braços e Olhos")
*Todos rodando de forma isolada em contêineres Docker, respeitando a Homeostase Computacional.*
* **PaddleOCR (Porta 8000):** Córtex Visual para extração de texto de Notas Fiscais e imagens escaneadas (estabilizado com `libgomp1` em `./docker_paddleocr`).
* **SearXNG (Porta 8080):** Buscador web privado para investigações sem rastros comerciais.
* **n8n (Porta 5678):** Automações periféricas (webhooks, integrações e e-mails).

## 6. 🏭 Engenharia de Software e CI/CD (O Cofre de Código)
* **Ferramenta:** Harness Open Source / Gitness (via Docker na porta 3000/3022).
* **Status:** 🟢 Definido em `docker-compose-ferramentas.yml` com persistência de volumes (`gitness_data`).
* **Fábrica de Software:** MetaGPT configurado com a equipe completa (`ProductManager`, `Architect`, `ProjectManager`, `Engineer`, `QaEngineer`) e integrado ao Llama 3.1 local.

---

## 🎯 Conclusão de Integridade
Todo o maquinário (Hardware, Modelos Ollama, Python 3.11.9, LangGraph, Bancos e Harness) foi **revalidado, testado e está 100% alinhado com a governança da DAISUGI.**
