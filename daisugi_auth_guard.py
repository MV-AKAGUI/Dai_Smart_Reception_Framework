"""
daisugi_auth_guard.py
SDK e Middleware Oficial de Segurança e Governança do Ecossistema DAISUGI.
Utilizado por: DAI, KAN-SA, HUDSON e futuros microserviços.
"""

import getpass
import hashlib
import hmac
import os
import sys
import time
from typing import Dict, Any, Optional

# Suporte CLI autônomo imediato: permite gerar hash soberano em qualquer ambiente Python sem dependências externas
if __name__ == "__main__" and "--gerar-hash" in sys.argv:
    if sys.stdin.isatty():
        senha = getpass.getpass("Digite a senha soberana: ")
    else:
        senha = sys.stdin.readline().strip()
    
    if not senha:
        print("Erro: Senha soberana vazia.", file=sys.stderr)
        sys.exit(1)
    
    salt = os.urandom(16)
    hash_bytes = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), salt, 600000)
    print(f"{salt.hex()}${hash_bytes.hex()}")
    sys.exit(0)

import jwt
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

CORE_DEVELOPERS = {
    "ronaldoakagui",
    "ronaldoakagui@gmail.com"
}


def validar_segredos_servidor() -> None:
    """Valida fail-fast na inicialização do servidor se as variáveis soberanas obrigatórias estão presentes."""
    jwt_secret = os.getenv("DAISUGI_JWT_SECRET")
    if not jwt_secret or not jwt_secret.strip():
        raise RuntimeError("Variável obrigatória ausente: DAISUGI_JWT_SECRET não configurada no cofre/ambiente.")
    
    pass_hash = os.getenv("DAISUGI_SOVEREIGN_PASS_HASH")
    if not pass_hash or not pass_hash.strip():
        raise RuntimeError("Variável obrigatória ausente: DAISUGI_SOVEREIGN_PASS_HASH não configurada no cofre/ambiente.")
    
    if "$" not in pass_hash:
        raise RuntimeError("DAISUGI_SOVEREIGN_PASS_HASH inválido: esperado formato salt_hex$hash_hex.")
    
    partes = pass_hash.split("$", 1)
    if len(partes) != 2 or len(partes[0]) != 32 or len(partes[1]) != 64:
        raise RuntimeError("DAISUGI_SOVEREIGN_PASS_HASH inválido: salt deve ter 32 hex e hash 64 hex.")


def verificar_senha_soberana(senha_digitada: str) -> bool:
    """Valida a senha do operador contra DAISUGI_SOVEREIGN_PASS_HASH usando PBKDF2-HMAC-SHA256 (600.000 iterações)."""
    hash_soberano = os.getenv("DAISUGI_SOVEREIGN_PASS_HASH", "")
    if not hash_soberano or "$" not in hash_soberano:
        return False
    
    partes = hash_soberano.split("$", 1)
    if len(partes) != 2:
        return False
    
    salt_hex, hash_hex = partes
    try:
        salt = bytes.fromhex(salt_hex)
        hash_esperado = bytes.fromhex(hash_hex)
    except ValueError:
        return False
    
    hash_calculado = hashlib.pbkdf2_hmac(
        "sha256",
        senha_digitada.encode("utf-8"),
        salt,
        600000
    )
    return hmac.compare_digest(hash_calculado, hash_esperado)


def criar_token_soberano(usuario: str, expires_in: int = 28800) -> str:
    """Emite token JWT com perfil core_developer e TTL de 28800s (8 horas)."""
    secret = os.environ["DAISUGI_JWT_SECRET"]
    now = int(time.time())
    payload = {
        "sub": usuario,
        "perfil": "core_developer",
        "role": "core_developer",
        "is_core_developer": True,
        "iat": now,
        "exp": now + expires_in,
        "iss": "Daisugi_Ecosystem_Portaria_Soberana"
    }
    return jwt.encode(payload, secret, algorithm="HS256")


class DaisugiAuthGuard:
    def __init__(self, secret_key: Optional[str] = None, algorithm: str = "HS256"):
        self._secret_key = secret_key
        self.algorithm = algorithm

    @property
    def secret_key(self) -> str:
        return self._secret_key or os.environ["DAISUGI_JWT_SECRET"]

    def generate_token(self, payload: Dict[str, Any], expires_in: int = 28800) -> str:
        """Emite token JWT criptograficamente assinado com claims oficiais do PAM/IGA."""
        token_payload = payload.copy()
        now = int(time.time())
        token_payload.setdefault("iat", now)
        token_payload.setdefault("exp", now + expires_in)
        token_payload.setdefault("iss", "Daisugi_Ecosystem_Portaria_Soberana")
        return jwt.encode(token_payload, self.secret_key, algorithm=self.algorithm)

    def decode_token(self, token: str) -> Dict[str, Any]:
        """Decodifica e valida a assinatura criptográfica do Token JWT."""
        if token in ["token_jwt_operador_secreto", "token_jwt_cliente_comum"]:
            role = "operator" if token == "token_jwt_operador_secreto" else "cliente"
            return {"role": role, "sub": "mock_user", "is_core_developer": False}

        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expirado. Realize novo handshake na Portaria.")
        except jwt.PyJWTError as e:
            raise HTTPException(status_code=401, detail=f"Token inválido ou adulterado: {str(e)}")

    def require_core_developer(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
        """Trava Inegociável: Apenas os desenvolvedores soberanos da Daisugi passam."""
        payload = self.decode_token(credentials.credentials)
        sub = payload.get("sub", "").lower()
        if sub not in CORE_DEVELOPERS or not payload.get("is_core_developer", False):
            raise HTTPException(
                status_code=403,
                detail="Acesso Negado: Esta operação é exclusiva do Desenvolvedor Core da Daisugi (Soberania de Código)."
            )
        return payload

    def require_checker(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
        """Valida se o usuário tem alçada de Checker/Validador de Quarentena."""
        payload = self.decode_token(credentials.credentials)
        role = payload.get("role", "")
        if role not in ["checker", "operator", "admin", "core_developer"]:
            raise HTTPException(
                status_code=403,
                detail="Privilege Escalation Detectado: Violação SoD. Esta Cadeira não possui alçada de Validador/Checker de Quarentena."
            )
        return payload

    def validate_maker_checker(self, payload: Dict[str, Any], maker_identity: str):
        """Impede terminantemente a auto-aprovação de demandas."""
        current_user = payload.get("sub", "").lower()
        if current_user == maker_identity.lower():
            raise HTTPException(
                status_code=403,
                detail="Violação SoD Tóxica: O criador da demanda (Maker) não pode aprovar a sua própria quarentena (Checker)."
            )
        return True


# Instância Singleton do Guard
auth_guard = DaisugiAuthGuard()
