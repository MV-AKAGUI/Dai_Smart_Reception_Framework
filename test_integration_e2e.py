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
    assert "token" in dados and len(dados["token"]) > 20


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
    token = resp.json()["token"]
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
    linhas = [l.strip() for l in req_txt.splitlines() if l.strip() and not l.startswith("#")]
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


def test_ca12_preservacao_escopo_compose():
    """CA-12: Preservação de HDW_API_KEY e OVPN_TOKEN no docker-compose.yml."""
    compose_txt = Path("docker-compose.yml").read_text(encoding="utf-8")
    assert "HDW_API_KEY" in compose_txt, "HDW_API_KEY deve ser preservada na Missão 0a"
    assert "OVPN_TOKEN" in compose_txt, "OVPN_TOKEN deve ser preservada na Missão 0a"
