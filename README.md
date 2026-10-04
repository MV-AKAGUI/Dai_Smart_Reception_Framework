# 🏥 Dai Smart Reception Framework

> **A "Home Page" Evoluiu.** Transforme a porta de entrada da sua empresa em uma Recepção Inteligente, Autônoma e Altamente Eficiente.

O **Dai Smart Reception Framework** é uma arquitetura de inteligência artificial open-source criada para atuar como o **Standard de Home Page** (o ponto central de atendimento e roteamento) para sistemas corporativos. Em vez de portais estáticos com menus confusos, o usuário interage diretamente com a **Dai**, uma recepcionista inteligente que conduz o paciente/cliente para a área correta da empresa de forma autônoma.

---

## 🌟 Premissa: A Dai como Standard de Home Page

Na arquitetura tradicional, o usuário precisa descobrir sozinho qual botão apertar. Com o framework da Dai, a Home Page passa a ser um **balcão de atendimento interativo**:
1. O usuário relata seu problema de forma orgânica.
2. A Dai faz a triagem baseada no histórico corporativo.
3. O usuário é teletransportado (roteado) para o corredor correto com o Especialista (Humano ou LLM) que irá resolver a dor.

## 🛠️ Recursos e Arquitetura Principal

### 1. 🎨 White-Label e Tematização Dinâmica
O front-end é 100% desacoplado. Não há strings ou cores *hardcoded*. Toda a interface visual, nomes, avatares e saudações são consumidos de um único arquivo `config_cliente.json`, permitindo o "reskin" completo do sistema para qualquer cliente (Clínicas, Escritórios de Advocacia, Setores de TI) em segundos.

### 2. ⚡ Triagem Zero-RAM (Eficiência e Custo)
A arquitetura é projetada para **depender menos de inferência pesada de LLM**.
Quando a Dai recebe uma mensagem, o sistema **não invoca um LLM** imediatamente:
* Ele traduz a frase em um vetor usando um modelo de Embeddings leve (`nomic-embed-text`).
* Realiza uma busca de Similaridade Vetorial (RAG) instantânea no PostgreSQL (`pgvector`).
* Apenas casos que não têm alta similaridade vetorial matemática sobem para o cérebro principal. Isso impede o colapso de memória (RAM) e "travas" sistêmicas, suportando milhares de interações em paralelo.

### 3. 🧠 Lógica Fuzzy para Refinamento
Se o sistema possui dúvida no roteamento (Matematicamente a distância vetorial é `>= 0.3`), ele não "chuta" uma resposta e não alucina. A Lógica Fuzzy impõe que a Dai faça um refinamento exigindo as respostas de **O QUE**, **COMO** e **POR QUE** antes de perturbar os Especialistas (LLMs pesados ou atendentes humanos reais).

### 4. 🔒 Homeostase Computacional
Todo o ambiente foi arquitetado para ser independente e rodar 100% em infraestrutura local (On-Premise) ou Nuvem Privada via Docker/Podman, garantindo total controle sobre os dados dos clientes e mitigando vazamentos.

---

## 🚀 Como Iniciar

1. Clone o repositório.
2. Certifique-se de que o **PostgreSQL (com pgvector)** está rodando na porta `5432` com as credenciais padrão do framework.
3. Instale os requisitos Python e certifique-se de possuir o servidor do **Ollama** rodando.
4. Ajuste as informações e o logotipo da sua empresa no `config_cliente.json`.
5. Execute a interface da Recepção:
   ```bash
   streamlit run app_chat_st.py
   ```

---
*Construído com ❤️ e Lógica pela Daisugi Tecnologias.*
