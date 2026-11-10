"""
Esquemas de dados para lançamentos financeiros e sincronização com parceiro.

pq existe: Pydantic BaseModel valida e converte os dados JSON da requisição,
           garantindo tipos corretos antes de qualquer lógica de negócio.
para que no projeto: contratos de entrada/saída para criação de lançamentos
                     (incluindo parcelamento e compartilhamento) e pendências.
"""

from decimal import Decimal
from datetime import date
from uuid import UUID
from typing import Optional
from pydantic import BaseModel


class EntradaLancamento(BaseModel):
    descricao: str
    valor: Decimal
    data_lancamento: date
    tipo: str
    cartao_id: Optional[UUID] = None
    forma_pagamento: Optional[str] = None
    conta_id: Optional[UUID] = None
    liquidado: Optional[bool] = None
    data_vencimento: Optional[date] = None
    nota: Optional[str] = None
    categoria: Optional[str] = None
    valor_aproximado: bool = False
    # Parcelamento
    parcelado: bool = False
    total_parcelas: Optional[int] = None
    parcela_inicio: int = 1
    periodo_fatura: Optional[str] = None
    # Compartilhamento
    email_compartilhado: Optional[str] = None
    percentual_compartilhado: Optional[Decimal] = None
    # Receita
    fonte: Optional[str] = None
    valor_recebido: Optional[Decimal] = None


class EntradaAtualizarLancamento(BaseModel):
    descricao: Optional[str] = None
    categoria: Optional[str] = None
    nota: Optional[str] = None
    liquidado: Optional[bool] = None
    data_liquidacao: Optional[date] = None
    valor_recebido: Optional[Decimal] = None
    fonte: Optional[str] = None


class RespostaLancamento(BaseModel):
    id: UUID
    descricao: str
    valor: Decimal
    data_lancamento: date
    tipo: str
    origem: str
    cartao_id: Optional[UUID] = None
    periodo_fatura: Optional[str] = None
    forma_pagamento: Optional[str] = None
    liquidado: Optional[bool] = None
    categoria: Optional[str] = None
    serie_id: Optional[UUID] = None
    parcela_atual: Optional[int] = None
    email_compartilhado: Optional[str] = None
    valor_compartilhado: Optional[Decimal] = None
    fonte: Optional[str] = None
    valor_recebido: Optional[Decimal] = None
    status_receita: Optional[str] = None

    model_config = {"from_attributes": True}


class RespostaPendente(BaseModel):
    id: UUID
    snapshot_descricao: str
    snapshot_valor: Decimal
    snapshot_data: date
    snapshot_tipo: str
    versao_fonte: int
    usuario_dono_id: UUID

    model_config = {"from_attributes": True}


class EntradaProcessarPendente(BaseModel):
    versao_esperada: int


class RespostaContagem(BaseModel):
    total: int


class EntradaConfirmarImportacao(BaseModel):
    linhas: list[dict]
