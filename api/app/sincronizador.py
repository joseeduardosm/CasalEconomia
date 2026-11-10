"""
Job de sincronização de lançamentos entre parceiros do CasalEconomia.

pq existe: APScheduler permite agendar funções Python em intervalos regulares
           sem depender de cron do sistema operacional.
para que no projeto: varre lançamentos 'proprio' de usuários com parceiro
                     e cria registros de pendência para o parceiro aceitar ou ignorar.
"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler

from app.database import FabricaSessao
from app.repositories import lancamento as repo

logger = logging.getLogger("sincronizador")

agendador = BackgroundScheduler()


def executar_sincronizacao() -> None:
    db = FabricaSessao()
    try:
        # Sincroniza lançamentos com parceiro
        lancamentos = repo.listar_proprios_sem_registro_parceiro(db)
        for lanc in lancamentos:
            parceiro_id = repo.buscar_parceiro_de(db, lanc.usuario_id)
            if parceiro_id:
                repo.criar_registro_parceiro(db, lanc, parceiro_id)
                logger.info("[sincronizador] Pendência: %s → parceiro %s", lanc.id, parceiro_id)

        # Garante que cartões ativos sempre têm faturas futuras
        from app.models.cartao import Cartao
        from app.services.cartao import garantir_faturas
        cartoes = db.query(Cartao).filter(Cartao.arquivado_em.is_(None)).all()
        for cartao in cartoes:
            garantir_faturas(db, cartao)
    except Exception as exc:
        logger.error("[sincronizador] Erro: %s", exc)
    finally:
        db.close()


def iniciar_agendador() -> None:
    agendador.add_job(executar_sincronizacao, "interval", seconds=60, id="sync_lancamentos")
    agendador.start()
    logger.info("[sincronizador] Agendador iniciado — sincronização a cada 60 segundos.")


def parar_agendador() -> None:
    agendador.shutdown(wait=False)
    logger.info("[sincronizador] Agendador encerrado.")
