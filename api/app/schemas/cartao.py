"""
Esquemas de dados para cartões de crédito e faturas.

pq existe: Pydantic BaseModel valida e converte os dados JSON da requisição,
           garantindo tipos corretos antes de qualquer lógica de negócio.
para que no projeto: contratos de entrada/saída para criação de cartões,
                     listagem com fatura atual embutida e operação de pagamento.
"""

from decimal import Decimal
from datetime import date
from uuid import UUID
from typing import Optional
from pydantic import BaseModel


class EntradaCartao(BaseModel):
    nome: str
    bandeira: str
    limite: Decimal
    dia_fechamento: int
    dia_vencimento: int
    fechar_em_dia_util: bool = False
    cor: str = "#3ba6f1"
    anotacao: Optional[str] = None


class RespostaFaturaResumo(BaseModel):
    fatura_id: UUID
    periodo: str
    data_vencimento: date
    valor_total: Decimal
    valor_pago: Decimal
    status: str

    model_config = {"from_attributes": True}


class RespostaCartao(BaseModel):
    id: UUID
    nome: str
    bandeira: str
    limite: Decimal
    dia_fechamento: int
    dia_vencimento: int
    fechar_em_dia_util: bool
    cor: str
    anotacao: Optional[str]
    fatura_atual: Optional[RespostaFaturaResumo]
    limite_disponivel: Decimal

    model_config = {"from_attributes": True}


class RespostaFaturaDetalhe(BaseModel):
    id: UUID
    periodo: str
    data_fechamento: date
    data_vencimento: date
    valor_total: Decimal
    valor_pago: Decimal
    valor_restante: Decimal
    status: str
    lancamentos: list[dict]

    model_config = {"from_attributes": True}


class EntradaPagamento(BaseModel):
    valor: Decimal
