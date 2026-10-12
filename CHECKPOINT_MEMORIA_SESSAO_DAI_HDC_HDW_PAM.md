# 📌 CHECKPOINT & MEMÓRIA DE SESSÃO: ARQUITETURA DAI, HDC, HDW E PAM DAISUGI
**Data de Registro:** 11 de Outubro de 2026  
**Status do Projeto:** Homologado na Oracle OCI e alinhado para evolução do Front-End  
**Responsável:** Dr. Taylor Code (Maestro da Homeostase) & PMO de Processos, Programação e TI  

---

## 1. Estado da Infraestrutura em Nuvem (Oracle OCI - 137.131.151.74)
- **Repositório Git (`origin/main`):** Atualizado no commit `0f4f96b`.
- **Containers Docker Ativos:**
  - `dai_frontend_lobby` (Porta 8501) — HTTP 200 OK.
  - `dai_backend_api` (Porta 8001) — HTTP 200 HEALTHY.
  - `dai_postgres_vector` (Porta 5432) — Up & Healthy.
- **Túnel OpenVPN na OCI:**
  - Serviço `openvpn-client@dai-hdw.service` ativo no host Ubuntu.
  - Interface `tun0` operante com IP `10.8.0.5/24`.
  - Conexão validada via `curl http://10.8.0.1:8000/health` $\rightarrow$ `{"status":"ok"}` com **64.75ms de latência**.
  - Roteamento blindado contra sequestro de default gateway (`pull-filter ignore "redirect-gateway"`).
- **Ponto Pendente com a TI da SUGOI (HDW Linux 192.168.1.122 / 10.8.0.1):**
  - Chave de API `38925b32ce108ddf4cda7d54cabc3cb9acc56e3c8b58fbd3ea8cf6327921e862` retornou `401 Chave de API invalida ou ausente`.
  - TI precisa recarregar o FastAPI no Linux ou confirmar a chave após finalizar a subida da carga física dos arquivos no acervo.

---

## 2. Diretrizes Arquiteturais Homologadas para o Front-End da DAI
1. **Web First & Mobile First:** Interface limpa, responsiva, amigável e fluida (Omotenashi com rigor militar).
2. **Remoção Absoluta de Seletores de LLM da Tela:**
   - O usuário **NUNCA** escolhe modelo de IA na tela (`Meta Llama`, `Qwen`, `DeepSeek`). Quem atende é a **DAI**.
   - As LLMs são órgãos internos no back-end, roteadas por especialidade de forma invisível via **RapidFuzz** e **HDC Harness**.
   - **Roteamento Interno:**
     - Exatas / Finanças / Código $\rightarrow$ Qwen 2.5 Coder.
     - Raciocínio Formal / WBS / Hashes $\rightarrow$ DeepSeek-R1.
     - Acolhimento / Geral / Linguagem $\rightarrow$ Llama 3.1 / SaulLM / Mistral-Nemo.

---

## 3. Matriz Oficial de Mapeamento: 9 Cadeiras Nominais PAM SUGOI
Governança transitória por mapeamento determinístico enquanto o PAM central da SUGOI não é automatizado:

| # | Nome Nominal | RG / Identificador | Cadeira Funcional PAM | Perfil RBAC | Alçada SoD | Salas Liberadas no Lobby | Estantes HDW |
| :-: | :--- | :---: | :--- | :---: | :---: | :--- | :--- |
| 1 | **Cintia** | `43012174X` | `pmo.gg@sugoisa.com.br` | `pmo_gg` | Gestor Governança | Kigyou, Cultura, Organograma PAM | `EST-04` (Atas) |
| 2 | **Wesley** | `477592211` | `especialista.ti@sugoisa.com.br` | `admin_tecnico` | Custodiante TI | Painel Técnico, Auditoria Hashes, IAs | `EST-01` a `EST-06` (Leitura técnica) |
| 3 | **Fernando Brasil** | `34440020` | `controller@sugoisa.com.br` | `controller_geral` | **Checker Pleno** | Quarentena Checker, Travas ERP, Kan-sa M4 | `EST-03`, `EST-06` |
| 4 | **Gustavo** | `460430464` | `monitor.operacoes@sugoisa.com.br` | `monitor_operacoes` | Maker Operacional | Cockpit Indicadores, Metas Obras | `EST-01`, `EST-05` |
| 5 | **Renato Barroso** | `44459051` | `diretor.operacoes@sugoisa.com.br` | `diretor_operacoes` | Aprovador Superior | Cockpit Operações, Homologação Praças | `EST-01`, `EST-02`, `EST-05`, `EST-06` |
| 6 | **Fabiana** | `306148651` | `pmo.operacoes.crm@sugoisa.com.br` | `pmo_operacoes_crm` | Gestor Processos | CRM, Vistorias, SLA Entregas Chaves | `EST-01`, `EST-02`, `EST-04` |
| 7 | **Flavia** | `426208195` | `pmo.financeiro@sugoisa.com.br` | `pmo_financeiro` | **Checker N1** | Auditoria M4/M9, Fluxo de Caixa, Quarentena | `EST-03`, `EST-06` |
| 8 | **Paola** | `439372616` | `advogado.imobiliario@sugoisa.com.br` | `especialista_juridico`| **Checker Jurídico**| Consultório Jurídico, Riscos, Matrículas | `EST-02`, `EST-06` |
| 9 | **Denise** | `425504657` | `especialista.financeiro@sugoisa.com.br` | `especialista_financeiro`| **Maker Financeiro** | Contas a Pagar, Conciliação, Input Faturas | `EST-03` |

---

## 5. Atualização Homologada: Front-End Split-Screen & LLM Open-Source Cloud
- **Split-Screen Claude-Style:** Implementado no `app_chat_st.py` com navegação pericial à esquerda e chat ativo à direita.
- **Detecção de Exercício / Ano:** Reconhecimento contextual de pedidos de laudos e relatórios de endividamento (ex: 2024, 2023, 2022, 2021) abrindo o respectivo exercício no Kan-sa.
- **HDC Harness Humanizado & LLM Open-Source:**
  - Remoção de mensagens mecânicas com colchetes e referências técnicas frias.
  - Conector nativo para provedor Open-Source em Nuvem de latência ultrabaixa (Groq/Llama 3.1 8B) sem custos de tokens.
  - Preservação estrita das travas de Closed-World Assumption e alçadas PAM-IGA no servidor.
- **Deploy em Produção (Oracle OCI - 137.131.151.74):**
  - Código injetado e ativo nos contêineres `dai_frontend_lobby` e `dai_backend_api`.
  - Verificação com HTTP 200 OK em [https://dai.daisugi.com.br](https://dai.daisugi.com.br).

---

## 6. Governança Vibe Coding DAISUGI
- Todo artefato e alteração no ecossistema segue a regra estrita de auto-sincronização com o repositório remoto Git.
- Nenhuma alteração é deixada isolada em ambiente local.
- Registro contínuo de decisões arquiteturais na memória soberana do projeto.

---

## 5. Próximos Passos Imediatos ao Retomar a Sessão
1. **No Front-End (`app_chat_st.py`):**
   - Retirar o toggle e `selectbox` de LLM do chat.
   - Atualizar a tela de login para disponibilizar os botões de atalho das 9 cadeiras nominais com nomes e RGs.
2. **No Back-End (`api_backend.py`):**
   - Cadastrar formalmente os 9 usuários no `/auth/login` emitindo JWT com claims completas.
   - Integrar o Roteador Cognitivo Soberano interno para as LLMs no endpoint de streaming SSE.
3. **Deploy Final na OCI:**
   - Rodar `git pull` e restart dos containers na Oracle Cloud para entrega da interface definitiva ao cliente.
