# ☁️ Arquitetura de Infraestrutura em Nuvem: Servidor Oracle Cloud (OCI) & Ecossistema DAISUGI

**Autor:** Equipe de Engenharia e Infraestrutura Cloud DAISUGI  
**Servidor Alvo:** Oracle Cloud Infrastructure (OCI) - IP `137.131.151.74`  
**Região:** `sa-saopaulo-1` (São Paulo, Brasil)  
**Domínio Raiz:** `daisugi.com.br`  

---

## 1. Diagnóstico Pericial: O Que Foi Feito no `02_Daisugi_kan-sa`

Ao analisar minuciosamente o repositório `02_Daisugi_kan-sa` (em especial os documentos de arquitetura, scripts de implantação e o `docker-compose.yml`), identificamos a seguinte configuração traçada para a máquina de produção:

*   **Instância Provisionada:** `daisugi-core-prod` (`137.131.151.74`).
*   **Sistema Operacional:** Ubuntu 24.04 Minimal LTS.
*   **Shape de Hardware:** `VM.Standard.E2.1.Micro` (1 OCPU AMD, **1 GB de memória RAM**, 50 GB Boot Volume) sob o plano *Always Free*.
*   **Containers Projetados no Docker Compose:**
    1.  `postgres:16-alpine` (Banco relacional contábil/pericial).
    2.  `backend` (FastAPI em Python 3.12/3.14 com Uvicorn).
    3.  `frontend` (Next.js 14 SSR com Node.js).
    4.  `daisugi-ai` (Serviço de IA com Docling e LangChain na porta 5000).
    5.  `caddy` (Proxy reverso para roteamento e certificados TLS automáticos).

---

## 2. Causa Raiz: Por Que o Back-End do Kan-sa Falhou no Servidor Oracle?

A causa dos problemas no back-end e no deploy do Kan-sa na Oracle foi uma combinação de **três fatores críticos de infraestrutura**:

### 2.1. O Gargalo Fatal de Memória RAM (OOM Killer do Linux)
*   A máquina possui apenas **1.024 MB (1 GB) de memória RAM**.
*   **Consumo Real da Stack Projetada:**
    *   *Kernel do Ubuntu:* ~150 MB.
    *   *PostgreSQL 16:* ~150 MB a 250 MB.
    *   *FastAPI Backend (Python + libs):* ~200 MB a 350 MB.
    *   *Next.js 14 Frontend:* ~400 MB a 800 MB (podendo ultrapassar 1,5 GB durante o comando `npm run build`).
    *   *Docling Hub (PyTorch/OCR):* Requer no mínimo **4 GB a 8 GB de RAM** para carregar pesos neurais.
*   **O que aconteceu:** Ao executar `docker compose up --build`, a memória física esgotou-se em segundos. O kernel do Linux disparou o **OOM-Killer (Out of Memory Killer)**, matando silenciosamente o processo do Uvicorn ou do PostgreSQL, ou travando a conexão SSH da máquina por completo. Como o Ubuntu da Oracle não vem com memória Swap configurada por padrão, qualquer pico acima de 1 GB derruba o sistema.

### 2.2. Variável de Ambiente do Frontend com `localhost`
No arquivo `docker-compose.yml` do Kan-sa:
```yaml
environment:
  - NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```
*   Variáveis que começam com `NEXT_PUBLIC_` são embutidas no código JavaScript que roda no **navegador do usuário** (client-side).
*   Quando um usuário externo tentava usar o sistema pelo navegador, o front tentava chamar `http://localhost:8000`, que apontava para a própria máquina do cliente em vez do IP ou domínio da Oracle (`137.131.151.74`), gerando erro de `Connection Refused` ou `Failed to fetch`.

### 2.3. Firewall Duplo da Oracle (Security List + iptables)
*   A OCI possui firewall na camada de rede virtual (Security List na VCN).
*   Além disso, as imagens oficiais do Ubuntu na Oracle vêm com regras internas de `iptables` ativas que **bloqueiam portas de entrada** mesmo que a Security List esteja aberta. É necessário sincronizar as portas ou descarregar o tráfego no Caddy nas portas 80 e 443.

---

## 3. A Estratégia de Ouro: Como Destravar a Nuvem Oracle

Existem dois caminhos práticos para resolver isso de forma definitiva:

### 🏆 OPÇÃO A (Recomendação Máxima): A Mina de Ouro do Always Free (Ampere A1 Flex)
A Oracle Cloud possui o plano gratuito mais generoso do mundo para instâncias **ARM Ampere A1 (`VM.Standard.A1.Flex`)**:
*   **Recursos 100% Gratuitos e Perpétuos:**
    *   **Até 4 OCPUs (núcleos de processador)**.
    *   **Até 24 GB de memória RAM**.
    *   **Até 200 GB de armazenamento NVMe em bloco**.
*   **Impacto no Ecossistema:**
    Se você criar uma instância com esse shape (ou redimensionar), seus 1 GB de RAM saltam para **24 GB de RAM**. 
    Nessa máquina de 24 GB rodam com folga total:
    *   ✅ O banco PostgreSQL 16 com `pgvector`.
    *   ✅ O Redis Cache em memória.
    *   ✅ O backend do Kan-sa (FastAPI).
    *   ✅ O frontend do Kan-sa (Next.js).
    *   ✅ O backend da Dai (FastAPI).
    *   ✅ O frontend da Dai (Streamlit ou PWA).
    *   ✅ O motor de IA (Docling / embeddings locais).
    *   ✅ O proxy reverso Caddy com SSL.

### 🛠️ OPÇÃO B: Hardening Extremo da VM Atual de 1 GB (E2.1.Micro)
Se você optar por manter a instância atual de 1 GB sem recriá-la, precisamos aplicar as seguintes regras de sobrevivência:
1.  **Criar Swap de 4 GB** no disco da máquina para o Linux ter margem de alocação:
    ```bash
    sudo fallocate -l 4G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    ```
2.  **Não rodar IA pesada localmente:** Em vez de subir Ollama e Docling na VM, conectar via API externa (Gemini API para embeddings com `text-embedding-004` e inferência).
3.  **Não compilar o Next.js dentro do servidor:** Fazer o build na máquina local ou GitHub Actions e enviar apenas os arquivos estáticos ou imagem Docker pronta para a Oracle.
4.  **Limitar a memória de cada container no Compose:** Definir `mem_limit: 256m` para evitar que um container derrube os outros.

---

## 4. Topologia de Ancoragem da DAI e KAN-SA no Servidor

Para que o sistema **não dependa da sua máquina física** e rode 24 horas por dia, 7 dias por semana com alta segurança e agilidade:

```mermaid
flowchart TB
    subgraph CLIENTE["📱 Dispositivos (Mobile / Web)"]
        USER["Usuários & Especialistas"]
    end

    subgraph OCI["☁️ SERVIDOR ORACLE CLOUD (OCI - IP 137.131.151.74)"]
        CADDY["🔒 Caddy Gateway 2 (TLS / SSL Automático)<br/>Portas 80 / 443"]

        subgraph DAI_CONTAINERS["🛎️ ECOSSISTEMA DAI"]
            DAI_FRONT["Lobby Front-End (Streamlit)<br/>Porta 8501"]
            DAI_BACK["API Back-End (FastAPI)<br/>Porta 8001 (RBAC, Fuzzy, Cache O(1))"]
        end

        subgraph KANSA_CONTAINERS["📊 ECOSSISTEMA KAN-SA"]
            KANSA_FRONT["Next.js Front-End<br/>Porta 3000"]
            KANSA_BACK["FastAPI Back-End<br/>Porta 8000 (Passivos & CCBs)"]
        end

        subgraph HUDSON_CONTAINERS["🤖 ECOSSISTEMA HUDSON"]
            HUDSON_CORE["Hudson Event Hub & Webhook<br/>Porta 9000 (Orquestrador)"]
        end

        subgraph DADOS["💾 BANCO POSTGRESQL 16 ENTERPRISE"]
            PG["PostgreSQL 16 + pgvector<br/>(Bancos: memoria_vetorial + sugoi_endividamento)"]
        end
    end

    subgraph CLOUD_AI["⚡ CLOUD AI EXTERNA (Sem Sobrecarga de RAM na OCI)"]
        GEMINI["Google Gemini API (1.5 Flash / 2.0 Flash)<br/>Clínico Geral & Laudos Rápidos (400ms)"]
    end

    USER -->|HTTPS 443| CADDY
    CADDY -->|dai.daisugi.com.br| DAI_FRONT
    CADDY -->|/api/*| DAI_BACK
    CADDY -->|kansa.daisugi.com.br| KANSA_FRONT
    CADDY -->|kansa-api...| KANSA_BACK
    CADDY -->|hudson.daisugi.com.br| HUDSON_CORE

    DAI_FRONT <--> DAI_BACK
    DAI_BACK <--> PG
    KANSA_BACK <--> PG

    DAI_BACK -.->|Quarentena Assíncrona 202| KANSA_BACK
    DAI_BACK -.->|Disparo de Webhook| HUDSON_CORE
    KANSA_BACK -.->|Eventos & Laudos| HUDSON_CORE

    DAI_BACK -->|Inferência REST| GEMINI
```

---

## 5. Roteamento de Subdomínios e Configuração Caddy (`Caddyfile`)

O servidor Caddy gerencia os certificados SSL Let's Encrypt automaticamente para todos os subdomínios:

```caddyfile
# -------------------------------------------------------------
# 1. KAN-SA: Auditoria, Passivos e Governança
# -------------------------------------------------------------
kansa.daisugi.com.br {
    reverse_proxy localhost:3000

    handle /api/v1/* {
        reverse_proxy localhost:8000
    }
}

# -------------------------------------------------------------
# 2. DAI: Recepção Inteligente, Triagem e Lobby
# -------------------------------------------------------------
dai.daisugi.com.br {
    reverse_proxy localhost:8501

    handle /api/* {
        reverse_proxy localhost:8001
    }
}

# -------------------------------------------------------------
# 3. HUDSON: Orquestrador & Webhook Central
# -------------------------------------------------------------
hudson.daisugi.com.br {
    reverse_proxy localhost:9000
}

# -------------------------------------------------------------
# 4. TRONCO-MÃE: Plataforma Geral DAISUGI
# -------------------------------------------------------------
daisugi.com.br {
    root * /var/www/daisugi
    file_server
}
```

---

## 6. Procedimento Passo a Passo para Subir a DAI no Servidor Oracle

### Passo 1: Acessar a Instância via SSH
```bash
ssh -i sua-chave-oracle.key ubuntu@137.131.151.74
```

### Passo 2: Liberar o Firewall Interno do Ubuntu para o Caddy
```bash
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save
```

### Passo 3: Clonar o Repositório da Dai no Servidor
```bash
cd /opt
sudo git clone https://github.com/MV-AKAGUI/Dai_Smart_Reception_Framework.git
cd Dai_Smart_Reception_Framework
```

### Passo 4: Criar o Arquivo de Variáveis de Produção (`.env`)
```bash
sudo cp .env.example .env
sudo nano .env
```
*(Preencher com as credenciais seguras de banco e JWT)*

### Passo 5: Inicializar os Serviços via Docker
```bash
sudo docker compose up -d --build
```

### Passo 6: Verificar Status e Logs
```bash
sudo docker compose ps
sudo docker compose logs -f api_backend
```

Pronto! A Dai e o Kan-sa passam a rodar ancorados na nuvem da Oracle, sem consumir bateria, RAM ou conexão da sua máquina física, com proteção de reinício automático (`restart: always`), banco isolado e conexão segura via HTTPS.
