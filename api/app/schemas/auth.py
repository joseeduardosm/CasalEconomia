"""
Schemas Pydantic para as rotas de autenticação.
Definem a forma dos dados de entrada e saída dos endpoints de registro e login.
"""

from pydantic import BaseModel, EmailStr, field_validator


class EntradaCadastro(BaseModel):
    """Dados necessários para registrar um novo usuário."""

    nome: str
    email: EmailStr
    senha: str

    @field_validator("senha")
    @classmethod
    def senha_minima(cls, v: str) -> str:
        if len(v) < 4:
            raise ValueError("A senha deve ter pelo menos 4 caracteres.")
        return v


class EntradaLogin(BaseModel):
    """Credenciais para autenticar um usuário existente."""

    email: EmailStr
    senha: str


class RespostaToken(BaseModel):
    """Token JWT retornado após autenticação bem-sucedida."""

    access_token: str
    tipo_token: str = "bearer"
