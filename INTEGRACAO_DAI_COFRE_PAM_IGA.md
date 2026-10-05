# 🤝 Integração DAI × Daisugi Ecosystem Cofre-PAM-IGA
**Documento Oficial de Integração, Protocolo de Portaria e Validação de Cadeiras**  
*Módulo de Segurança e Governança da DAI Smart Reception*

---

## 1. Visão Geral da Integração

A **DAI (Daisugi Smart Reception)** não atua como autoridade primária de credenciais. Toda autenticação, governança de cadeiras, alçadas e segregação de funções (SoD) é delegada ao serviço central **`Daisugi_Ecosystem_Cofre-PAM-IGA`**.

```
[ Usuário / Colaborador ]
           │
           ▼
[ Portaria / Lobby da DAI ] ──(1. Handshake Pré-Lobby)──► [ COFRE-PAM-IGA CENTRAL ]
                                                          • Valida Cadeira no Catálogo
                                                          • Confere SoD (Maker/Checker)
                                                          • Autoridade Soberana da Daisugi
                                                                     │
[ DAI: Sessão Aberta ] ◄──────(2. Token JWT Assinado)───────────────┘
• Validação Criptográfica Local O(1) (< 1ms)
• Renderização seletiva das Salas autorizadas
• Trava Core Dev inegociável
```

---

## 2. Fluxo de Handshake Pré-Lobby

Quando o usuário insere seu login no Streamlit ou Web App da DAI:
1. A DAI despacha a requisição para o endpoint central do Cofre:
   `POST https://auth.daisugi.com.br/api/v1/auth/handshake`
2. O Cofre valida a identidade, a alçada corporativa e emite o token assinado contendo:
   - `sub`: Identidade nominal (`ronaldo.akagui@sugoisa.com.br`)
   - `cadeira_principal`: Cadeira funcional (`controller@sugoisa.com.br`)
   - `role`: Papel de negócio (`checker`, `maker` ou `core_developer`)
   - `salas_liberadas`: Lista de salas permitidas
   - `is_core_developer`: Booleano estritamente reservado aos e-mails soberanos da Akagui.

---

## 3. Blindagem de Desenvolvedor (Core Dev Lock) na DAI

* Os usuários clientes (como a SUGOI) operam nas alçadas de negócio (`checker`, `maker`).
* Qualquer rota de manutenção interna, reparametrização de sinapses globais ou auditoria de sistema exige a claim `"is_core_developer": true`.
* Apenas as contas `montanhavermelha@akagui.com` e `ronaldoakagui@gmail.com` são aceitas como desenvolvedores da plataforma.

---

## 4. Validação Maker/Checker na Quarentena de Risco

Ao aprovar uma quarentena na DAI (endpoint `/api/quarentena/validar`):
* A DAI invoca a regra SoD: se o usuário que está aprovando for o mesmo que gerou o documento ou a medição (Maker), o sistema retorna `HTTP 403 Forbidden` com alerta de violação SoD.
* Apenas cadeiras de controle (`controller`, `advogado`, `diretor`) atuando como **Checker** têm permissão de aprovação.
