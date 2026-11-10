"""
Modelos ORM para cartões de crédito e faturas mensais.

pq existe: SQLAlchemy Mapped/mapped_column — ORM moderno que mapeia classes
           Python diretamente em tabelas do banco sem SQL explícito.
para que no projeto: define cartoes (configuração do cartão com limites e datas)
                     e faturas (extrato mensal com status de pagamento).
"""

from decimal import Decimal
from uuid import uuid4
from sqlalchemy import String, Numeric, Integer, Boolean, Date, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP

from app.database import Base


class Cartao(Base):
    __tablename__ = "cartoes"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    usuario_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    bandeira: Mapped[str] = mapped_column(String(20), nullable=False)
    limite: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    dia_fechamento: Mapped[int] = mapped_column(Integer, nullable=False)
    dia_vencimento: Mapped[int] = mapped_column(Integer, nullable=False)
    fechar_em_dia_util: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    cor: Mapped[str] = mapped_column(String(7), nullable=False, default="#3ba6f1")
    anotacao: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    arquivado_em: Mapped[TIMESTAMP | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    criado_em: Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )


class Fatura(Base):
    __tablename__ = "faturas"
    __table_args__ = (UniqueConstraint("cartao_id", "periodo", name="uq_fatura_cartao_periodo"),)

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    cartao_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    usuario_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    periodo: Mapped[str] = mapped_column(String(7), nullable=False)  # "2026-11"
    data_fechamento: Mapped[Date] = mapped_column(Date, nullable=False)
    data_vencimento: Mapped[Date] = mapped_column(Date, nullable=False)
    valor_pago: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0"))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="aberta")
    criado_em: Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
