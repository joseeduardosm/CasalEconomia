"""
Modelo ORM para a tabela de séries de parcelamento.

pq existe: SQLAlchemy Mapped/mapped_column — ORM moderno sem SQL explícito.
para que no projeto: agrupa as parcelas de uma compra parcelada sob um mesmo
                     registro-pai, permitindo edição e exclusão por série.
"""

from decimal import Decimal
from uuid import uuid4
from sqlalchemy import SmallInteger, Numeric, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP

from app.database import Base


class SerieParcelamento(Base):
    __tablename__ = "series_parcelamento"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    usuario_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    total_parcelas: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    parcela_inicio: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    valor_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    criado_em: Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
