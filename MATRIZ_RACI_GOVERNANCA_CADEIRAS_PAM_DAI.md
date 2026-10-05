# 🏛️ MATRIZ RACI, MODELO DE CADEIRAS PAM/IGA E SEGURANÇA DA DAI

---

## 1. Contexto e Integração com o Modelo PAM/IGA SUGOI

Este documento estabelece o modelo corporativo de **Governança, Autenticação, Autorização e Matriz RACI** para o ecossistema da **DAI (Daisugi Smart Reception)**, integrando-se nativamente à arquitetura de **Cadeiras, Perfis e Gestão de Privilégios (PAM/IGA)** desenvolvida pela TI da SUGOI conforme especificado nos documentos base:
- `KT_Arquitetura_Cadeiras_Contratacao_SUGOI.docx`
- `SUGOI_Modelo_Gestao_PAM_R03.xlsx` (Abas *Arquitetura_Hierarquica*, *Catalogo_Cadeiras*, *Papéis RBAC*, *Matriz RACI* e *SoD*).

### 1.1 O Conceito de Cadeira na DAI: Funcional vs. Nominal
Na DAI, o acesso aos recursos, salas virtuais e painéis de auditoria não é concedido a uma pessoa física arbitrária, mas sim à **Cadeira** que ela ocupa no modelo corporativo:

```
+---------------------------------------------------------------------------------------------------+
|                                   ARQUITETURA DE CADEIRAS PAM/IGA                                 |
+---------------------------------------------------------------------------------------------------+
|  [ ARQUITETURA HIERÁRQUICA ]  ---> Código Setorial (Ex: 1.05 Controladoria / 1.1 Governança)       |
|            |                                                                                      |
|            v                                                                                      |
|  [ CADEIRA PRINCIPAL ]        ---> E-mail Funcional: <alcada>.<perfil>@sugoisa.com.br             |
|            |                       Ex: controller@sugoisa.com.br / diretor.operacoes@sugoisa.com.br|
|            v                                                                                      |
|  [ CADEIRA NOMINAL ]          ---> Identidade Individual: <nome>.<sobrenome>@sugoisa.com.br       |
|            |                       Ex: ronaldo.akagui@sugoisa.com.br                              |
|            v                                                                                      |
|  [ TOKEN JWT DA DAI ]         ---> Claims: { sub, cadeira_principal, alcada, perfil, role, tenant}|
+---------------------------------------------------------------------------------------------------+
```

1. **Cadeira Principal (Identificador Funcional)**: Representa a função e alçada dentro da hierarquia (ex: `controller@sugoisa.com.br`, `pmo.fpa@sugoisa.com.br`, `advogado.imobiliario@sugoisa.com.br`). Permanece constante mesmo com rotatividade de pessoas.
2. **Cadeira Nominal (Identidade do Operador/Usuário)**: Representa a pessoa física que ocupa a cadeira no momento (ex: `ronaldo.akagui@sugoisa.com.br`).
3. **Princípio do Menor Privilégio e Segregação de Funções (SoD)**: O acesso ao Painel de Quarentena e ao aprendizado da IA é restrito estritamente às alçadas qualificadas no Catálogo de Cadeiras.

---

## 2. Matriz RACI da DAI (Usuário, Especialista e Operador)

A matriz RACI define claramente os papéis em cada etapa do ciclo de vida da recepção, triagem e auditoria:
- **R (Responsible - Responsável)**: Quem executa a tarefa ou faz a solicitação na interface.
- **A (Accountable - Aprovador/Alçada)**: Quem tem autoridade final e responde pelo resultado da ação.
- **C (Consulted - Consultado)**: Especialistas e áreas que fornecem insumos, pareceres ou validações técnicas.
- **I (Informed - Informado)**: Partes que recebem logs imutáveis, notificações ou relatórios automáticos.

| ID | Macroprocesso / Etapa na DAI | R (Executa) | A (Aprova/Responde) | C (Consultado) | I (Notificado) |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **F01** | **Acolhimento & Identificação na Portaria**<br>*(Login no Lobby Streamlit via credencial PAM)* | Usuário Solicitante *(Colaborador / Terceiro)* | CISO / Administrador de IGA | RH (Gente & Gestão); TI Service Desk | Auditoria Interna; Log de Acesso |
| **F02** | **Triagem de Sintomas e Dúvidas**<br>*(Chat com a Mente da Dai / RAG e Trava Anti-Alucinação)* | Usuário Solicitante | Especialista da Cadeira de Destino | Base Vetorial PgVector; Cache Redis | Trilha de Auditoria do Atendimento |
| **F03** | **Encaminhamento para Sala Especializada**<br>*(Direcionamento do ticket/ficha de atendimento)* | Dai (Motor de Roteamento) | Gestor da Área de Destino | PMO de Governança / Especialista | Solicitante; Operador de Triagem |
| **F04** | **Validação de Hash CCB na Quarentena**<br>*(Desacoplamento Assíncrono HTTP 202 com Kan-sa)* | **Controller / Auditoria / Advogado** *(Cadeiras Checker)* | **Diretoria Financeira / Diretor de Operações** | Comitê de Investimentos; PMO de FP&A | Compliance; Kan-sa; Hudson; Solicitante |
| **F05** | **Aprendizado Contínuo (`/triage/learn`)**<br>*(Registro de nova sinapse no PgVector por especialista)* | Especialista da Cadeira *(Engenharia, Fiscal, Jurídico)* | Controller / CISO *(Governança de IA)* | Operador da Recepção; Solicitante Original | Toda a Rede Dai (se Global); Tenant |
| **F06** | **Gestão de Memória Multi-Tenant**<br>*(Isolamento rigoroso de bases entre clientes e SPEs)* | Administrador de Sistemas / ERP | CISO / DPO (LGPD) | Controladoria; Jurídico | Auditoria Independente; Diretoria |
| **F07** | **Gestão de Cofre PAM e Chaves JWT**<br>*(Rotação de segredos, certificados TLS e credenciais)* | Administrador de PAM (Cofre) | CISO | Analista de Infraestrutura de TI | Diretoria; Compliance; Logs Imutáveis |
| **F08** | **Auditoria de Conflitos SoD e Logs**<br>*(Inspeção periódica de acessos e Maker/Checker)* | Interface de Auditoria Independente *(Controller)* | Conselho de Administração | CISO; Compliance; Gestores de Área | Auditoria Externa; Diretoria-Presidente |

---

## 3. Mapeamento de Cadeiras Corporativas para a DAI

Com base no **Catálogo de Cadeiras** da SUGOI, o acesso aos módulos da DAI é mapeado diretamente para as atribuições da cadeira:

```
                                +--------------------------------------+
                                |        PORTARIA / LOBBY DAI          |
                                +--------------------------------------+
                                                   |
                        +--------------------------+--------------------------+
                        |                                                     |
                        v                                                     v
          [ PERFIL: USUÁRIO SOLICITANTE ]                        [ PERFIL: VALIDADOR / OPERADOR ]
          * Qualquer Cadeira Operacional                         * Cadeira de Controle / Governança
          * Ex: Comprador, Engenheiro Obra                       * Ex: Controller, Advogado, PMO, CISO
          * Triagem de Sintomas e Dúvidas                        * Painel de Quarentena (HTTP 202)
          * Acesso apenas às salas da sua área                   * Treinamento da IA (/triage/learn)
          * Sem acesso a validação de risco                      * Visualização de auditoria e métricas
```

### 3.1 Detalhamento por Cadeira:

| Cadeira Principal | Alçada | Perfil de Negócio | Papel na DAI | Permissões Específicas |
| :--- | :--- | :--- | :--- | :--- |
| **`diretor.presidente@sugoisa.com.br`** | Diretor Presidente | Presidência | Super-Auditor | Acesso total a todas as salas, quarentenas e métricas consolidadas. |
| **`diretor.operacoes@sugoisa.com.br`** | Diretor | Operações | Aprovador Máximo | Aprovação de quarentenas críticas (> R$ 15.000) e liberação Kan-sa. |
| **`controller@sugoisa.com.br`** | Especialista / Gestor | Controladoria | **Validador de Quarentena (Checker)** | Validação de Hashes de CCB, quitação tributária e governança de travas. |
| **`advogado.imobiliario@sugoisa.com.br`** | Especialista | Jurídico | **Validador de Risco Jurídico** | Pareceres de quarentena sobre minutas, escrituras e ônus reais. |
| **`pmo.fpa@sugoisa.com.br`** | PMO | Governança & FP&A | Gestor de Roteamento | Monitoramento do SLA do corredor de salas e fluxo de demandas. |
| **`ciso@sugoisa.com.br`** | Gestor | Segurança da Informação | Guardião PAM / CISO | Gestão de chaves JWT, regras de Firewall, trilha de auditoria e SoD. |
| **`analista.service.desk@sugoisa.com.br`**| Analista | TI / Suporte | Operador de Recepção | Triagem inicial de suporte e encaminhamento operacional. |
| **`comprador@sugoisa.com.br`** | Assistente / Analista | Suprimentos | Usuário Solicitante (Maker) | Abertura de chamados, consulta de procedimentos de contratação. |
| **`engenheiro.obra@sugoisa.com.br`** | Especialista | Engenharia / Obras | Usuário Solicitante (Maker) | Consulta de fichas técnicas e envio de relatórios de medição. |

---

## 4. Regras de Segregação de Funções (SoD) e Princípio Maker/Checker

O modelo de gestão PAM da SUGOI estabelece regras rígidas de **Segregation of Duties (SoD)** para mitigar riscos de fraude e condescendência. Na DAI, essas regras são implementadas via código:

### 4.1 A Regra de Ouro: Maker ≠ Checker na Quarentena
- **O Solicitante (Maker)** que gera o documento, envia a demanda ou insere a queixa **NUNCA** pode aprovar a quarentena correspondente no Painel de Quarentena da DAI.
- Exemplo prático:
  - Se um **Comprador** ou **Engenheiro de Obra** submete uma medição ou minuta de contrato com Hash SHA-256 no sistema, o token JWT dele **não possui** a claim `role: validator`.
  - Apenas o **Controller**, o **Advogado** ou o **Diretor de Operações** (atuando como Checker) pode aprovar a quarentena no endpoint assíncrono `/api/quarentena/validar`.

### 4.2 Matriz de Conflitos SoD Monitorados pela DAI:
1. **Comprador / Engenheiro × Validador de Quarentena**: Bloqueio total. A tentativa de auto-aprovação dispara alerta imediato de *Privilege Escalation* (HTTP 403).
2. **Administrador de PAM (Cofre) × Gestor de Fechamento**: Acesso ao cofre não confere autorização contábil ou financeira.
3. **Operador de Recepção × Gestor de Memória Global**: O analista de recepção pode sugerir novos conhecimentos, mas apenas o Controller ou o CISO pode autorizar que um aprendizado se torne `is_global = true` (visível para todas as SPEs/Clientes).

---

## 5. Arquitetura de Autenticação e Autorização (RBAC & JWT)

Atendendo às recomendações técnicas de segurança, a autenticação da DAI é desenhada em profundidade (*Defense in Depth*):

### 5.1 Estrutura do Token JWT da DAI
Quando o usuário se autentica na Portaria, a API emite um Token JWT assinado contendo as claims da Cadeira:

```json
{
  "sub": "ronaldo.akagui@sugoisa.com.br",
  "nome": "Ronaldo Akagui",
  "cadeira_principal": "diretor.presidente@sugoisa.com.br",
  "alcada": "Diretor",
  "perfil": "Presidência",
  "role": "operator",
  "clientes_acesso": ["controladoria", "juridico", "engenharia"],
  "sod_checks": ["bypass_not_allowed"],
  "iat": 1791168497,
  "exp": 1791197297
}
```

### 5.2 Validação de Middleware RBAC na API FastAPI
Endpoints de alta sensibilidade são protegidos por injeção de dependência e validação de claims:

```python
# Middleware nativo da API Dai (api_backend.py)
def verify_operator_role(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Valida se a Cadeira possui alçada de Operador/Validador (Checker)."""
    token = credentials.credentials
    payload = decodificar_jwt(token)
    if payload.get("role") not in ["operator", "validator", "controller"]:
        raise HTTPException(
            status_code=403, 
            detail="Violação SoD / Privilege Escalation: Esta Cadeira não possui alçada de Validador."
        )
    return True
```

---

## 6. Hardening de Segurança do Servidor e Firewall (Oracle OCI)

A infraestrutura ancorada na Oracle Cloud (IP `137.131.151.74`) adota o modelo de **Zero Trust de Perímetro**:

### 6.1 Regras de Firewall e Portas
```
+-----------------------------------------------------------------------------------+
|                        TOPOLOGIA DE REDE E FIREWALL OCI                           |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  INTERNET EXTERNA (0.0.0.0/0)                                                     |
|        │                                                                          |
|        ▼                                                                          |
|  PORTA 80 (HTTP)  ──[ Redirecionamento 308 Imediato ]──► PORTA 443 (HTTPS Caddy)  |
|  PORTA 443 (HTTPS) ───────────────────────────────────► Caddy Gateway TLS v1.3    |
|        │                                                                          |
|        │ (Reverse Proxy Local Seguro via Docker Bridge)                           |
|        ├──────────────────────┬──────────────────────┐                            |
|        ▼                      ▼                      ▼                            |
|  Porta 8501 (Lobby)    Porta 8001 (API)      Porta 8000 (Kan-sa)                  |
|  127.0.0.1             127.0.0.1             127.0.0.1                            |
|        │                      │                      │                            |
|        └──────────────────────┼──────────────────────┘                            |
|                               ▼                                                   |
|                        Porta 5432 (PgVector)                                      |
|                        127.0.0.1 / Rede Docker Interna                            |
|                        [BLOQUEADA DO EXTERIOR]                                    |
+-----------------------------------------------------------------------------------+
```

1. **OCI VCN Ingress Rules**:
   - `Porta 22 (SSH)`: Apenas com chave RSA/ED25519; autenticação por senha explicitamente desativada em `/etc/ssh/sshd_config`.
   - `Portas 80 e 443`: Abertas para emissão automática de certificados SSL (Let's Encrypt / ZeroSSL).
   - `Portas 5432, 8000, 8001, 8501`: **100% Bloqueadas externamente**. Nenhum cliente pode acessar o banco de dados diretamente sem passar pelo gateway autenticado.

2. **Firewall Local do Ubuntu (`iptables`)**:
   Regras de persistência ativas para garantir que o tráfego não autorizado seja descartado:
   ```bash
   sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
   sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
   sudo netfilter-persistent save
   ```

3. **Proteção de Memória e Resiliência contra OOM**:
   - Memória RAM Física: `954 MiB` (~1 GB).
   - Swapfile Ativo: `6.0 GiB` montado em SSD de alta performance.
   - Consumo da DAI: `~114 MiB` total (~12% da máquina), deixando mais de `400 MiB` de RAM livre para oscilações e concorrência.
