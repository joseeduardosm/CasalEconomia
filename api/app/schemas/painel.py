"""
Esquemas de saída do endpoint agregado /painel.

pq existe: Pydantic BaseModel tipifica e valida a resposta do painel
           antes de serializar para JSON.
para que no projeto: contrato único que o frontend consome para montar
                     todos os widgets do dashboard.
"""

from decimal import Decimal
from datetime import date
from uuid import UUID
from typing import Optional
from pydantic import BaseModel


class ResumoPainel(BaseModel):
    total_receitas: Decimal
    total_receitas_recebidas: Decimal
    total_despesas: Decimal
    total_despesas_pagas: Decimal
    saldo: Decimal
    a_receber: Decimal
    a_pagar: Decimal


class FaturaAberta(BaseModel):
    fatura_id: UUID
    cartao_id: UUID
    cartao_nome: str
    cartao_cor: str
    valor_total: Decimal
    valor_pago: Decimal
    valor_restante: Decimal
    data_vencimento: Optional[date] = None
    status: str
    vencendo_em_breve: bool


class ProximoVencimento(BaseModel):
    id: UUID
    descricao: str
    valor: Decimal
    data_vencimento: date
    tipo: str
    liquidado: bool
    dias_para_vencer: int
    vencido: bool


class LancamentoRecente(BaseModel):
    id: UUID
    descricao: str
    valor: Decimal
    tipo: str
    data_lancamento: date
    forma_pagamento: Optional[str] = None
    liquidado: Optional[bool] = None
    parcela_atual: Optional[int] = None
    total_parcelas: Optional[int] = None
    cartao_nome: Optional[str] = None
    status_receita: Optional[str] = None


class PendentePainel(BaseModel):
    id: UUID
    snapshot_descricao: str
    snapshot_valor: Decimal
    snapshot_data: date
    snapshot_tipo: str
    versao_fonte: int


class ParceiroPainel(BaseModel):
    nome: str
    pendentes_count: int
    pendentes: list[PendentePainel]
    resumo_despesas: Decimal
    resumo_receitas: Decimal


class RespostaPainel(BaseModel):
    usuario_nome: str
    resumo_mes: ResumoPainel
    faturas_abertas: list[FaturaAberta]
    proximos_vencimentos: list[ProximoVencimento]
    lancamentos_recentes: list[LancamentoRecente]
    parceiro: Optional[ParceiroPainel] = None

    model_config = {"from_attributes": True}
