"""
Esquemas de dados para as rotas de autenticação do CasalEconomia.
Definem a forma dos dados de entrada e saída das rotas de registro e login.

pq existe: Pydantic BaseModel valida e converte automaticamente os dados JSON
           da requisição, gerando erros claros quando os campos são inválidos.
para que no projeto: contrato de entrada para cadastro (nome+e-mail+senha) e
                     login (e-mail+senha), e contrato de saída com a ficha JWT.
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
