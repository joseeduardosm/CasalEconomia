"""
Modelo ORM das tabelas de convite e conexão do casal no CasalEconomia.

pq existe: SQLAlchemy Mapped/mapped_column — API moderna do ORM que mapeia
           classes Python em tabelas do banco sem SQL explícito.
para que no projeto: define convites (link único de uso único para convidar
                     parceiro) e conexoes_casal (vínculo entre dois usuários).
"""

from uuid import uuid4
from sqlalchemy import String, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP

from app.database import Base


class Convite(Base):
    """Tabela `convites` — cada linha é um convite pendente ou já utilizado."""

    __tablename__ = "convites"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    token: Mapped[UUID] = mapped_column(UUID(as_uuid=True), unique=True, index=True, default=uuid4)
    nome_convidado: Mapped[str] = mapped_column(String(100), nullable=False)
    email_convidado: Mapped[str] = mapped_column(String(255), nullable=False)
    remetente_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    usado_em: Mapped[TIMESTAMP | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    criado_em: Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    remetente = relationship("Usuario", foreign_keys=[remetente_id])


class ConexaoCasal(Base):
    """Tabela `conexoes_casal` — vínculo sem hierarquia entre dois usuários."""

    __tablename__ = "conexoes_casal"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    usuario_id_1: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    usuario_id_2: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    criado_em: Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    parceiro_1 = relationship("Usuario", foreign_keys=[usuario_id_1])
    parceiro_2 = relationship("Usuario", foreign_keys=[usuario_id_2])
