"""
Rotas HTTP para o fluxo de convite do CasalEconomia.

pq existe: APIRouter do FastAPI agrupa rotas relacionadas com prefixo e tags,
           mantendo o main.py enxuto e os módulos coesos.
para que no projeto: expõe três endereços — criar convite (autenticado),
                     consultar dados do convite (público) e aceitar convite (público).
"""

from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import obter_sessao
from app.schemas.convite import EntradaCriarConvite, RespostaConvite, RespostaDadosConvite, EntradaAceitarConvite
from app.services import convite as svc
from app.routers.auth import obter_usuario_atual

roteador_convite = APIRouter(prefix="/convites", tags=["convites"])


@roteador_convite.post("", status_code=status.HTTP_201_CREATED, response_model=RespostaConvite)
def criar_convite(
    dados: EntradaCriarConvite,
    usuario_atual=Depends(obter_usuario_atual),
    db: Session = Depends(obter_sessao),
):
    convite = svc.criar_convite(
        db,
        nome=dados.nome_convidado,
        email=dados.email_convidado,
        remetente_id=usuario_atual.id,
    )
    return RespostaConvite(
        token=str(convite.token),
        nome_convidado=convite.nome_convidado,
        email_convidado=convite.email_convidado,
    )


@roteador_convite.get("/{token}", response_model=RespostaDadosConvite)
def consultar_convite(token: UUID, db: Session = Depends(obter_sessao)):
    convite = svc.buscar_convite(db, token)
    return RespostaDadosConvite(nome=convite.nome_convidado, email=convite.email_convidado)


@roteador_convite.post("/{token}/aceitar", status_code=status.HTTP_204_NO_CONTENT)
def aceitar_convite(
    token: UUID,
    dados: EntradaAceitarConvite,
    db: Session = Depends(obter_sessao),
):
    svc.aceitar_convite(db, token=token, senha=dados.senha)
