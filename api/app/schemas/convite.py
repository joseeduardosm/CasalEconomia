"""
Esquemas de dados para as rotas de convite do CasalEconomia.

pq existe: Pydantic BaseModel valida e converte os dados JSON da requisição,
           gerando erros claros quando os campos estão inválidos.
para que no projeto: contrato de entrada para criar convite (nome+e-mail do
                     convidado) e de saída com a ficha do convite gerado.
"""

from pydantic import BaseModel, EmailStr


class EntradaCriarConvite(BaseModel):
    nome_convidado: str
    email_convidado: EmailStr


class RespostaConvite(BaseModel):
    token: str
    nome_convidado: str
    email_convidado: str


class RespostaDadosConvite(BaseModel):
    nome: str
    email: str


class EntradaAceitarConvite(BaseModel):
    senha: str
