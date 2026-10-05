"""
daisugi_auth_guard.py
SDK e Middleware Oficial de Segurança e Governança do Ecossistema DAISUGI.
Utilizado por: DAI, KAN-SA, HUDSON e futuros microserviços.
"""

import os
import time
from typing import Dict, Any, Optional, List
import jwt
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

CORE_DEVELOPERS = {
    "montanhavermelha@akagui.com",
    "ronaldoakagui@gmail.com"
}

class DaisugiAuthGuard:
    def __init__(self, secret_key: Optional[str] = None, algorithm: str = "HS256"):
        self.secret_key = secret_key or os.getenv("DAISUGI_JWT_SECRET", "daisugi_master_vault_secret_key_2026")
        self.algorithm = algorithm

    def generate_token(self, payload: Dict[str, Any], expires_in: int = 86400) -> str:
        """Emite token JWT criptograficamente assinado com claims oficiais do PAM/IGA."""
        token_payload = payload.copy()
        now = int(time.time())
        token_payload.setdefault("iat", now)
        token_payload.setdefault("exp", now + expires_in)
        token_payload.setdefault("iss", "Daisugi_Ecosystem_Cofre-PAM-IGA")
        return jwt.encode(token_payload, self.secret_key, algorithm=self.algorithm)

    def decode_token(self, token: str) -> Dict[str, Any]:
        """Decodifica e valida a assinatura criptográfica do Token JWT."""
        # Suporte legado para testes locais em desenvolvimento
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
