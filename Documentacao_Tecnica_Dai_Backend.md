# Documentação Técnica: Dai Smart Reception Framework (Back-End)

A **Dai** atua como o framework de Front-End de Triagem (Lobby) e roteamento de usuários, desenhada com foco em segurança extrema, isolamento de dados e zero alucinação. Esta documentação detalha a arquitetura do motor de back-end que sustenta a inteligência e a memória do sistema.

---

## 1. Stack Tecnológico e Ferramentas Utilizadas

- **FastAPI:** Framework central do Back-End. Utilizado por sua alta performance e suporte nativo a rotas assíncronas.
- **PostgreSQL + pgvector:** Banco de dados relacional equipado com a extensão `pgvector`. Responsável por armazenar os "Prontuários" e atuar como o motor do nosso banco de dados vetorial (Vector DB).
- **LangChain & OllamaEmbeddings (`nomic-embed-text`):** Motor de conversão de texto para vetores (Embeddings).
- **Streamlit:** Framework de interface que atua como o "Rosto" (Lobby), focado em usabilidade móvel (Mobile-First) e design responsivo.

---

## 2. A Ferramenta Fuzzy e o "Fuzzy Harness"

### 2.1. O que é o nosso Fuzzy?
Diferente de sistemas clássicos que usam lógica difusa de texto (como *Levenshtein* ou bibliotecas como *TheFuzz*), a Dai utiliza um **Fuzzy Semântico de Alta Precisão**, impulsionado pela extensão **`pgvector`** e o cálculo de **Distância Euclidiana (L2 Distance, operador `<->`)**. 

### 2.2. O Fuzzy Harness (A Trava de Segurança)
O **Fuzzy Harness** é a arquitetura de contenção anti-alucinação da Dai.
Na etapa de triagem, a queixa do usuário é vetorizada e o `pgvector` realiza a busca. O **Harness** (a trava) está configurado no limite de distância: **`distancia < 0.3`**.

- **Por que usamos essa abordagem?** Para **blindar** o sistema. LLMs (Grandes Modelos de Linguagem) têm a tendência de "adivinhar" respostas quando não sabem. Ao usar matemática vetorial estrita (pgvector) antes de acionar um LLM, nós retiramos do modelo a capacidade de adivinhar. 
- **O Protocolo de Segurança:** Se a distância do vetor for maior que 0.3, a busca é considerada "Inconclusiva". A trava é ativada e a Dai se recusa a rotear o usuário, acionando o Protocolo Universal de Refinamento com as três perguntas investigativas:
  1. **O Quê** você precisa resolver?
  2. **Como** espera que a equipe ajude?
  3. **Por Que** isso é uma prioridade agora?

Isso força a criação de um bloco de texto muito mais rico. Quando o usuário responde, o novo vetor ganha precisão milimétrica, garantindo segurança no roteamento.

---

## 3. Isolamento Multi-Tenant e Segurança de Dados

Para assegurar que as informações (Prontuários e RAG) de um cliente B2B nunca cruzem com as de outro cliente, a Dai utiliza **Isolamento Físico de Memória**.

- Em vez de uma tabela gigante onde dados se misturam, o banco de dados cria fisicamente tabelas isoladas: `memoria_controladoria`, `memoria_juridico`, etc.
- **Segurança de Consulta Simultânea:** O back-end lê a matriz de permissões do usuário logado (Tabela `usuario_clientes`) e monta uma query SQL dinâmica utilizando `UNION ALL` **apenas** nas tabelas que o usuário tem acesso. Isso elimina o risco de "Data Leakage" (Vazamento de dados) via prompt injection.

---

## 4. O Prontuário, Memória e Evolução (RAG)

A inteligência da Dai não vem de pré-treinamentos fixos, mas sim de uma **Evolução Contínua via Prontuário**.

1. **Geração do Prontuário:** A queixa inicial somada às respostas das 3 perguntas universais formam o Prontuário do usuário.
2. **Resolução:** O especialista (Dr. Taylor Code, Dr. Qwen, etc) nas salas específicas (Corredores) realiza o atendimento e encerra a demanda.
3. **Aprendizado da Máquina (Lastro):** A rota `/triage/learn` é acionada. O Prontuário completo + a Solução do especialista são vetorizados e gravados na tabela `memoria_<cliente>`.
4. **Ciclo de Segurança:** No próximo atendimento similar, o `pgvector` encontrará esse Prontuário com `distancia < 0.3`. A Dai poderá então resolver a questão instantaneamente no Lobby, esvaziando a fila dos especialistas. Esta evolução acontece em banco de dados isolado (RAG) sem precisar re-treinar ou expor dados para APIs de Inteligência Artificial externas.

---

## 5. Conclusão de Segurança
A segurança do framework baseia-se em **reduzir a dependência de inferência livre de IA** na camada de atendimento primário. A Dai substitui o processamento em nuvem de LLMs por validação matemática (pgvector), transformando um processo sujeito a "alucinações" em uma engenharia de triagem exata, determinística e baseada unicamente no próprio lastro histórico corporativo.
