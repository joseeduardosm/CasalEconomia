"""
Rota HTTP para o endpoint agregado do painel principal.

pq existe: APIRouter do FastAPI agrupa a rota do painel com tag e prefixo,
           mantendo o main.py enxuto.
para que no projeto: expõe GET /painel que retorna todos os dados
                     necessários para o dashboard em uma única chamada.
"""

from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import obter_sessao
from app.schemas.painel import RespostaPainel
from app.services import painel as svc
from app.routers.auth import obter_usuario_atual

roteador_painel = APIRouter(tags=["painel"])


@roteador_painel.get("/painel", response_model=RespostaPainel)
def obter_painel(
    mes: str = Query(default=None),
    usuario=Depends(obter_usuario_atual),
    db: Session = Depends(obter_sessao),
):
    if not mes:
        hoje = date.today()
        mes = f"{hoje.year:04d}-{hoje.month:02d}"
    return svc.montar_painel(db, usuario.id, mes)
