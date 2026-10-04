# 🎨 Documentação de Identidade Visual e Estilo (Lobby)

Esta documentação registra a primeira fase da injeção de estilo na interface da Dai, utilizando as premissas da marca **Daisugi Brand Suite**.

## Premissas Visuais Aplicadas

A interface passou a incorporar CSS injetado de forma nativa no `app_chat_st.py`, transformando a aplicação em um ambiente Premium e imersivo com os guias de marca Daisugi.

### 1. Fundo e Padrões (Background)
A interface adota um **Dark Mode** sofisticado com os seguintes aspectos:
*   **Cor de Fundo Base:** `#0B192C` (Daisugi Navy).
*   **Textura de Fundo:** Um padrão de grade sutil (`grid-pattern`), com linhas translúcidas desenhadas por gradientes CSS, trazendo um aspecto técnico, de controle e painel de comando.

### 2. Tipografia
*   **Família de Fontes:** Importação do Google Fonts utilizando **'Plus Jakarta Sans'**. Esta tipografia entrega clareza cirúrgica para aplicações corporativas, substituindo a fonte padrão do sistema.

### 3. Glassmorphism e Transparência
As áreas fixas, como o Painel de Login e a Barra Lateral (Sidebar), receberam um efeito "Vidro Fosco":
*   Fundo escuro semitransparente `rgba(15, 23, 42, 0.7)`.
*   Desfoque do fundo (`backdrop-filter: blur(12px)`).
*   Bordas suaves arredondadas e delineamento sutil de borda clara, dando uma impressão de que os painéis flutuam sobre a grade de fundo.

### 4. Elementos Interativos (Botões e Inputs)
*   **Call To Action (CTA):** Todos os botões primários adotam a cor da marca Emerald (`#10b981`), com um brilho de sombra inferior e efeito sutil de flutuação (`transform: translateY(-2px)`) no `:hover`.
*   **Caixas de Texto:** Fundos sólidos em ardósia escura (`#1e293b`), mas que ao receberem foco alteram suas bordas para Emerald, guiando visualmente a atenção do usuário no preenchimento do formulário/chat.

### 5. Alertas Semânticos Customizados
Os blocos de feedback visual (Avisos, Informações, Erros, Sucessos) nativos do Streamlit foram inteiramente reestilizados. Eles perdem o fundo padrão e passam a adotar caixas sutis com transparência e apenas a borda lateral esquerda destacando a cor da severidade.
*   **Sucesso:** Emerald Soft / Verde.
*   **Aviso:** Amber Soft / Amarelo.
*   **Informativo:** Sky Soft / Azul Claro.

### 6. Ocultação do Cromo do Streamlit
Para uma experiência **White-Label**, o CSS desativa a renderização do cabeçalho (`header`), do rodapé (`footer`) e dos menus em hambúrguer (`#MainMenu`) nativos da framework. O usuário tem a percepção de estar rodando uma Single Page Application própria.

---
*Este arquivo será mantido como histórico das decisões visuais baseadas nas especificações de marca.*
