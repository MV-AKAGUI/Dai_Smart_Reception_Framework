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

## 📚 Central de Documentação Técnica

| Documento | Foco | Público |
|---|---|---|
| [**Protocolo de Segurança Anti-Alucinação**](./Protocolo_Seguranca_Anti_Alucinacao.md) | As 5 camadas de contenção, premissa de mundo fechado, temperatura 0.0 e validação determinística. | Engenharia, Segurança e IA |
| [**Documentação Técnica do Back-End**](./Documentacao_Tecnica_Dai_Backend.md) | FastAPI, pgvector, cache O(1), RBAC, endpoints REST e contratos Pydantic. | Arquitetura e Back-End |
| [**Documentação de Integração Front & Back**](./Documentacao_Integracao_Front_Back.md) | Protocolos de comunicação, diagrama de sequência, estados e timeouts. | Engenharia Full-Stack |
| [**Infraestrutura e Deploy Oracle OCI**](./INFRAESTRUTURA_ORACLE_OCI_DEPLOY.md) | Topologia de nuvem, Docker, Caddyfile, dimensionamento Ampere A1 e integrações Kan-sa / Hudson. | DevOps e Cloud |

---
*Construído com ❤️ e Lógica pela Daisugi Tecnologias.*

