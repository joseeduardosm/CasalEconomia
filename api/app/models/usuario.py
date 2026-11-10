"""
Modelo ORM da tabela de usuários do CasalEconomia.
Representa cada pessoa cadastrada, com e-mail único e senha cifrada.

pq existe: SQLAlchemy Mapped/mapped_column é a API moderna do ORM —
           cada classe Python vira uma tabela, cada atributo vira uma coluna.
para que no projeto: define a estrutura da tabela `users` no PostgreSQL,
                     mapeando id, nome, e-mail, hash de senha e data de criação.
"""

from uuid import uuid4
from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP

from app.database import Base


class Usuario(Base):
    """Tabela `users` — cada linha é um usuário registrado no sistema."""

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    criado_em: Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
