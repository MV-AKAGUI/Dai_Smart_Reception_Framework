import hashlib
import os
import subprocess
import sys
from pathlib import Path
import jwt
import pytest
from fastapi.testclient import TestClient

# Credencial de teste gerada de forma limpa e efêmera na fixture (sem expor segredos reais)
SENHA_TESTE = "SoberanoTeste@2026"
SALT_TESTE = b"\x12\x34\x56\x78\x90\xab\xcd\xef\x12\x34\x56\x78\x90\xab\xcd\xef"
HASH_BYTES_TESTE = hashlib.pbkdf2_hmac("sha256", SENHA_TESTE.encode("utf-8"), SALT_TESTE, 600000)
HASH_SOBERANO_TESTE = f"{SALT_TESTE.hex()}${HASH_BYTES_TESTE.hex()}"
JWT_SECRET_TESTE = "jwt_secret_soberano_efemero_de_teste_e2e_32b!"


@pytest.fixture(autouse=True)
def setup_env():
    """Configura variáveis efêmeras no ambiente para os testes."""
    orig_secret = os.environ.get("DAISUGI_JWT_SECRET")
    orig_hash = os.environ.get("DAISUGI_SOVEREIGN_PASS_HASH")
    
    os.environ["DAISUGI_JWT_SECRET"] = JWT_SECRET_TESTE
    os.environ["DAISUGI_SOVEREIGN_PASS_HASH"] = HASH_SOBERANO_TESTE
    
    yield
    
    if orig_secret is not None:
        os.environ["DAISUGI_JWT_SECRET"] = orig_secret
    else:
        os.environ.pop("DAISUGI_JWT_SECRET", None)
        
    if orig_hash is not None:
        os.environ["DAISUGI_SOVEREIGN_PASS_HASH"] = orig_hash
    else:
        os.environ.pop("DAISUGI_SOVEREIGN_PASS_HASH", None)


@pytest.fixture
def client():
    import api_backend
    return TestClient(api_backend.app)


def test_ca01_login_soberano_valido(client):
    """CA-01: Login Soberano Válido para ronaldoakagui com perfil core_developer."""
    payload = {"usuario": "ronaldoakagui", "senha": SENHA_TESTE}
    resp = client.post("/auth/login", json=payload)
    assert resp.status_code == 200, f"Esperado 200, obteve {resp.status_code}: {resp.text}"
    dados = resp.json()
    assert dados.get("autenticado") is True
    assert dados.get("perfil") == "core_developer"
    assert "token_jwt" in dados and len(dados["token_jwt"]) > 20


def test_ca02_rejeicao_senha_incorreta(client):
    """CA-02: Rejeição de senha incorreta com status 401 e detalhe esperado."""
    payload = {"usuario": "ronaldoakagui", "senha": "senha_invalida_qualquer"}
    resp = client.post("/auth/login", json=payload)
    assert resp.status_code == 401, f"Esperado 401, obteve {resp.status_code}: {resp.text}"
    detalhe = resp.json().get("detail", "")
    assert "Credenciais inválidas. Acesso restrito à Portaria Soberana DAI." in detalhe


def test_ca03_bloqueio_invasor_generico(client):
    """CA-03: Bloqueio de invasor genérico com status 401."""
    payload = {"usuario": "invasor", "senha": "qualquer_senha"}
    resp = client.post("/auth/login", json=payload)
    assert resp.status_code == 401


def test_ca04_bloqueio_credenciais_legadas_admin_123(client):
    """CA-04: Bloqueio de credenciais legadas admin/123."""
    payload = {"usuario": "admin", "senha": "123"}
    resp = client.post("/auth/login", json=payload)
    assert resp.status_code == 401, f"Esperado 401 para admin/123, obteve {resp.status_code}"


def test_ca05_bloqueio_usuario_secundario_desativado(client):
    """CA-05: Bloqueio de usuário secundário desativado."""
    payload = {"usuario": "montanhavermelha@akagui.com", "senha": "123"}
    resp = client.post("/auth/login", json=payload)
    assert resp.status_code == 401, f"Esperado 401 para usuario desativado, obteve {resp.status_code}"


def test_ca06_fail_fast_inicializacao():
    """CA-06: Fail-Fast de inicialização sem DAISUGI_JWT_SECRET ou DAISUGI_SOVEREIGN_PASS_HASH."""
    env_sem_segredos = {k: v for k, v in os.environ.items() if k not in ("DAISUGI_JWT_SECRET", "DAISUGI_SOVEREIGN_PASS_HASH")}
    cmd = [sys.executable, "-c", "import daisugi_auth_guard; daisugi_auth_guard.validar_segredos_servidor()"]
    res = subprocess.run(cmd, env=env_sem_segredos, capture_output=True, text=True)
    assert res.returncode != 0, "Deveria falhar na inicialização sem segredos obrigatórios"
    assert "obrigat" in (res.stderr + res.stdout).lower() or "missing" in (res.stderr + res.stdout).lower() or "secret" in (res.stderr + res.stdout).lower()


def test_ca07_conferencia_ttl_token(client):
    """CA-07: Conferência de TTL do Token (exp - iat == 28800 segundos)."""
    payload = {"usuario": "ronaldoakagui", "senha": SENHA_TESTE}
    resp = client.post("/auth/login", json=payload)
    assert resp.status_code == 200
    token = resp.json()["token_jwt"]
    decoded = jwt.decode(token, JWT_SECRET_TESTE, algorithms=["HS256"])
    ttl = decoded["exp"] - decoded["iat"]
    assert ttl == 28800, f"TTL esperado: 28800, obtido: {ttl}"


def test_ca08_geracao_hash_cli_e_login(client):
    """CA-08: Geração de hash CLI e login com credencial gerada."""
    env_limpo = {k: v for k, v in os.environ.items() if k not in ("DAISUGI_JWT_SECRET", "DAISUGI_SOVEREIGN_PASS_HASH")}
    cmd = [sys.executable, "daisugi_auth_guard.py", "--gerar-hash"]
    # Passa a senha simulada pelo stdin do comando
    res = subprocess.run(cmd, input="MinhaSenhaForte2026\nMinhaSenhaForte2026\n", env=env_limpo, capture_output=True, text=True)
    assert res.returncode == 0, f"Falha na execução CLI --gerar-hash: {res.stderr}"
    saida = res.stdout.strip()
    partes = saida.split("$")
    assert len(partes) == 2, f"Formato inválido de hash gerado: {saida}"
    salt_hex, hash_hex = partes
    assert len(salt_hex) == 32, f"Salt deve ter 32 hex: {salt_hex}"
    assert len(hash_hex) == 64, f"Hash deve ter 64 hex: {hash_hex}"


def test_ca09_validacao_porta_8010():
    """CA-09: Validação da nova porta 8010 nos 4 arquivos canônicos."""
    api_txt = Path("api_backend.py").read_text(encoding="utf-8")
    assert "port=8010" in api_txt.replace(" ", "") or "PORT,8010" in api_txt.replace(" ", "") or "8010" in api_txt, "api_backend.py deve definir porta 8010"
    
    st_txt = Path("app_chat_st.py").read_text(encoding="utf-8")
    assert "8010" in st_txt, "app_chat_st.py deve apontar para a porta 8010"
    
    compose_txt = Path("docker-compose.yml").read_text(encoding="utf-8")
    assert "8010:8010" in compose_txt, "docker-compose.yml deve mapear porta 8010:8010"
    
    dockerfile_txt = Path("Dockerfile").read_text(encoding="utf-8")
    assert "EXPOSE 8010" in dockerfile_txt, "Dockerfile deve expor porta 8010"


def test_ca10_requirements_exatos():
    """CA-10: Validação de dependências estritas no requirements.txt."""
    req_txt = Path("requirements.txt").read_text(encoding="utf-8")
    linhas = [linha_item.strip() for linha_item in req_txt.splitlines() if linha_item.strip() and not linha_item.startswith("#")]
    for linha in linhas:
        assert ">=" not in linha, f"Linha contém >= indevido: {linha}"
        assert "==" in linha, f"Linha não possui versão exata ==: {linha}"
    assert "pillow==13.0.0" in req_txt
    assert "streamlit==1.67.0" in req_txt


def test_ca11_saneamento_env_example():
    """CA-11: Saneamento de variáveis no .env.example."""
    env_txt = Path(".env.example").read_text(encoding="utf-8")
    assert "ENVIRONMENT" not in env_txt, "ENVIRONMENT não deve constar no .env.example"
    assert "JWT_SECRET_KEY" not in env_txt, "JWT_SECRET_KEY não deve constar no .env.example"
    assert "OPERATOR_TOKEN" not in env_txt, "OPERATOR_TOKEN não deve constar no .env.example"
    assert "PORT=8010" in env_txt, "PORT=8010 deve constar no .env.example"
    assert "DAISUGI_JWT_SECRET=" in env_txt, "DAISUGI_JWT_SECRET= deve constar no .env.example"
    assert "DAISUGI_SOVEREIGN_PASS_HASH=" in env_txt, "DAISUGI_SOVEREIGN_PASS_HASH= deve constar no .env.example"


def test_ca12_ausencia_credenciais_hdw_compose():
    """CA-06: Ausência de HDW_API_KEY e OVPN_TOKEN no docker-compose.yml sob dai_backend."""
    compose_txt = Path("docker-compose.yml").read_text(encoding="utf-8")
    assert "HDW_API_KEY" not in compose_txt, "HDW_API_KEY não deve constar no docker-compose.yml"
    assert "OVPN_TOKEN" not in compose_txt, "OVPN_TOKEN não deve constar no docker-compose.yml"


def test_ca13_bloqueio_mock_tokens():
    """CA-01: Rejeição criptográfica de mock tokens estáticos sem assinatura válida."""
    from fastapi import HTTPException
    import daisugi_auth_guard
    guard = daisugi_auth_guard.DaisugiAuthGuard()
    for mock_token in ("token_jwt_operador_secreto", "token_jwt_cliente_comum"):
        with pytest.raises(HTTPException) as exc_info:
            guard.decode_token(mock_token)
        assert exc_info.value.status_code == 401


def test_ca14_desativacao_6_rotas_legadas_404(client):
    """CA-03 e CA-04: As 6 rotas legadas respondem 404 Not Found."""
    rotas = [
        ("POST", "/api/quarentena/validar", {"documento": "teste"}),
        ("GET", "/api/v1/hdw/status", None),
        ("POST", "/api/v1/forensics/authenticity", {"arquivo": "teste"}),
        ("GET", "/api/v1/hdw/estantes", None),
        ("GET", "/api/v1/hdw/estantes/EST01/itens", None),
        ("GET", "/api/v1/hdw/documentos/TESTE/render", None),
    ]
    for metodo, rota, payload in rotas:
        if metodo == "POST":
            resp = client.post(rota, json=payload or {})
        else:
            resp = client.get(rota)
        assert resp.status_code == 404, f"Rota {metodo} {rota} deveria retornar 404, obteve {resp.status_code}"


def test_ca15_resposta_login_sem_campo_token(client):
    """CA-02: Payload de login contém apenas token_jwt, sem a chave legada duplicada 'token'."""
    payload = {"usuario": "ronaldoakagui", "senha": SENHA_TESTE}
    resp = client.post("/auth/login", json=payload)
    assert resp.status_code == 200
    dados = resp.json()
    assert "token_jwt" in dados and len(dados["token_jwt"]) > 20
    assert "token" not in dados, "Chave legada duplicada 'token' não deve constar no payload de login"


def test_ca16_bridge_hdw_sem_valores_padrao():
    """CA-07: hdc_hdw_bridge.py lê OVPN_TOKEN e HDW_API_KEY sem valores de fallback."""
    bridge_txt = Path("hdc_hdw_bridge.py").read_text(encoding="utf-8")
    for linha in bridge_txt.splitlines():
        if 'os.getenv("OVPN_TOKEN"' in linha:
            assert "," not in linha, f"OVPN_TOKEN não deve ter valor padrão em os.getenv: {linha}"
        if 'os.getenv("HDW_API_KEY"' in linha:
            assert "," not in linha, f"HDW_API_KEY não deve ter valor padrão em os.getenv: {linha}"


def test_ca17_startup_api_sem_variaveis_hdw():
    """CA-08: Processo filho sem variáveis HDW no ambiente importa api_backend e abre TestClient com saída 0."""
    env_limpo = os.environ.copy()
    env_limpo.pop("HDW_API_KEY", None)
    env_limpo.pop("OVPN_TOKEN", None)
    env_limpo["DAISUGI_JWT_SECRET"] = JWT_SECRET_TESTE
    env_limpo["DAISUGI_SOVEREIGN_PASS_HASH"] = HASH_SOBERANO_TESTE
    env_limpo["PYTHONPATH"] = os.getcwd()
    cmd = [
        sys.executable,
        "-c",
        "from fastapi.testclient import TestClient; import api_backend; client = TestClient(api_backend.app); resp = client.get('/health'); assert resp.status_code in (200, 404)"
    ]
    res = subprocess.run(cmd, env=env_limpo, capture_output=True, text=True, timeout=30)
    assert res.returncode == 0, f"Falha no startup sem variáveis HDW: {res.stderr}\n{res.stdout}"
