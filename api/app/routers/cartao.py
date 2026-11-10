"""
Rotas HTTP para cartões de crédito e faturas mensais.

pq existe: APIRouter do FastAPI agrupa rotas relacionadas com prefixo e tags,
           mantendo o main.py enxuto e os módulos coesos.
para que no projeto: expõe CRUD de cartões (com soft-delete) e operações
                     de fatura — detalhe, pagamento e histórico.
"""

from datetime import date
from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import obter_sessao
from app.models.cartao import Cartao, Fatura
from app.schemas.cartao import EntradaCartao, EntradaPagamento
from app.services import cartao as svc
from app.routers.auth import obter_usuario_atual
from datetime import datetime, timezone

roteador_cartao = APIRouter(tags=["cartões"])


@roteador_cartao.post("/cartoes", status_code=status.HTTP_201_CREATED)
def criar_cartao(
    dados: EntradaCartao,
    usuario=Depends(obter_usuario_atual),
    db: Session = Depends(obter_sessao),
):
    from uuid import uuid4
    cartao = Cartao(
        usuario_id=usuario.id,
        nome=dados.nome,
        bandeira=dados.bandeira,
        limite=dados.limite,
        dia_fechamento=dados.dia_fechamento,
        dia_vencimento=dados.dia_vencimento,
        fechar_em_dia_util=dados.fechar_em_dia_util,
        cor=dados.cor,
        anotacao=dados.anotacao,
    )
    db.add(cartao)
    db.commit()
    db.refresh(cartao)
    svc.garantir_faturas(db, cartao)
    return {"id": str(cartao.id), "nome": cartao.nome, "bandeira": cartao.bandeira, "cor": cartao.cor}


@roteador_cartao.get("/cartoes")
def listar_cartoes(
    incluir_arquivados: bool = False,
    usuario=Depends(obter_usuario_atual),
    db: Session = Depends(obter_sessao),
):
    return svc.listar_cartoes(db, usuario.id, incluir_arquivados)


@roteador_cartao.put("/cartoes/{cartao_id}")
def atualizar_cartao(
    cartao_id: UUID,
    dados: EntradaCartao,
    usuario=Depends(obter_usuario_atual),
    db: Session = Depends(obter_sessao),
):
    from fastapi import HTTPException
    cartao = db.query(Cartao).filter(Cartao.id == cartao_id, Cartao.usuario_id == usuario.id).first()
    if not cartao:
        raise HTTPException(status_code=404, detail="Cartão não encontrado.")
    if cartao.arquivado_em:
        raise HTTPException(status_code=400, detail="Cartão arquivado não pode ser editado.")
    for campo, valor in dados.model_dump(exclude_none=True).items():
        setattr(cartao, campo, valor)
    db.commit()
    svc.garantir_faturas(db, cartao)
    return {"id": str(cartao.id), "mensagem": "Cartão atualizado."}


@roteador_cartao.delete("/cartoes/{cartao_id}")
def arquivar_cartao(
    cartao_id: UUID,
    usuario=Depends(obter_usuario_atual),
    db: Session = Depends(obter_sessao),
):
    from fastapi import HTTPException
    cartao = db.query(Cartao).filter(Cartao.id == cartao_id, Cartao.usuario_id == usuario.id).first()
    if not cartao:
        raise HTTPException(status_code=404, detail="Cartão não encontrado.")
    cartao.arquivado_em = datetime.now(timezone.utc)
    db.commit()
    return {"mensagem": "Cartão arquivado."}


@roteador_cartao.get("/faturas/{fatura_id}")
def detalhe_fatura(
    fatura_id: UUID,
    usuario=Depends(obter_usuario_atual),
    db: Session = Depends(obter_sessao),
):
    return svc.detalhe_fatura(db, fatura_id, usuario.id)


@roteador_cartao.post("/faturas/{fatura_id}/pagar")
def pagar_fatura(
    fatura_id: UUID,
    dados: EntradaPagamento,
    usuario=Depends(obter_usuario_atual),
    db: Session = Depends(obter_sessao),
):
    return svc.pagar_fatura(db, fatura_id, dados.valor, usuario.id)


@roteador_cartao.get("/faturas/cartao/{cartao_id}/historico")
def historico_faturas(
    cartao_id: UUID,
    usuario=Depends(obter_usuario_atual),
    db: Session = Depends(obter_sessao),
):
    faturas = (
        db.query(Fatura)
        .filter(Fatura.cartao_id == cartao_id, Fatura.usuario_id == usuario.id)
        .order_by(Fatura.periodo.desc())
        .all()
    )
    resultado = []
    for f in faturas:
        total, st = svc.calcular_status_fatura(db, f)
        resultado.append({
            "fatura_id": str(f.id),
            "periodo": f.periodo,
            "data_vencimento": str(f.data_vencimento),
            "valor_total": str(total),
            "valor_pago": str(f.valor_pago),
            "status": st,
        })
    return resultado
