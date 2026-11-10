"""
Rotas HTTP para lançamentos financeiros e sincronização com parceiro.

pq existe: APIRouter do FastAPI agrupa rotas relacionadas com prefixo e tags,
           mantendo o main.py enxuto e os módulos coesos.
para que no projeto: expõe criação, listagem, edição, exclusão de lançamentos,
                     importação XLSX e ações sobre pendências do parceiro.
"""

from uuid import UUID
from fastapi import APIRouter, Depends, File, UploadFile, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import obter_sessao
from app.schemas.lancamento import (
    EntradaLancamento, EntradaAtualizarLancamento, RespostaLancamento,
    RespostaPendente, EntradaProcessarPendente, RespostaContagem,
    EntradaConfirmarImportacao,
)
from app.services import lancamento as svc
from app.repositories import lancamento as repo
from app.routers.auth import obter_usuario_atual

roteador_lancamento = APIRouter(tags=["lançamentos"])


@roteador_lancamento.post("/lancamentos", status_code=status.HTTP_201_CREATED, response_model=RespostaLancamento)
def criar_lancamento(
    dados: EntradaLancamento,
    usuario=Depends(obter_usuario_atual),
    db: Session = Depends(obter_sessao),
):
    return svc.criar_lancamento(
        db,
        descricao=dados.descricao,
        valor=dados.valor,
        data_lancamento=dados.data_lancamento,
        tipo=dados.tipo,
        usuario_id=usuario.id,
        cartao_id=dados.cartao_id,
        forma_pagamento=dados.forma_pagamento,
        liquidado=dados.liquidado,
        data_vencimento=dados.data_vencimento,
        nota=dados.nota,
        categoria=dados.categoria,
        valor_aproximado=dados.valor_aproximado,
        parcelado=dados.parcelado,
        total_parcelas=dados.total_parcelas,
        parcela_inicio=dados.parcela_inicio,
        periodo_fatura_explicito=dados.periodo_fatura,
        email_compartilhado=dados.email_compartilhado,
        percentual_compartilhado=dados.percentual_compartilhado,
        fonte=dados.fonte,
        valor_recebido=dados.valor_recebido,
    )


@roteador_lancamento.get("/lancamentos", response_model=list[RespostaLancamento])
def listar_lancamentos(
    mes: str = Query(default=None),
    cartao_id: UUID = Query(default=None),
    liquidado: bool = Query(default=None),
    tipo: str = Query(default=None),
    usuario=Depends(obter_usuario_atual),
    db: Session = Depends(obter_sessao),
):
    from datetime import date as _date
    if not mes:
        hoje = _date.today()
        mes = f"{hoje.year:04d}-{hoje.month:02d}"
    lista = repo.listar_por_usuario(db, usuario.id, mes=mes, cartao_id=cartao_id, liquidado=liquidado, tipo=tipo)
    return [svc.enriquecer_lancamento(l) for l in lista]


@roteador_lancamento.put("/lancamentos/{lancamento_id}", response_model=RespostaLancamento)
def atualizar_lancamento(
    lancamento_id: UUID,
    dados: EntradaAtualizarLancamento,
    escopo: str = Query(default="individual"),
    usuario=Depends(obter_usuario_atual),
    db: Session = Depends(obter_sessao),
):
    from fastapi import HTTPException
    from app.models.lancamento import Lancamento
    lanc = db.query(Lancamento).filter(Lancamento.id == lancamento_id, Lancamento.usuario_id == usuario.id).first()
    if not lanc:
        raise HTTPException(status_code=404, detail="Lançamento não encontrado.")

    if escopo == "serie" and lanc.serie_id:
        alvos = db.query(Lancamento).filter(Lancamento.serie_id == lanc.serie_id).all()
        for alvo in alvos:
            if dados.descricao is not None:
                alvo.descricao = dados.descricao
            if dados.categoria is not None:
                alvo.categoria = dados.categoria
            if dados.nota is not None:
                alvo.nota = dados.nota
        db.commit()
        db.refresh(lanc)
        return svc.enriquecer_lancamento(lanc)

    # Lógica especial de receita ao marcar recebido
    if dados.liquidado is True and lanc.tipo == "receita":
        vr = dados.valor_recebido if dados.valor_recebido is not None else lanc.valor
        if vr <= 0:
            raise HTTPException(status_code=400, detail="Valor recebido deve ser positivo.")
        if vr > lanc.valor:
            raise HTTPException(status_code=400, detail="Valor recebido não pode ser superior ao valor esperado.")
        lanc.liquidado = True
        lanc.valor_recebido = vr
        from datetime import date as _date
        lanc.data_liquidacao = _date.today()
    elif dados.liquidado is False and lanc.tipo == "receita":
        lanc.liquidado = False
        lanc.valor_recebido = None
        lanc.data_liquidacao = None
    else:
        for campo, val in dados.model_dump(exclude_none=True).items():
            setattr(lanc, campo, val)
    db.commit()
    db.refresh(lanc)
    return svc.enriquecer_lancamento(lanc)


@roteador_lancamento.delete("/lancamentos/{lancamento_id}")
def excluir_lancamento(
    lancamento_id: UUID,
    escopo: str = Query(default="individual"),
    usuario=Depends(obter_usuario_atual),
    db: Session = Depends(obter_sessao),
):
    from fastapi import HTTPException
    from app.models.lancamento import Lancamento, LancamentoParceiro
    lanc = db.query(Lancamento).filter(Lancamento.id == lancamento_id, Lancamento.usuario_id == usuario.id).first()
    if not lanc:
        raise HTTPException(status_code=404, detail="Lançamento não encontrado.")

    if escopo == "serie" and lanc.serie_id:
        alvos = (
            db.query(Lancamento)
            .filter(
                Lancamento.serie_id == lanc.serie_id,
                Lancamento.parcela_atual >= (lanc.parcela_atual or 1),
            )
            .all()
        )
        for alvo in alvos:
            db.query(LancamentoParceiro).filter(LancamentoParceiro.lancamento_id == alvo.id).delete()
            db.delete(alvo)
        db.commit()
        return {"mensagem": f"{len(alvos)} parcelas excluídas."}

    db.query(LancamentoParceiro).filter(LancamentoParceiro.lancamento_id == lanc.id).delete()
    db.delete(lanc)
    db.commit()
    return {"mensagem": "Lançamento excluído."}


@roteador_lancamento.get("/lancamentos/modelo-importacao")
def baixar_modelo(usuario=Depends(obter_usuario_atual)):
    conteudo = svc.gerar_modelo_xlsx()
    return Response(
        content=conteudo,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=\"modelo-lancamentos.xlsx\""},
    )


@roteador_lancamento.post("/lancamentos/importar")
async def importar_lancamentos(
    arquivo: UploadFile = File(...),
    usuario=Depends(obter_usuario_atual),
    db: Session = Depends(obter_sessao),
):
    conteudo = await arquivo.read()
    return svc.validar_importacao(conteudo, usuario.id, db)


@roteador_lancamento.post("/lancamentos/importar/confirmar", status_code=status.HTTP_201_CREATED)
def confirmar_importacao(
    dados: EntradaConfirmarImportacao,
    usuario=Depends(obter_usuario_atual),
    db: Session = Depends(obter_sessao),
):
    criados = svc.confirmar_importacao(dados.linhas, usuario.id, db)
    return {"criados": criados}


@roteador_lancamento.get("/parceiro/pendentes/contagem", response_model=RespostaContagem)
def contar_pendentes(usuario=Depends(obter_usuario_atual), db: Session = Depends(obter_sessao)):
    return RespostaContagem(total=repo.contar_pendentes(db, usuario.id))


@roteador_lancamento.get("/parceiro/pendentes", response_model=list[RespostaPendente])
def listar_pendentes(usuario=Depends(obter_usuario_atual), db: Session = Depends(obter_sessao)):
    return repo.listar_pendentes_do_parceiro(db, usuario.id)


@roteador_lancamento.post("/parceiro/{registro_id}/aceitar")
def aceitar_pendente(
    registro_id: UUID,
    dados: EntradaProcessarPendente,
    usuario=Depends(obter_usuario_atual),
    db: Session = Depends(obter_sessao),
):
    return svc.aceitar_pendente(db, registro_id, dados.versao_esperada, usuario.id)


@roteador_lancamento.post("/parceiro/{registro_id}/ignorar")
def ignorar_pendente(
    registro_id: UUID,
    dados: EntradaProcessarPendente,
    usuario=Depends(obter_usuario_atual),
    db: Session = Depends(obter_sessao),
):
    return svc.ignorar_pendente(db, registro_id, dados.versao_esperada, usuario.id)
