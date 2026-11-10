"""
Ponto de entrada dos modelos ORM.
Importa todos os modelos para que o Alembic os detecte automaticamente ao gerar migrações.
Adicione aqui cada novo modelo criado no projeto.
"""

from app.models.usuario import Usuario  # noqa: F401
