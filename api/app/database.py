"""
Configuração do banco de dados para o CasalEconomia.
Define o motor de conexão, a fábrica de sessões e a classe Base para os modelos ORM.

pq existe: SQLAlchemy é um ORM Python que abstrai SQL em objetos Python,
           permitindo consultas tipadas sem escrever SQL diretamente.
para que no projeto: cria a conexão com PostgreSQL, gerencia o ciclo de vida
                     das sessões por requisição e fornece a Base para os modelos.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Configuracoes(BaseSettings):
    """Lê as variáveis de ambiente do arquivo .env."""

    DATABASE_URL: str
    SECRET_KEY: str
    CORS_ORIGINS: str = "http://localhost:4200"

    model_config = {"env_file": ".env"}


configuracoes = Configuracoes()

# Motor de conexão com o banco de dados PostgreSQL
motor = create_engine(
    configuracoes.DATABASE_URL,
    pool_pre_ping=True,  # verifica a conexão antes de usar do pool
)

# Fábrica de sessões — cada requisição cria e fecha a sua própria sessão
FabricaSessao = sessionmaker(autocommit=False, autoflush=False, bind=motor)


class Base(DeclarativeBase):
    """Classe base para todos os modelos ORM do projeto."""
    pass


def obter_sessao():
    """Gerador de sessão para injeção de dependência no FastAPI."""
    sessao = FabricaSessao()
    try:
        yield sessao
    finally:
        sessao.close()
