"""
Modelos ORM das tabelas de lançamentos financeiros do CasalEconomia.

pq existe: SQLAlchemy Mapped/mapped_column — ORM moderno que mapeia classes
           Python diretamente em tabelas do banco sem SQL explícito.
para que no projeto: define lancamentos (movimentações financeiras de cada usuário)
                     e lancamentos_parceiro (fila de sincronização entre parceiros).
"""

from decimal import Decimal
from uuid import uuid4
from sqlalchemy import String, Numeric, Date, Integer, SmallInteger, Boolean, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP

from app.database import Base


class Lancamento(Base):
    __tablename__ = "lancamentos"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    descricao: Mapped[str] = mapped_column(String(200), nullable=False)
    valor: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    data_lancamento: Mapped[Date] = mapped_column(Date, nullable=False)
    tipo: Mapped[str] = mapped_column(String(10), nullable=False)
    usuario_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    origem: Mapped[str] = mapped_column(String(20), nullable=False, default="proprio")
    lancamento_origem_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lancamentos.id", ondelete="SET NULL"), nullable=True
    )
    cartao_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cartoes.id", ondelete="SET NULL"), nullable=True
    )
    periodo_fatura: Mapped[str | None] = mapped_column(String(7), nullable=True)
    # Campos da tarefa 07
    forma_pagamento: Mapped[str | None] = mapped_column(String(30), nullable=True)
    conta_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    liquidado: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    data_vencimento: Mapped[Date | None] = mapped_column(Date, nullable=True)
    data_liquidacao: Mapped[Date | None] = mapped_column(Date, nullable=True)
    nota: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    serie_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("series_parcelamento.id", ondelete="SET NULL"), nullable=True
    )
    parcela_atual: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    email_compartilhado: Mapped[str | None] = mapped_column(String(255), nullable=True)
    percentual_compartilhado: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    valor_compartilhado: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    categoria: Mapped[str | None] = mapped_column(String(80), nullable=True)
    valor_aproximado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Campos da tarefa 08
    fonte: Mapped[str | None] = mapped_column(String(120), nullable=True)
    valor_recebido: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    criado_em: Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    usuario = relationship("Usuario", foreign_keys=[usuario_id])


class LancamentoParceiro(Base):
    __tablename__ = "lancamentos_parceiro"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    lancamento_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lancamentos.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    usuario_dono_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    usuario_parceiro_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pendente")
    versao_fonte: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    lancamento_importado_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    snapshot_descricao: Mapped[str] = mapped_column(String(200), nullable=False)
    snapshot_valor: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    snapshot_data: Mapped[Date] = mapped_column(Date, nullable=False)
    snapshot_tipo: Mapped[str] = mapped_column(String(10), nullable=False)
    criado_em: Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    lancamento = relationship("Lancamento", foreign_keys=[lancamento_id])
    dono = relationship("Usuario", foreign_keys=[usuario_dono_id])
    parceiro = relationship("Usuario", foreign_keys=[usuario_parceiro_id])
