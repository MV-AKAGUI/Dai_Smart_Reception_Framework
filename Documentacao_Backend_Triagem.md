# ⚙️ Documentação Técnica: Lógica de Back-End do Lobby (RAG & Fuzzy)

Este documento detalha o motor lógico que opera "por trás do balcão" do Lobby. A arquitetura de roteamento foi projetada para ter altíssima eficiência computacional (sem depender exclusivamente de inferência pesada de LLM) e extrema precisão na identificação da necessidade do usuário.

---

## 1. Fluxo de Autenticação e Perfil de Acesso
A triagem no Lobby é **Context-Aware** (Ciente do Contexto). Antes mesmo de processar uma requisição, o sistema identifica quem é o usuário.

*   **Identificação (Portaria):** O usuário faz o login.
*   **Injeção de Perfil:** O `st.session_state` armazena o Nome e o Perfil (ex: "Admin", "Desenvolvimento", "Cliente B2B").
*   **Isolamento de Salas (Segurança):** A renderização dinâmica (lado direito do Lobby) oculta fisicamente as salas que não pertencem ao perfil logado. Isso significa que, mesmo que o sistema de RAG recomende a sala "DevOps", se um "Cliente B2B" tentar acessar, a interface não renderizará o ponto de acesso, garantindo segurança na camada de visualização.

---

## 2. A "Mente" da Dai: Embeddings e pgvector (Primeira Camada)
O objetivo principal da arquitetura é rotear o usuário gastando o mínimo possível de recursos de máquina. Para isso, evitamos chamar a geração de texto do LLM para tarefas triviais, usando **Mapeamento Vetorial**.

1.  **O Banco de Dados (`pgvector`):** Utiliza-se um banco PostgreSQL com a extensão `vector`. Isso transforma o banco em uma "Mente Vetorial", capaz de realizar buscas por similaridade matemática.
2.  **O Processo de Embeddings:** Quando o usuário escreve uma queixa (ex: "A internet da filial 2 caiu"), o sistema usa o modelo `nomic-embed-text` (via Ollama) para converter essa frase em uma matriz numérica (um vetor de 768 dimensões).
3.  **A Matemática do Roteamento:** O banco de dados compara este novo vetor com os vetores já conhecidos no histórico (a "memória" da Dai). A busca utiliza a operação `<->` (Distância L2).

---

## 3. Limiares de Decisão (Thresholds) e a Lógica Fuzzy

O coração da tomada de decisão reside em como a Dai interpreta o cálculo de distância vetorial (`distancia`).

### A Lógica Fuzzy (Tolerância à Ambiguidade)
Na computação clássica, ou é 0 ou é 1. Na **Lógica Fuzzy**, trabalhamos com graus de incerteza. A Dai classifica o grau de certeza matemática do RAG em dois limiares:

*   **Limiar de Alta Certeza (Distância < 0.3):**
    *   *Interpretação:* A queixa atual é matematicamente quase idêntica a algo que já sabemos como resolver.
    *   *Ação (Fast-Track):* O sistema contorna o LLM, emite o Laudo de Triagem e destrava o acesso à Sala correta imediatamente. O usuário sente fluidez absoluta (fricção zero).

*   **Limiar de Ambiguidade / Dúvida (Distância >= 0.3):**
    *   *Interpretação:* O vetor está difuso. Pode pertencer a mais de uma sala ou não faz sentido.
    *   *Ação (Gatilho Fuzzy):* Em vez de "chutar" e errar, a Dai interrompe o roteamento automático e engaja o usuário em uma entrevista de refinamento. Ela dispara as 3 perguntas cruciais (O que, Como, Por que).
    *   *Resultado:* Ao responder as perguntas, o usuário concatena mais contexto. Um novo texto muito maior e mais rico é gerado, criando um vetor muito mais definido que, na próxima tentativa, cruzará a barreira do `0.3` com facilidade.

### Por que isso é importante?
1.  **Economia de Memória (RAM/VRAM):** Buscar vetores no PostgreSQL exige milissegundos de processamento de CPU. Chamar um Llama 3.1 para "adivinhar" o que o usuário quer consumiria gigabytes de VRAM e levaria segundos.
2.  **Proteção contra "Alucinação":** O roteamento é baseado em dados exatos (matemática vetorial), não na probabilidade de próxima palavra do LLM.
3.  **Escalabilidade B2B:** Empresas podem cadastrar milhares de fluxos de roteamento no banco sem pesar o sistema. O modelo de embeddings dá conta do recado sozinho.
