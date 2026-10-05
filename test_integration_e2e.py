import sys
import os

# Suporte a UTF-8 no console Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from fastapi.testclient import TestClient
from api_backend import app, REDIS_CACHE_MOCK

client = TestClient(app)

def test_01_healthcheck():
    """Valida se o probe de saúde responde 200 OK para o Caddy e OCI."""
    response = client.get("/health")
    assert response.status_code == 200, f"Healthcheck falhou: {response.text}"
    dados = response.json()
    assert dados["status"] == "HEALTHY"
    print("✅ [TESTE 1/5 PASSOU] Healthcheck probe operacional.")

def test_02_autenticacao_login():
    """Valida o handshake de login e injeção do Bearer Token JWT."""
    # 1. Login com credenciais válidas (Admin / Operador)
    res_admin = client.post("/auth/login", json={"usuario": "admin", "senha": "123"})
    assert res_admin.status_code == 200
    dados_admin = res_admin.json()
    assert dados_admin["autenticado"] is True
    assert dados_admin["token_jwt"] == "token_jwt_operador_secreto"
    assert any(s["nome"] == "Painel Quarentena" for s in dados_admin["salas_liberadas"])

    # 2. Login com cliente comum
    res_cli = client.post("/auth/login", json={"usuario": "cliente", "senha": "123"})
    assert res_cli.status_code == 200
    assert res_cli.json()["perfil"] == "cliente"

    # 3. Bloqueio de credenciais inválidas
    res_fake = client.post("/auth/login", json={"usuario": "invasor", "senha": "errada"})
    assert res_fake.status_code == 401
    print("✅ [TESTE 2/5 PASSOU] Autenticação e separação de perfis validadas.")

def test_03_quarentena_rbac_blindagem():
    """Valida a barreira contra Privilege Escalation na rota de Quarentena."""
    payload = {"hash_id_documento": "hash_teste_ccb_123", "aprovado": True}

    # 1. Tentativa sem token -> 401 Unauthorized (Padrão RFC 7235)
    res_sem_token = client.post("/api/quarentena/validar", json=payload)
    assert res_sem_token.status_code in [401, 403], f"Esperava 401 ou 403, obteve {res_sem_token.status_code}"

    # 2. Tentativa com token de cliente comum (Privilege Escalation Detectado -> 403 Forbidden)
    headers_cli = {"Authorization": "Bearer token_jwt_cliente_comum"}
    res_escalation = client.post("/api/quarentena/validar", headers=headers_cli, json=payload)
    assert res_escalation.status_code == 403
    assert "Privilege Escalation Detectado" in res_escalation.json()["detail"]

    # 3. Operador autorizado -> HTTP 202 Accepted (Desacoplamento Assíncrono)
    headers_op = {"Authorization": "Bearer token_jwt_operador_secreto"}
    res_op = client.post("/api/quarentena/validar", headers=headers_op, json=payload)
    assert res_op.status_code == 202
    assert res_op.json()["status_http"] == 202
    assert res_op.json()["hash_processado"] == "hash_teste_ccb_123"
    print("✅ [TESTE 3/5 PASSOU] Blindagem RBAC e HTTP 202 Accepted aprovados.")

def test_04_cache_redis_o1():
    """Valida se uma consulta em cache não bate no banco vetorial nem alucina."""
    queixa_teste = "Minha conta de acesso está bloqueada"
    import hashlib
    hash_queixa = hashlib.md5(queixa_teste.strip().encode()).hexdigest()

    # Injeta a resposta prévia no cache O(1)
    REDIS_CACHE_MOCK[hash_queixa] = {
        "destino": "Sala Suporte Contas",
        "cliente_destino": "controladoria"
    }

    # Dispara a triagem
    res = client.post("/chat/triage", json={"id_usuario": 1, "texto_usuario": queixa_teste})
    assert res.status_code == 200
    dados = res.json()
    assert dados["cache_hit"] is True
    assert dados["destino"] == "Sala Suporte Contas"
    assert "⚡ (Via Cache)" in dados["resposta_dai"]
    print("✅ [TESTE 4/5 PASSOU] Proteção de Cache Redis O(1) validada.")

def test_05_trava_fuzzy_anti_alucinacao():
    """Valida se queixas sem dados cadastrados no banco acionam o modo Fuzzy de 3 perguntas."""
    # Uma queixa sem similaridade no banco (sem conexao com Postgres ou mock vazio)
    queixa_ambigua = "Quero falar sobre um assunto qualquer"
    res = client.post("/chat/triage", json={"id_usuario": 999, "texto_usuario": queixa_ambigua})
    assert res.status_code == 200
    dados = res.json()
    # Deve acionar o modo Fuzzy e pedir refinamento
    assert dados["status_fuzzy"] is True
    print("✅ [TESTE 5/5 PASSOU] Trava Anti-Alucinação Fuzzy aprovada.")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🔬 INICIANDO TESTES DE INTEGRAÇÃO E2E (AUDITORIA DR. TAYLOR)")
    print("="*60)
    test_01_healthcheck()
    test_02_autenticacao_login()
    test_03_quarentena_rbac_blindagem()
    test_04_cache_redis_o1()
    test_05_trava_fuzzy_anti_alucinacao()
    print("="*60)
    print("🏆 TODOS OS TESTES PASSARAM COM 100% DE SUCESSO!")
    print("="*60 + "\n")
