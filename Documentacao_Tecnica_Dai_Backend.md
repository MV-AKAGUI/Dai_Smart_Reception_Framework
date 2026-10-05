# ⚙️ Documentação Técnica Oficial: Dai Smart Reception Framework (Back-End)

A **Dai** atua como o framework inteligente de **Front-End de Triagem (Lobby) e Roteamento Corporativo Multi-Tenant**, projetada com foco em segurança estrita (RBAC), isolamento de dados em múltiplos tenants, tolerância à ambiguidade (Lógica Fuzzy) e imunidade a alucinações de LLMs.

Esta documentação detalha a arquitetura completa do motor de back-end (`api_backend.py`), seus contratos de dados, pipelines assíncronos e o ciclo de evolução contínua da inteligência.

---

## 1. Stack Tecnológico de Produção

| Componente | Tecnologia | Papel no Ecossistema |
|---|---|---|
| **API Framework** | FastAPI (Python 3.11+) | Orquestrador REST/ASGI assíncrono de alta vazão e documentação OpenAPI nativa. |
| **Banco Relacional & Vetorial** | PostgreSQL 16 + `pgvector` | Armazenamento de identidades, matrizes de acesso e busca vetorial euclidiana (L2). |
| **Camada de Cache Ultrarrápido** | Redis (O(1)) / Mock integrado | Armazena em memória hashes de queixas já resolvidas, mitigando gargalos no RAG. |
| **Motor de Embeddings** | `nomic-embed-text` (768 dimensões) | Converte texto cru em representações matemáticas compactas sem custo de inferência generativa. |
| **Segurança e RBAC** | HTTP Bearer + JWT com Claims | Controle de acesso baseado em papéis (Operator, Tenant Client, Auditor). |
| **Desacoplamento Assíncrono** | FastAPI `BackgroundTasks` | Libera a interface imediatamente (HTTP 202 Accepted) enquanto processos pesados rodam em background. |

---

## 2. Arquitetura Topológica Completa: Oracle Cloud, Dai, Kan-sa & Hudson

Abaixo está o mapeamento dos nós, caixas e tráfego de dados do ecossistema, detalhando o que roda **dentro** do contêiner Docker no Oracle e o que é consumido de forma assíncrona **fora** via barramento de APIs:

```mermaid
flowchart TB
    subgraph CLIENTE["📱 Dispositivos dos Usuários & Especialistas"]
        USER["Navegador Web / Mobile PWA<br/>(Celular, Tablet, Desktop)"]
    end

    subgraph INTERNET["🌐 Nuvem Pública & Conectividade"]
        DNS["DNS Registro.br<br/>daisugi.com.br / dai.daisugi.com.br"]
    end

    subgraph OCI["☁️ SERVIDOR ORACLE CLOUD (OCI - IP 137.131.151.74)"]
        subgraph GATEWAY["🔒 Borda & Segurança"]
            CADDY["Caddy Gateway 2 (TLS / SSL Automático)<br/>Portas 80 / 443"]
        end

        subgraph STACK_DAI["🛎️ ECOSSISTEMA DAI SMART RECEPTION (Docker Network)"]
            LOBBY["Front-End Lobby (Streamlit)<br/>Porta 8501: Mobile-First"]
            BACKEND["Back-End Dai (FastAPI)<br/>Porta 8001: RAG, RBAC & Assíncrono"]
            REDIS["Redis Cache O(1)<br/>Hash Check de Queixas"]
            FUZZY["RapidFuzz & Fuzzy Harness<br/>Threshold 0.3 Anti-Alucinação"]
        end

        subgraph BANCO_DADOS["💾 PERSISTÊNCIA RELACIONAL & VETORIAL"]
            PG["PostgreSQL 16 + pgvector<br/>(Volume NVMe Isolado)"]
            MEM_GLOBAL["memoria_global_daisugi<br/>(Sabedoria Coletiva)"]
            MEM_CLIENTE["memoria_{cliente}<br/>(Isolamento B2B)"]
            TAB_USUARIOS["usuarios, clientes, salas"]
        end

        subgraph INTEGRACOES_ORACLE["🏢 MICROSSERVIÇOS CORPORATIVOS DAISUGI"]
            KANSA["DAISUGI KAN-SA (Porta 8000)<br/>Auditoria Forense de Passivos & CCBs"]
            HUDSON["HUDSON (Porta 9000)<br/>Orquestrador & Webhook Event Hub"]
        end
    end

    subgraph EXTERNO_IA["⚡ INTELIGÊNCIA EM NUVEM EXTERNA (Zero GPU na Oracle)"]
        GEMINI["Google Gemini API (1.5 Flash / 2.0 Flash)<br/>Clínico Geral & Especialistas (400ms)"]
        EMBED_API["Embeddings API (text-embedding-004)<br/>Vetorização 768 Dimensões"]
        GITHUB["GitHub Repository & CI/CD<br/>MV-AKAGUI / Sincronização"]
    end

    USER -->|HTTPS 443| DNS --> CADDY
    CADDY -->|dai.daisugi.com.br| LOBBY
    CADDY -->|/api/*| BACKEND
    CADDY -->|kansa.daisugi.com.br| KANSA

    LOBBY <-->|JSON Rest| BACKEND
    BACKEND <-->|O(1) Hash Cache| REDIS
    BACKEND <-->|Validação Local C++| FUZZY
    BACKEND <-->|SQL & Vetores L2| PG

    PG --- MEM_GLOBAL
    PG --- MEM_CLIENTE
    PG --- TAB_USUARIOS

    BACKEND -.->|Quarentena Desacoplada 202| KANSA
    BACKEND -.->|Notificação Assíncrona Webhook| HUDSON
    KANSA -.->|Eventos & Laudos| HUDSON

    BACKEND -->|Inferência Rápida REST| GEMINI
    BACKEND -->|Geração de Embeddings| EMBED_API

    GITHUB -.->|Deploy Contínuo Git Pull| OCI
```

---

### 2.1. Papel dos Nós e Integração Entre os Sistemas

* **Dai Smart Reception (Portas 8501 e 8001):**
  Porta de entrada universal. Recebe a queixa do usuário, valida a identidade via RBAC, verifica se a queixa já existe no **Redis Cache O(1)** e, se for nova, realiza a busca semântica no **PostgreSQL com `pgvector`**.
* **RapidFuzz & Fuzzy Harness:**
  Opera dentro da memória do container backend. Se a busca vetorial tiver distância $\ge 0.3$, o Fuzzy trava o roteamento automático e aciona a entrevista de 3 perguntas.
* **Integração com o KAN-SA (Porta 8000):**
  Documentos sensíveis, debêntures e conciliações contábeis que caem na recepção são direcionados para a rota de **Quarentena**. A Dai despacha a tarefa de forma assíncrona (HTTP 202) para o Kan-sa, sem travar a interface da recepção.
* **Integração com o HUDSON (Porta 9000):**
  Atua como o **Event Hub / Orquestrador Central**. Recebe webhooks tanto da Dai quanto do Kan-sa informando status de triagens, laudos gerados e alertas de segurança.
* **Gemini API (Clínico Geral em Nuvem):**
  Fornece a inferência neural profunda sem exigir placa de vídeo (GPU) da Oracle, garantindo respostas em 400ms e custo quase nulo.

---

## 3. Mecanismos Centrais de Inteligência e Performance

### 3.1. Proteção de Cache O(1) (Mitigação de Gargalo RAG)
O RAG vetorial e a extensão `pgvector` são extremamente rápidos para milhares de registros, porém requisições idênticas repetidas não devem bater no banco relacional nem no gerador de embeddings.
- Cada texto de queixa gera um hash MD5 determinístico: `hash_prompt = hashlib.md5(prompt.encode()).hexdigest()`.
- O back-end consulta a chave no cache Redis em tempo $O(1)$.
- Em caso de **Cache Hit**, a rota devolve a resposta instantaneamente com `cache_hit: true`, economizando ciclos de CPU e conexões de banco de dados.

### 3.2. O Fuzzy Harness Semântico (Trava Anti-Alucinação)
Diferente de sistemas legados que usam similaridade ortográfica (Levenshtein), a Dai utiliza **Fuzzy Semântico Vetorial**:
- O vetor da queixa atual ($\vec{v}$) é comparado com os vetores do banco histórico via distância euclidiana (`<->`).
- **Limiar de Alta Certeza ($\text{distancia} < 0.3$):** A queixa é matematicamente análoga a uma resolução anterior homologada. A Dai despacha a resposta e desbloqueia a Sala correspondente.
- **Limiar de Ambiguidade / Dúvida ($\text{distancia} \ge 0.3$):** A queixa é ambígua ou inédita. O sistema recusa-se a alucinar ou "chutar", acionando o **Protocolo Universal de Refinamento (3 Perguntas)**:
  1. **(i) O QUE** você precisa resolver?
  2. **(ii) COMO** espera que a equipe ajude?
  3. **(iii) POR QUE** isso é uma prioridade agora?
- Quando o usuário responde, um novo vetor muito mais denso e representativo é gerado, cruzando o limiar de 0.3 na iteração seguinte.

### 3.3. RAG Híbrido e Isolamento Físico de Tenants
Para evitar o risco de vazamento de dados entre empresas (Data Leakage) e ao mesmo tempo permitir que a inteligência operacional beneficie todos:
1. **Memória Global Coletiva (`memoria_global_daisugi`):** Tabela pública de conhecimento geral e procedimental (dúvidas de navegação, reset de credenciais, normas gerais).
2. **Memórias Isoladas de Clientes (`memoria_{cliente}`):** Cada cliente corporativo (ex: `memoria_controladoria`, `memoria_juridico`) tem sua tabela estritamente particionada.
3. **Query Dinâmica com `UNION ALL`:** Ao realizar a triagem, o back-end lê os IDs de clientes aos quais o usuário logado pertence na tabela relacional `usuario_clientes` e monta uma busca combinada:
   ```sql
   (SELECT texto_original, destino, 'Global' as cliente_destino, embedding <-> '[...]'::vector AS distancia FROM memoria_global_daisugi ORDER BY distancia ASC LIMIT 1)
   UNION ALL
   (SELECT texto_original, destino, 'controladoria' as cliente_destino, embedding <-> '[...]'::vector AS distancia FROM memoria_controladoria ORDER BY distancia ASC LIMIT 1)
   ORDER BY distancia ASC LIMIT 1;
   ```
   Dessa forma, o usuário jamais enxerga ou busca em tabelas de tenants que não pertencem à sua credencial.

---

## 4. Segurança, RBAC e Desacoplamento Assíncrono

### 4.1. Controle de Acesso Baseado em Papéis (RBAC)
O endpoint crítico de auditoria e validação é protegido pelo decorator de injeção de dependência `verify_operator_role`.
- Requisições sem o token apropriado são barradas imediatamente com código **HTTP 403 Forbidden**.
- Mensagem padronizada de bloqueio: `Privilege Escalation Detectado: Acesso negado. Token não possui a claim 'role: operator'`.

### 4.2. Desacoplamento Temporal da Quarentena (HTTP 202 Accepted)
Auditorias periciais de documentos pesados (como as CCBs, debêntures e conciliações do **Kan-sa**) podem levar de minutos a horas para processar.
- A rota `/api/quarentena/validar` recebe o hash do documento e aprovação.
- O FastAPI adiciona a tarefa pesada à fila em segundo plano (`BackgroundTasks.add_task(processar_auditoria_kansa_async)`).
- A API retorna imediatamente o status **HTTP 202 Accepted** para a interface.
- O usuário e a interface continuam livres e responsivos (zero travamento de tela / sem *hanging request*), enquanto o worker executa o processamento e notifica o orquestrador (Hudson) via webhook na conclusão.

---

## 5. Especificação dos Endpoints REST

### 5.1. `POST /auth/login`
Autentica o usuário e devolve seu perfil, salas dinâmicas liberadas e o token JWT correspondente.
- **Request:**
  ```json
  {
    "usuario": "admin",
    "senha": "123"
  }
  ```
- **Response (HTTP 200):**
  ```json
  {
    "autenticado": true,
    "id_usuario": 1,
    "nome": "Administrador Operador",
    "perfil": "admin",
    "salas_liberadas": [
      { "nome": "Painel Quarentena", "funcao": "Validação de Risco", "cor": "#EF4444" }
    ],
    "clientes_acesso": ["1", "2"],
    "token_jwt": "token_jwt_operador_secreto"
  }
  ```

### 5.2. `POST /chat/triage`
Executa o fluxo de triagem semântica, validação de cache e acionamento da Lógica Fuzzy.
- **Request:**
  ```json
  {
    "id_usuario": 1,
    "texto_usuario": "A internet da filial 2 caiu totalmente"
  }
  ```
- **Response (HTTP 200 - Rota Concluída):**
  ```json
  {
    "status_fuzzy": false,
    "destino": "Sala Suporte Redes",
    "cliente_destino": "controladoria",
    "resposta_dai": "🔍 Busca RAG concluída. Sala **Sala Suporte Redes** (controladoria).",
    "laudo_final": "✅ Triagem Concluída.",
    "cache_hit": false
  }
  ```
- **Response (HTTP 200 - Falso Fuzzy / Refinamento Necessário):**
  ```json
  {
    "status_fuzzy": true,
    "destino": null,
    "cliente_destino": null,
    "resposta_dai": "Para que eu direcione corretamente:\n(i) O QUE você precisa?\n(ii) COMO podemos ajudar?\n(iii) POR QUE é prioridade?",
    "laudo_final": "⚠️ Triagem Inconclusiva.",
    "cache_hit": false
  }
  ```

### 5.3. `POST /triage/learn`
Registra a evolução do conhecimento após a resolução de um ticket por um especialista humano ou agente autônomo.
- **Request:**
  ```json
  {
    "texto_usuario": "A internet da filial 2 caiu totalmente",
    "destino_final": "Sala Suporte Redes",
    "cliente_destino": "controladoria",
    "resolucao_especialista": "Troca de roteador de borda e reativação da rota de contingência 4G",
    "is_global": false
  }
  ```
- **Response (HTTP 200):**
  ```json
  {
    "status": "sucesso",
    "mensagem": "A Dai evoluiu. Nova trilha sináptica criada na Memória Isolada (controladoria)."
  }
  ```

### 5.4. `POST /api/quarentena/validar`
Recebe laudos de quarentena documental com autenticação de operador e despacha a auditoria assíncrona.
- **Headers:** `Authorization: Bearer <token_jwt_operador_secreto>`
- **Request:**
  ```json
  {
    "hash_id_documento": "a3f5b72189d0c64e5...",
    "aprovado": true
  }
  ```
- **Response (HTTP 202 Accepted):**
  ```json
  {
    "status_http": 202,
    "message": "Solicitação aceita. O pacote JSON leve foi recebido e o Kan-sa assumiu a tarefa em segundo plano.",
    "hash_processado": "a3f5b72189d0c64e5..."
  }
  ```

### 5.5. `GET /health`
Probe de liveness e readiness para orquestradores de contêiner e balanceadores de carga.
- **Response (HTTP 200):**
  ```json
  {
    "status": "HEALTHY",
    "sistema": "Dai Smart Reception API",
    "embedder_ativo": true,
    "cache_redis_itens": 1,
    "timestamp": 1728085600.0
  }
  ```

---

## 6. Variáveis de Ambiente e Configuração

O backend é 100% configurável via variáveis de ambiente, permitindo transição suave entre ambiente local e nuvem:

| Variável | Padrão | Descrição |
|---|---|---|
| `PORT` | `8001` | Porta TCP em que o servidor Uvicorn escuta. |
| `DB_HOST` | `localhost` | Host do banco de dados PostgreSQL. |
| `DB_PORT` | `5432` | Porta TCP do PostgreSQL. |
| `DB_NAME` | `memoria_vetorial` | Nome do banco relacional com extensão `pgvector`. |
| `DB_USER` | `admin` | Usuário com permissão DDL e DML. |
| `DB_PASSWORD` | `masterkey123` | Senha do usuário do banco de dados. |
| `OLLAMA_HOST` | `http://localhost:11434` | Endpoint do serviço Ollama para geração de embeddings. |
| `EMBED_MODEL` | `nomic-embed-text` | Modelo de embedding a ser invocado pelo LangChain. |
