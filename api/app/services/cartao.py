"""
Regras de negócio para cartões de crédito e faturas mensais.

pq existe: Service Layer concentra a lógica de negócio fora das rotas HTTP,
           tornando o código testável e reutilizável.
para que no projeto: calcula datas de fechamento/vencimento, determina o período
                     de fatura de cada lançamento e gerencia o status da fatura.
"""

import calendar
from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.cartao import Cartao, Fatura
from app.models.lancamento import Lancamento


def _avancar_para_dia_util(d: date) -> date:
    """Se cair em sábado (5) ou domingo (6), avança para segunda-feira."""
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d


def _calcular_vencimento(ano: int, mes: int, dia: int, dia_util: bool) -> date:
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    dia_real = min(dia, ultimo_dia)
    d = date(ano, mes, dia_real)
    return _avancar_para_dia_util(d) if dia_util else d


def _calcular_fechamento(
    ano_venc: int, mes_venc: int, dia_fechamento: int, dia_vencimento: int, dia_util: bool
) -> date:
    if dia_fechamento >= dia_vencimento:
        mes_fech = mes_venc - 2
        ano_fech = ano_venc
        if mes_fech <= 0:
            mes_fech += 12
            ano_fech -= 1
    else:
        mes_fech = mes_venc - 1
        ano_fech = ano_venc
        if mes_fech <= 0:
            mes_fech += 12
            ano_fech -= 1
    ultimo_dia = calendar.monthrange(ano_fech, mes_fech)[1]
    dia_real = min(dia_fechamento, ultimo_dia)
    d = date(ano_fech, mes_fech, dia_real)
    return _avancar_para_dia_util(d) if dia_util else d


def garantir_faturas(db: Session, cartao: Cartao) -> None:
    """Cria faturas para mês atual + 3 futuros. Idempotente."""
    hoje = date.today()
    for delta in range(4):
        mes = hoje.month + delta
        ano = hoje.year + (mes - 1) // 12
        mes = ((mes - 1) % 12) + 1
        periodo = f"{ano:04d}-{mes:02d}"
        existe = db.query(Fatura).filter(
            Fatura.cartao_id == cartao.id, Fatura.periodo == periodo
        ).first()
        if not existe:
            venc = _calcular_vencimento(ano, mes, cartao.dia_vencimento, False)
            fech = _calcular_fechamento(
                ano, mes, cartao.dia_fechamento, cartao.dia_vencimento, cartao.fechar_em_dia_util
            )
            fatura = Fatura(
                cartao_id=cartao.id,
                usuario_id=cartao.usuario_id,
                periodo=periodo,
                data_fechamento=fech,
                data_vencimento=venc,
            )
            db.add(fatura)
    db.commit()


def calcular_periodo_fatura(db: Session, cartao_id: UUID, data_lancamento: date) -> str:
    hoje = date.today()
    periodo_atual = f"{hoje.year:04d}-{hoje.month:02d}"
    fatura = db.query(Fatura).filter(
        Fatura.cartao_id == cartao_id, Fatura.periodo == periodo_atual
    ).first()
    if fatura and data_lancamento > fatura.data_fechamento:
        prox = date(hoje.year, hoje.month, 1) + timedelta(days=32)
        return f"{prox.year:04d}-{prox.month:02d}"
    return periodo_atual


def calcular_status_fatura(
    db: Session, fatura: Fatura
) -> tuple[Decimal, str]:
    valor_total = db.query(Lancamento).filter(
        Lancamento.cartao_id == fatura.cartao_id,
        Lancamento.periodo_fatura == fatura.periodo,
    ).with_entities(Lancamento.valor).all()
    total = sum(r.valor for r in valor_total) if valor_total else Decimal("0")

    hoje = date.today()
    pago = fatura.valor_pago or Decimal("0")

    if total > 0 and pago >= total:
        status = "paga"
    elif pago > 0:
        status = "parcialmente_paga"
    elif hoje > fatura.data_vencimento:
        status = "vencida"
    elif hoje > fatura.data_fechamento:
        status = "fechada"
    else:
        status = "aberta"

    return total, status


def listar_cartoes(db: Session, usuario_id: UUID, incluir_arquivados: bool = False):
    q = db.query(Cartao).filter(Cartao.usuario_id == usuario_id)
    if not incluir_arquivados:
        q = q.filter(Cartao.arquivado_em.is_(None))
    cartoes = q.all()
    resultado = []
    hoje = date.today()
    periodo_atual = f"{hoje.year:04d}-{hoje.month:02d}"

    for c in cartoes:
        fatura = db.query(Fatura).filter(
            Fatura.cartao_id == c.id, Fatura.periodo == periodo_atual
        ).first()
        total, status = calcular_status_fatura(db, fatura) if fatura else (Decimal("0"), "aberta")
        if fatura:
            fatura.status = status
            db.commit()

        gasto = db.query(Lancamento).filter(
            Lancamento.cartao_id == c.id,
            Lancamento.periodo_fatura == periodo_atual,
        ).with_entities(Lancamento.valor).all()
        total_gasto = sum(r.valor for r in gasto) if gasto else Decimal("0")

        resultado.append({
            "cartao": c,
            "fatura_atual": {
                "fatura_id": fatura.id if fatura else None,
                "periodo": periodo_atual,
                "data_vencimento": fatura.data_vencimento if fatura else None,
                "valor_total": total,
                "valor_pago": fatura.valor_pago if fatura else Decimal("0"),
                "status": status,
            } if fatura else None,
            "limite_disponivel": c.limite - total_gasto,
        })
    return resultado


def detalhe_fatura(db: Session, fatura_id: UUID, usuario_id: UUID):
    fatura = db.query(Fatura).filter(Fatura.id == fatura_id, Fatura.usuario_id == usuario_id).first()
    if not fatura:
        raise HTTPException(status_code=404, detail="Fatura não encontrada.")
    total, status = calcular_status_fatura(db, fatura)
    fatura.status = status
    db.commit()
    lancs = db.query(Lancamento).filter(
        Lancamento.cartao_id == fatura.cartao_id,
        Lancamento.periodo_fatura == fatura.periodo,
    ).all()
    return {
        "id": fatura.id,
        "periodo": fatura.periodo,
        "data_fechamento": fatura.data_fechamento,
        "data_vencimento": fatura.data_vencimento,
        "valor_total": total,
        "valor_pago": fatura.valor_pago,
        "valor_restante": max(total - fatura.valor_pago, Decimal("0")),
        "status": status,
        "lancamentos": [
            {
                "id": str(l.id),
                "descricao": l.descricao,
                "valor": str(l.valor),
                "data_lancamento": str(l.data_lancamento),
            }
            for l in lancs
        ],
    }


def pagar_fatura(db: Session, fatura_id: UUID, valor: Decimal, usuario_id: UUID):
    fatura = db.query(Fatura).filter(Fatura.id == fatura_id, Fatura.usuario_id == usuario_id).first()
    if not fatura:
        raise HTTPException(status_code=404, detail="Fatura não encontrada.")
    total, status = calcular_status_fatura(db, fatura)
    if status == "paga":
        raise HTTPException(status_code=400, detail="Fatura já está paga.")
    restante = max(total - fatura.valor_pago, Decimal("0"))
    if valor > restante:
        raise HTTPException(status_code=400, detail=f"Valor superior ao restante (R$ {restante:.2f}).")
    fatura.valor_pago += valor
    _, novo_status = calcular_status_fatura(db, fatura)
    fatura.status = novo_status
    db.commit()
    return {
        "mensagem": "Pagamento registrado.",
        "valor_pago": str(fatura.valor_pago),
        "valor_restante": str(max(total - fatura.valor_pago, Decimal("0"))),
        "status": novo_status,
    }
