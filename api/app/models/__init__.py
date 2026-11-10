"""
Ponto de entrada dos modelos ORM.
Importa todos os modelos para que o Alembic os detecte automaticamente ao gerar migrações.
Adicione aqui cada novo modelo criado no projeto.
"""

from app.models.usuario import Usuario  # noqa: F401
from app.models.convite import Convite, ConexaoCasal  # noqa: F401
from app.models.cartao import Cartao, Fatura  # noqa: F401
from app.models.serie_parcelamento import SerieParcelamento  # noqa: F401
from app.models.lancamento import Lancamento, LancamentoParceiro  # noqa: F401
