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

## 3. Arquitetura de RAG Híbrido (Isolamento Multi-Tenant e Memória Global)

A grande inovação arquitetural da Dai é seu **RAG Híbrido**. Para garantir que a sabedoria coletiva beneficie todos os clientes da Daisugi, sem comprometer a confidencialidade de dados (Data Leakage), nós separamos as memórias em dois níveis:

### 3.1. Memória Global Coletiva (`memoria_global_daisugi`)
Uma tabela de uso geral contendo resoluções anonimizadas e procedimentais (Ex: *Como resetar a senha, dúvidas sobre a plataforma Daisugi*). Qualquer aprendizado salvo aqui passa a beneficiar **todos** os usuários instantaneamente.

### 3.2. Memórias Isoladas de Clientes (Isolamento Físico Nível 2)
Para cada cliente B2B da Daisugi, é criada uma tabela física no banco (Ex: `memoria_controladoria`, `memoria_juridico`). Se o especialista definir que um atendimento contém dados sensíveis (contratos, compliance interno), a inteligência vai apenas para essa tabela. O isolamento é absoluto.

### 3.3. Segurança de Consulta Simultânea (A União)
O back-end lê a matriz de permissões do usuário logado e monta uma query SQL dinâmica utilizando `UNION ALL`. A matemática busca o vetor do usuário **simultaneamente** na `memoria_global_daisugi` e apenas nas tabelas de clientes que ele tem permissão de acesso. Isso elimina o risco de vazamento, cruzamento indevido ou prompt injection.

---

## 4. O Prontuário, Memória e Evolução (RAG)

A inteligência da Dai não vem de pré-treinamentos fixos, mas sim de uma **Evolução Contínua via Prontuário**.

1. **Geração do Prontuário:** A queixa inicial somada às respostas das 3 perguntas universais formam o Prontuário do usuário.
2. **Resolução:** O especialista (Dr. Taylor Code, Dr. Qwen, etc) nas salas específicas (Corredores) realiza o atendimento e encerra a demanda.
3. **Aprendizado da Máquina (Lastro):** A rota `/triage/learn` é acionada. O Prontuário completo + a Solução do especialista são vetorizados. O especialista decide no formulário de encerramento:
   - Se for conhecimento Genérico/Operacional, envia (com `is_global=true`) para a `memoria_global_daisugi`.
   - Se for conhecimento Sensível/Restrito, envia para a `memoria_<cliente>` (Tabela isolada).
4. **Ciclo de Segurança Híbrido:** No próximo atendimento, o `pgvector` buscará simultaneamente na rede global e nas redes restritas daquele usuário. Encontrando um Prontuário com `distancia < 0.3`, a Dai resolve o ticket na recepção. Esta evolução constante permite que a plataforma inteira cresça coletivamente em inteligência, preservando o sigilo corporativo.

---

## 5. Conclusão de Segurança
A segurança do framework baseia-se em **reduzir a dependência de inferência livre de IA** na camada de atendimento primário. A Dai substitui o processamento em nuvem de LLMs por validação matemática (pgvector), transformando um processo sujeito a "alucinações" em uma engenharia de triagem exata, determinística e baseada unicamente no próprio lastro histórico corporativo.
