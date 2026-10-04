# 📱 Interface, Acesso e UX (Lobby Central)

Este documento detalha o funcionamento da interface visual (Front-End) da Dai, as regras de acesso e como a experiência do usuário (UX) foi projetada para atuar como o **Standard de Home Page** de forma agnóstica e responsiva.

---

## 1. 🏗️ Estrutura Agnóstica: Do Específico ao Universal
Inicialmente concebida para o cenário da "Clínica Neural" (com "Pacientes", "Prontuários" e "Corredores"), a interface foi 100% refatorada para uma linguagem universal, aplicável a qualquer corporação (B2B, B2C, RH, TI). 

*   **Portaria:** O ponto de autenticação e identificação inicial do usuário.
*   **Lobby Central:** Substitui a "Recepção da Clínica". É o local onde o usuário interage livremente com a Dai.
*   **Salas:** Substituem os "Corredores Médicos". Representam as áreas especializadas (ex: Jurídico, Financeiro, TI).
*   **Contexto do Usuário (Ticket):** Substitui o "Prontuário". É onde o histórico de interações e métricas ficam registrados.
*   **Laudo de Roteamento:** A decisão final e o "carimbo" para qual sala o usuário foi direcionado.

Essa linguagem universal é parametrizada no arquivo `config_cliente.json`, permitindo adaptar a aplicação para advocacia, concessionárias, SaaS, etc.

---

## 2. 📱 UX "Mobile First" (Responsividade)
O design foi projetado pensando em telas pequenas (Smartphones), que representam a maior fatia de interações:
*   **Empilhamento Inteligente:** Em telas Desktop, a tela é dividida horizontalmente (`layout="wide"`), com a Dai à esquerda e as Salas à direita. Em ambientes Mobile, a interface empilha automaticamente: o **Lobby da Dai (Chat)** aparece primeiro (ação principal), seguido das Salas e do Contexto.
*   **Foco na Conversa:** A barra de digitação sempre permanece visível e acessível para facilitar o envio da queixa ou solicitação.
*   **Clean Design:** Uso de botões grandes, painéis expansíveis e alertas em cores sólidas (Sucesso/Aviso/Erro) para legibilidade rápida ao sol ou em movimento.

---

## 3. 🔐 Portaria e Análise de Perfil de Acesso
A triagem não depende apenas do que o usuário *fala*, mas de *quem* ele é.
1.  **Autenticação:** O usuário passa pela "Portaria" (Login).
2.  **Injeção de Perfil:** O sistema captura o Nível de Acesso (ex: Admin, Cliente B2B, Dev).
3.  **Renderização Dinâmica de Salas:** A visão da tela da direita muda completamente. Um "Cliente B2B" enxerga apenas as salas de "Consultoria" ou "Contratos". Um "Desenvolvedor" enxerga as salas de "DevOps" e "QA". A Dai nunca vai rotear um usuário para uma sala que ele não tem credencial para ver.

---

## 4. 🔀 A Experiência de Triagem (RAG & Lógica Fuzzy)
A UX por trás do balcão segue o princípio da **Fricção Mínima**:

### Cenário A (Caminho Feliz - Alta Certeza)
1. O usuário diz: *"Quero ver os relatórios de balanço do mês."*
2. A Dai cria um vetor silencioso e busca no `pgvector` (RAG Vetorial).
3. Distância Vetorial = `0.1` (Excelente).
4. **UX:** O sistema responde imediatamente: *"Encaminhando para a Sala Financeira"* e libera o acesso ao especialista. Nenhuma dor de cabeça para o usuário.

### Cenário B (Lógica Fuzzy - Dúvida e Refinamento)
1. O usuário diz: *"Preciso de ajuda com um problema urgente."* (Muito vago).
2. A busca no RAG retorna Distância Vetorial = `0.6` (Incerteza/Ambiguidade).
3. **UX (Gatilho Fuzzy):** A Dai não "chuta" e nem joga a responsabilidade para a sala errada. Ela responde na interface com 3 perguntas de triagem rápidas:
   * **O QUE** você precisa resolver?
   * **COMO** espera que a equipe ajude?
   * **POR QUE** isso é uma prioridade agora?
4. Assim que o usuário responde, a certeza matemática aumenta e o roteamento é feito.

---
## 🎨 5. Personalização Visual
A cor Primária e Secundária, o Avatar e o Emoji podem ser alterados em tempo real alterando o arquivo `config_cliente.json`. Recomendamos o uso de paletas suaves (ex: Azuis para passar confiança, Verdes para estabilidade) para garantir conforto visual no Lobby.
