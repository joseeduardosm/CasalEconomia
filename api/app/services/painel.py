"""
Agregação de dados para o painel principal do CasalEconomia.

pq existe: Uma query por widget geraria N+1 requests no frontend.
           Este service faz 5 queries e retorna tudo em um único payload.
para que no projeto: alimenta o GET /painel com resumo do mês, faturas,
                     vencimentos, lançamentos recentes e dados do parceiro.
"""

from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.lancamento import Lancamento, LancamentoParceiro
from app.models.cartao import Cartao, Fatura
from app.models.convite import ConexaoCasal
from app.models.usuario import Usuario
from app.schemas.painel import (
    ResumoPainel, FaturaAberta, ProximoVencimento,
    LancamentoRecente, PendentePainel, ParceiroPainel, RespostaPainel,
)
from app.services.lancamento import calcular_status_receita


def _periodo_para_datas(mes: str):
    ano, m = int(mes[:4]), int(mes[5:7])
    inicio = date(ano, m, 1)
    if m == 12:
        fim = date(ano + 1, 1, 1)
    else:
        fim = date(ano, m + 1, 1)
    return inicio, fim


def _calcular_total_fatura(db: Session, fatura: Fatura) -> Decimal:
    rows = db.query(Lancamento.valor).filter(
        Lancamento.cartao_id == fatura.cartao_id,
        Lancamento.periodo_fatura == fatura.periodo,
    ).all()
    return sum(r.valor for r in rows) if rows else Decimal("0")


def _status_fatura(db: Session, fatura: Fatura, valor_total: Decimal) -> str:
    hoje = date.today()
    pago = fatura.valor_pago or Decimal("0")
    if valor_total > 0 and pago >= valor_total:
        return "paga"
    if pago > 0:
        return "parcialmente_paga"
    if hoje > fatura.data_vencimento:
        return "vencida"
    if hoje > fatura.data_fechamento:
        return "fechada"
    return "aberta"


def montar_painel(db: Session, usuario_id: UUID, mes: str) -> RespostaPainel:
    inicio, fim = _periodo_para_datas(mes)
    hoje = date.today()

    # 1. Resumo financeiro do mês
    lancs_mes = db.query(Lancamento).filter(
        Lancamento.usuario_id == usuario_id,
        Lancamento.data_lancamento >= inicio,
        Lancamento.data_lancamento < fim,
    ).all()

    total_receitas = sum(l.valor for l in lancs_mes if l.tipo == "receita")
    total_receitas_recebidas = sum(
        (l.valor_recebido or l.valor)
        for l in lancs_mes if l.tipo == "receita" and l.liquidado
    )
    total_despesas = sum(l.valor for l in lancs_mes if l.tipo == "despesa")
    total_despesas_pagas = sum(
        l.valor for l in lancs_mes
        if l.tipo == "despesa" and l.liquidado is True and not l.cartao_id
    )
    a_receber = sum(l.valor for l in lancs_mes if l.tipo == "receita" and not l.liquidado)
    a_pagar = sum(l.valor for l in lancs_mes if l.tipo == "despesa" and l.liquidado is False)
    saldo = total_receitas - total_despesas

    resumo = ResumoPainel(
        total_receitas=total_receitas,
        total_receitas_recebidas=total_receitas_recebidas,
        total_despesas=total_despesas,
        total_despesas_pagas=total_despesas_pagas,
        saldo=saldo,
        a_receber=a_receber,
        a_pagar=a_pagar,
    )

    # 2. Faturas abertas do período
    faturas_db = db.query(Fatura).join(
        Cartao, Cartao.id == Fatura.cartao_id
    ).filter(
        Fatura.usuario_id == usuario_id,
        Fatura.periodo == mes,
        Cartao.arquivado_em.is_(None),
    ).all()

    faturas_abertas: list[FaturaAberta] = []
    for f in faturas_db:
        cartao = db.query(Cartao).filter(Cartao.id == f.cartao_id).first()
        if not cartao:
            continue
        valor_total = _calcular_total_fatura(db, f)
        status = _status_fatura(db, f, valor_total)
        if status == "paga":
            continue
        pago = f.valor_pago or Decimal("0")
        vencendo = bool(f.data_vencimento and f.data_vencimento <= hoje + timedelta(days=5))
        faturas_abertas.append(FaturaAberta(
            fatura_id=f.id,
            cartao_id=cartao.id,
            cartao_nome=cartao.nome,
            cartao_cor=cartao.cor,
            valor_total=valor_total,
            valor_pago=pago,
            valor_restante=max(valor_total - pago, Decimal("0")),
            data_vencimento=f.data_vencimento,
            status=status,
            vencendo_em_breve=vencendo,
        ))

    # 3. Próximos vencimentos (vencidos sem pagar + próximos 14 dias)
    limite_futuro = hoje + timedelta(days=14)
    venc_db = db.query(Lancamento).filter(
        Lancamento.usuario_id == usuario_id,
        Lancamento.data_vencimento.isnot(None),
        Lancamento.liquidado == False,
        Lancamento.data_vencimento <= limite_futuro,
    ).order_by(Lancamento.data_vencimento.asc()).all()

    proximos: list[ProximoVencimento] = []
    for l in venc_db:
        dias = (l.data_vencimento - hoje).days
        proximos.append(ProximoVencimento(
            id=l.id,
            descricao=l.descricao,
            valor=l.valor,
            data_vencimento=l.data_vencimento,
            tipo=l.tipo,
            liquidado=bool(l.liquidado),
            dias_para_vencer=dias,
            vencido=dias < 0,
        ))

    # 4. Últimos 8 lançamentos do mês
    recentes_db = db.query(Lancamento).filter(
        Lancamento.usuario_id == usuario_id,
        Lancamento.data_lancamento >= inicio,
        Lancamento.data_lancamento < fim,
    ).order_by(Lancamento.data_lancamento.desc()).limit(8).all()

    recentes: list[LancamentoRecente] = []
    for l in recentes_db:
        cartao_nome = None
        if l.cartao_id:
            c = db.query(Cartao).filter(Cartao.id == l.cartao_id).first()
            cartao_nome = c.nome if c else None

        total_p = None
        if l.serie_id:
            from app.models.serie_parcelamento import SerieParcelamento
            serie = db.query(SerieParcelamento).filter(
                SerieParcelamento.id == l.serie_id
            ).first()
            total_p = serie.total_parcelas if serie else None

        status_receita = calcular_status_receita(l) if l.tipo == "receita" else None
        recentes.append(LancamentoRecente(
            id=l.id,
            descricao=l.descricao,
            valor=l.valor,
            tipo=l.tipo,
            data_lancamento=l.data_lancamento,
            forma_pagamento=l.forma_pagamento,
            liquidado=l.liquidado,
            parcela_atual=l.parcela_atual,
            total_parcelas=total_p,
            cartao_nome=cartao_nome,
            status_receita=status_receita,
        ))

    # 5. Dados do parceiro (opcional)
    parceiro_data = None
    conexao = db.query(ConexaoCasal).filter(
        (ConexaoCasal.usuario_id_1 == usuario_id) | (ConexaoCasal.usuario_id_2 == usuario_id)
    ).first()

    if conexao:
        parceiro_id = (
            conexao.usuario_id_2 if conexao.usuario_id_1 == usuario_id
            else conexao.usuario_id_1
        )
        parceiro_usuario = db.query(Usuario).filter(Usuario.id == parceiro_id).first()
        if parceiro_usuario:
            pendentes_db = db.query(LancamentoParceiro).filter(
                LancamentoParceiro.usuario_parceiro_id == usuario_id,
                LancamentoParceiro.status == "pendente",
            ).order_by(LancamentoParceiro.criado_em.desc()).all()

            pendentes_count = len(pendentes_db)
            pendentes_preview = [
                PendentePainel(
                    id=p.id,
                    snapshot_descricao=p.snapshot_descricao,
                    snapshot_valor=p.snapshot_valor,
                    snapshot_data=p.snapshot_data,
                    snapshot_tipo=p.snapshot_tipo,
                    versao_fonte=p.versao_fonte,
                )
                for p in pendentes_db[:3]
            ]

            lancs_parceiro = db.query(Lancamento).filter(
                Lancamento.usuario_id == parceiro_id,
                Lancamento.data_lancamento >= inicio,
                Lancamento.data_lancamento < fim,
            ).all()

            parceiro_data = ParceiroPainel(
                nome=parceiro_usuario.nome,
                pendentes_count=pendentes_count,
                pendentes=pendentes_preview,
                resumo_despesas=sum(l.valor for l in lancs_parceiro if l.tipo == "despesa"),
                resumo_receitas=sum(l.valor for l in lancs_parceiro if l.tipo == "receita"),
            )

    return RespostaPainel(
        resumo_mes=resumo,
        faturas_abertas=faturas_abertas,
        proximos_vencimentos=proximos,
        lancamentos_recentes=recentes,
        parceiro=parceiro_data,
    )
