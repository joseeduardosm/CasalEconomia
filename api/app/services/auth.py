"""
Serviço de autenticação do CasalEconomia.
Responsável por gerar e verificar tokens JWT e por fazer o hash de senhas.
"""

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.database import configuracoes

# Contexto de hash de senha usando bcrypt
_contexto_senha = CryptContext(schemes=["bcrypt"], deprecated="auto")

_ALGORITMO = "HS256"
_EXPIRACAO_DIAS = 7


def gerar_hash_senha(senha: str) -> str:
    """Retorna o hash bcrypt da senha informada."""
    return _contexto_senha.hash(senha)


def verificar_senha(senha: str, senha_hash: str) -> bool:
    """Verifica se a senha em texto plano corresponde ao hash armazenado."""
    return _contexto_senha.verify(senha, senha_hash)


def gerar_token(usuario_id: uuid.UUID) -> str:
    """Gera um token JWT com expiração de 7 dias para o usuário informado."""
    expiracao = datetime.now(timezone.utc) + timedelta(days=_EXPIRACAO_DIAS)
    carga = {"sub": str(usuario_id), "exp": expiracao}
    return jwt.encode(carga, configuracoes.SECRET_KEY, algorithm=_ALGORITMO)


def verificar_token(token: str) -> uuid.UUID:
    """Decodifica o token JWT e retorna o ID do usuário. Lança 401 se inválido."""
    try:
        carga = jwt.decode(token, configuracoes.SECRET_KEY, algorithms=[_ALGORITMO])
        usuario_id: str = carga.get("sub")
        if usuario_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido.")
        return uuid.UUID(usuario_id)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido ou expirado.")
