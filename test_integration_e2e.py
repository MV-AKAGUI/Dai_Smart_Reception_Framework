import hashlib
import os
import subprocess
import sys
from pathlib import Path
import re
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


# ==============================================================================
# TESTES DA MISSÃO 0b2 — TRAVA DE SEGREDOS REVOGADOS HDW/OVPN (CA-01 A CA-08)
# ==============================================================================


def test_ca01_missao_0b2_script_gerar_hashes_revogados():
    """CA-01: scripts/gerar_hashes_revogados.py extrai hashes do commit ce6c3b0 e emite saída canônica."""
    script_path = Path("scripts/gerar_hashes_revogados.py")
    assert script_path.exists(), "scripts/gerar_hashes_revogados.py não encontrado"
    res = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True, timeout=30)
    assert res.returncode == 0, f"Script falhou com código {res.returncode}: {res.stderr}"
    assert res.stdout == "2 hashes gravados\n", f"Saída inesperada do script: {repr(res.stdout)}"
    assert Path("segredos_revogados.sha256").exists(), "segredos_revogados.sha256 não foi gerado pelo script"


def test_ca02_missao_0b2_formato_segredos_revogados():
    """CA-02: Formato de segredos_revogados.sha256 obedece rigorosamente à regex canônica."""
    lista_path = Path("segredos_revogados.sha256")
    assert lista_path.exists(), "segredos_revogados.sha256 não encontrado"
    linhas = [linha.strip() for linha in lista_path.read_text(encoding="utf-8").splitlines() if linha.strip()]
    assert len(linhas) == 2, f"Arquivo segredos_revogados.sha256 deve conter exatamente 2 linhas, possui {len(linhas)}"
    padrao = re.compile(r"^[a-f0-9]{64} \d+ (HDW_API_KEY|OVPN_TOKEN)$")
    variaveis = set()
    for linha in linhas:
        assert padrao.match(linha), f"Linha fora do padrão canônico: {linha}"
        variaveis.add(linha.split()[2])
    assert variaveis == {"HDW_API_KEY", "OVPN_TOKEN"}, f"Variáveis esperadas não encontradas: {variaveis}"


def test_ca03_missao_0b2_trava_lista_ausente_e_invalida_sintetico(tmp_path):
    """CA-03: verificar_revogados levanta RuntimeError canônico para lista ausente ou inválida (sintético)."""
    import hdc_hdw_bridge
    verificar_revogados = getattr(hdc_hdw_bridge, "verificar_revogados", None)
    assert verificar_revogados is not None, "Função verificar_revogados não implementada em hdc_hdw_bridge"

    # Caso 1: Lista ausente
    arquivo_ausente = tmp_path / "lista_ausente.sha256"
    with pytest.raises(RuntimeError) as exc_ausente:
        verificar_revogados(caminho_lista=arquivo_ausente, ambiente={})
    assert str(exc_ausente.value) == "lista de revogados ausente"

    # Caso 2: Lista vazia
    arquivo_vazio = tmp_path / "lista_vazia.sha256"
    arquivo_vazio.write_text("", encoding="utf-8")
    with pytest.raises(RuntimeError) as exc_vazio:
        verificar_revogados(caminho_lista=arquivo_vazio, ambiente={})
    assert str(exc_vazio.value) == "lista de revogados inválida"

    # Caso 3: Linha malformada / fora da regex
    arquivo_invalido = tmp_path / "lista_invalida.sha256"
    arquivo_invalido.write_text("hash_invalido 10 VAR_DESCONHECIDA\n", encoding="utf-8")
    with pytest.raises(RuntimeError) as exc_invalido:
        verificar_revogados(caminho_lista=arquivo_invalido, ambiente={})
    assert str(exc_invalido.value) == "lista de revogados inválida"


def test_ca04_missao_0b2_trava_credencial_revogada_sintetico(tmp_path):
    """CA-04: verificar_revogados levanta RuntimeError canônico para credencial revogada (sintético)."""
    import hdc_hdw_bridge
    verificar_revogados = getattr(hdc_hdw_bridge, "verificar_revogados", None)
    assert verificar_revogados is not None, "Função verificar_revogados não implementada em hdc_hdw_bridge"

    # Valores sintéticos de teste (sem segredos reais)
    val_sint_hdw = "sintetico_hdw_segredo_teste_123"
    val_sint_ovpn = "sintetico_ovpn_token_teste_456"
    hash_hdw = hashlib.sha256(val_sint_hdw.encode("utf-8")).hexdigest()
    hash_ovpn = hashlib.sha256(val_sint_ovpn.encode("utf-8")).hexdigest()

    lista_sintetica = tmp_path / "segredos_sinteticos.sha256"
    lista_sintetica.write_text(
        f"{hash_hdw} {len(val_sint_hdw)} HDW_API_KEY\n{hash_ovpn} {len(val_sint_ovpn)} OVPN_TOKEN\n",
        encoding="utf-8"
    )

    # Teste de bloqueio de HDW_API_KEY
    with pytest.raises(RuntimeError) as exc_hdw:
        verificar_revogados(caminho_lista=lista_sintetica, ambiente={"HDW_API_KEY": val_sint_hdw})
    assert str(exc_hdw.value) == "credencial revogada: HDW_API_KEY"

    # Teste de bloqueio de OVPN_TOKEN
    with pytest.raises(RuntimeError) as exc_ovpn:
        verificar_revogados(caminho_lista=lista_sintetica, ambiente={"OVPN_TOKEN": val_sint_ovpn})
    assert str(exc_ovpn.value) == "credencial revogada: OVPN_TOKEN"


def test_ca05_missao_0b2_inicializacao_sem_credenciais_sintetico(tmp_path):
    """CA-05: verificar_revogados conclui sem exceção quando credenciais estão ausentes ou vazias (sintético)."""
    import hdc_hdw_bridge
    verificar_revogados = getattr(hdc_hdw_bridge, "verificar_revogados", None)
    assert verificar_revogados is not None, "Função verificar_revogados não implementada em hdc_hdw_bridge"

    val_sint_hdw = "sintetico_hdw_teste"
    val_sint_ovpn = "sintetico_ovpn_teste"
    hash_hdw = hashlib.sha256(val_sint_hdw.encode("utf-8")).hexdigest()
    hash_ovpn = hashlib.sha256(val_sint_ovpn.encode("utf-8")).hexdigest()

    lista_sintetica = tmp_path / "segredos_sinteticos.sha256"
    lista_sintetica.write_text(
        f"{hash_hdw} {len(val_sint_hdw)} HDW_API_KEY\n{hash_ovpn} {len(val_sint_ovpn)} OVPN_TOKEN\n",
        encoding="utf-8"
    )

    # Ambiente vazio
    ret_vazio = verificar_revogados(caminho_lista=lista_sintetica, ambiente={})
    assert ret_vazio is None

    # Variáveis com strings vazias
    ret_strings_vazias = verificar_revogados(
        caminho_lista=lista_sintetica,
        ambiente={"HDW_API_KEY": "", "OVPN_TOKEN": ""}
    )
    assert ret_strings_vazias is None


def test_ca06_missao_0b2_janela_deslizante_substrings_sintetico(tmp_path):
    """CA-06: Pre-commit hook detecta segredos sintéticos embutidos nos 4 formatos via janela deslizante (sintético em tmp_path)."""
    hook_origem = Path(".githooks/pre-commit")
    assert hook_origem.exists(), ".githooks/pre-commit não encontrado"

    # Inicializa repositório Git temporário isolado
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.name", "Test Runner"], cwd=tmp_path, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, capture_output=True, check=True)

    # Cria diretório de hooks e copia o script
    hooks_dir = tmp_path / ".githooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    hook_destino = hooks_dir / "pre-commit"
    hook_destino.write_bytes(hook_origem.read_bytes())

    # Cria lista de bloqueio sintética no repositório temporário
    val_sintetico = "segredo_sintetico_janela_teste_789"
    hash_sintetico = hashlib.sha256(val_sintetico.encode("utf-8")).hexdigest()
    (tmp_path / "segredos_revogados.sha256").write_text(
        f"{hash_sintetico} {len(val_sintetico)} HDW_API_KEY\n",
        encoding="utf-8"
    )

    # Cria arquivo com os 4 formatos sintéticos, um por linha
    linhas = [
        f'export HDW_API_KEY="${{HDW_API_KEY:-{val_sintetico}}}"',
        f'HDW_API_KEY="{val_sintetico}"',
        f"const token = '{val_sintetico}';",
        f"prefixo_{val_sintetico}_sufixo"
    ]
    arquivo_teste = tmp_path / "arquivo_teste.txt"
    arquivo_teste.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    subprocess.run(["git", "add", "arquivo_teste.txt"], cwd=tmp_path, capture_output=True, check=True)

    res = subprocess.run([sys.executable, str(hook_destino)], cwd=tmp_path, capture_output=True, text=True)
    assert res.returncode == 1, f"Hook deveria retornar 1 para arquivo com segredo, retornou {res.returncode}"
    saida = res.stdout + res.stderr
    for num_linha in (1, 2, 3, 4):
        assert f"arquivo_teste.txt:{num_linha}" in saida, f"Referência arquivo_teste.txt:{num_linha} ausente na saída do hook"
    assert val_sintetico not in saida, "Valor sintético não deve aparecer na saída do hook"


def test_ca07_missao_0b2_varredura_arquivos_rastreados_lista_real():
    """CA-07: Varredura de integridade em arquivos rastreados via git ls-files com lista real segredos_revogados.sha256."""
    lista_path = Path("segredos_revogados.sha256")
    assert lista_path.exists(), "segredos_revogados.sha256 não encontrado"

    entradas = []
    for linha in lista_path.read_text(encoding="utf-8").splitlines():
        linha_limpa = linha.strip()
        if not linha_limpa:
            continue
        partes = linha_limpa.split()
        assert len(partes) == 3, f"Entrada inválida na lista: {linha_limpa}"
        entradas.append((partes[0], int(partes[1]), partes[2]))

    res = subprocess.run(["git", "ls-files"], capture_output=True, text=True, check=True)
    arquivos_rastreados = [f for f in res.stdout.splitlines() if f.strip()]

    ocorrencias = []
    for rel_path in arquivos_rastreados:
        p = Path(rel_path)
        if not p.is_file():
            continue
        try:
            conteudo = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        for num_linha, linha_texto in enumerate(conteudo.splitlines(), start=1):
            for hash_revogado, tam, _ in entradas:
                if len(linha_texto) < tam:
                    continue
                for i in range(len(linha_texto) - tam + 1):
                    pedaco = linha_texto[i:i + tam]
                    if hashlib.sha256(pedaco.encode("utf-8")).hexdigest() == hash_revogado:
                        ocorrencias.append(f"{rel_path}:{num_linha}")
                        break

    assert len(ocorrencias) == 0, f"Segredo revogado encontrado em: {ocorrencias}"


def test_ca08_missao_0b2_pre_commit_hook_repo_temporario(tmp_path):
    """CA-08: Pre-commit hook bloqueia commits de segredos e autoriza commits limpos (sintético em tmp_path)."""
    hook_origem = Path(".githooks/pre-commit")
    assert hook_origem.exists(), ".githooks/pre-commit não encontrado"

    # Inicializa repositório Git temporário isolado
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.name", "Test Runner"], cwd=tmp_path, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, capture_output=True, check=True)

    # Cria diretório de hooks e copia o script
    hooks_dir = tmp_path / ".githooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    hook_destino = hooks_dir / "pre-commit"
    hook_destino.write_bytes(hook_origem.read_bytes())

    # Cria lista de bloqueio sintética no repositório temporário
    val_sintetico = "segredo_sintetico_para_precommit_hook"
    hash_sintetico = hashlib.sha256(val_sintetico.encode("utf-8")).hexdigest()
    (tmp_path / "segredos_revogados.sha256").write_text(
        f"{hash_sintetico} {len(val_sintetico)} HDW_API_KEY\n",
        encoding="utf-8"
    )

    # Teste 1: Arquivo com segredo sintético em stage deve ser bloqueado
    arquivo_sujo = tmp_path / "config_vazada.py"
    arquivo_sujo.write_text(f'API_KEY = "{val_sintetico}"\n', encoding="utf-8")
    subprocess.run(["git", "add", "config_vazada.py"], cwd=tmp_path, capture_output=True, check=True)

    res_hook_bloqueio = subprocess.run([sys.executable, str(hook_destino)], cwd=tmp_path, capture_output=True, text=True)
    assert res_hook_bloqueio.returncode == 1, f"Hook deveria retornar 1 para arquivo com segredo, retornou {res_hook_bloqueio.returncode}"
    assert "config_vazada.py:1" in res_hook_bloqueio.stdout or "config_vazada.py:1" in res_hook_bloqueio.stderr
    assert val_sintetico not in res_hook_bloqueio.stdout and val_sintetico not in res_hook_bloqueio.stderr

    # Teste 2: Arquivo limpo em stage deve passar com exit code 0
    subprocess.run(["git", "reset", "HEAD", "config_vazada.py"], cwd=tmp_path, capture_output=True, check=True)
    arquivo_limpo = tmp_path / "clean_code.py"
    arquivo_limpo.write_text('print("hello world")\n', encoding="utf-8")
    subprocess.run(["git", "add", "clean_code.py"], cwd=tmp_path, capture_output=True, check=True)

    res_hook_limpo = subprocess.run([sys.executable, str(hook_destino)], cwd=tmp_path, capture_output=True, text=True)
    assert res_hook_limpo.returncode == 0, f"Hook deveria retornar 0 para arquivo limpo: {res_hook_limpo.stderr}"

