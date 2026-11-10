"""
Repositório de lançamentos financeiros e pendências de parceiro.

pq existe: Repository Pattern isola as consultas SQL do restante da aplicação,
           facilitando testes e futuras trocas de banco de dados.
para que no projeto: centraliza operações nas tabelas lancamentos e
                     lancamentos_parceiro, usadas pelo serviço e pelo sincronizador.
"""

from decimal import Decimal
from datetime import date
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.lancamento import Lancamento, LancamentoParceiro
from app.models.convite import ConexaoCasal


def criar_lancamento(
    db: Session,
    descricao: str,
    valor: Decimal,
    data_lancamento: date,
    tipo: str,
    usuario_id: UUID,
    origem: str = "proprio",
    lancamento_origem_id: UUID | None = None,
    cartao_id: UUID | None = None,
    periodo_fatura: str | None = None,
    forma_pagamento: str | None = None,
    liquidado: bool | None = None,
    data_vencimento: date | None = None,
    nota: str | None = None,
    categoria: str | None = None,
    valor_aproximado: bool = False,
    serie_id: UUID | None = None,
    parcela_atual: int | None = None,
    email_compartilhado: str | None = None,
    percentual_compartilhado: Decimal | None = None,
    valor_compartilhado: Decimal | None = None,
) -> Lancamento:
    lanc = Lancamento(
        descricao=descricao, valor=valor, data_lancamento=data_lancamento,
        tipo=tipo, usuario_id=usuario_id, origem=origem,
        lancamento_origem_id=lancamento_origem_id, cartao_id=cartao_id,
        periodo_fatura=periodo_fatura, forma_pagamento=forma_pagamento,
        liquidado=liquidado, data_vencimento=data_vencimento, nota=nota,
        categoria=categoria, valor_aproximado=valor_aproximado,
        serie_id=serie_id, parcela_atual=parcela_atual,
        email_compartilhado=email_compartilhado,
        percentual_compartilhado=percentual_compartilhado,
        valor_compartilhado=valor_compartilhado,
    )
    db.add(lanc)
    db.commit()
    db.refresh(lanc)
    return lanc


def listar_por_usuario(
    db: Session,
    usuario_id: UUID,
    mes: str | None = None,
    cartao_id: UUID | None = None,
    liquidado: bool | None = None,
    tipo: str | None = None,
) -> list[Lancamento]:
    q = db.query(Lancamento).filter(Lancamento.usuario_id == usuario_id)
    if mes:
        from datetime import date as _date, timedelta
        ano, m = int(mes[:4]), int(mes[5:7])
        inicio = _date(ano, m, 1)
        if m == 12:
            fim = _date(ano + 1, 1, 1)
        else:
            fim = _date(ano, m + 1, 1)
        q = q.filter(Lancamento.data_lancamento >= inicio, Lancamento.data_lancamento < fim)
    if cartao_id:
        q = q.filter(Lancamento.cartao_id == cartao_id)
    if liquidado is not None:
        q = q.filter(Lancamento.liquidado == liquidado)
    if tipo:
        q = q.filter(Lancamento.tipo == tipo)
    return q.order_by(Lancamento.data_lancamento.desc(), Lancamento.criado_em.desc()).all()


def listar_proprios_sem_registro_parceiro(db: Session) -> list[Lancamento]:
    """Retorna lançamentos 'proprio' de usuários que têm parceiro e ainda não geraram registro."""
    subq = db.query(LancamentoParceiro.lancamento_id).subquery()
    return (
        db.query(Lancamento)
        .join(ConexaoCasal, (
            (ConexaoCasal.usuario_id_1 == Lancamento.usuario_id)
            | (ConexaoCasal.usuario_id_2 == Lancamento.usuario_id)
        ))
        .filter(Lancamento.origem == "proprio")
        .filter(Lancamento.id.notin_(subq))
        .all()
    )


def buscar_parceiro_de(db: Session, usuario_id: UUID) -> UUID | None:
    conexao = (
        db.query(ConexaoCasal)
        .filter(
            (ConexaoCasal.usuario_id_1 == usuario_id)
            | (ConexaoCasal.usuario_id_2 == usuario_id)
        )
        .first()
    )
    if not conexao:
        return None
    return conexao.usuario_id_2 if conexao.usuario_id_1 == usuario_id else conexao.usuario_id_1


def criar_registro_parceiro(
    db: Session,
    lancamento: Lancamento,
    usuario_parceiro_id: UUID,
) -> LancamentoParceiro:
    reg = LancamentoParceiro(
        lancamento_id=lancamento.id,
        usuario_dono_id=lancamento.usuario_id,
        usuario_parceiro_id=usuario_parceiro_id,
        snapshot_descricao=lancamento.descricao,
        snapshot_valor=lancamento.valor,
        snapshot_data=lancamento.data_lancamento,
        snapshot_tipo=lancamento.tipo,
    )
    db.add(reg)
    db.commit()
    return reg


def listar_pendentes_do_parceiro(db: Session, usuario_id: UUID) -> list[LancamentoParceiro]:
    return (
        db.query(LancamentoParceiro)
        .filter(
            LancamentoParceiro.usuario_parceiro_id == usuario_id,
            LancamentoParceiro.status == "pendente",
        )
        .order_by(LancamentoParceiro.criado_em.desc())
        .all()
    )


def contar_pendentes(db: Session, usuario_id: UUID) -> int:
    return (
        db.query(LancamentoParceiro)
        .filter(
            LancamentoParceiro.usuario_parceiro_id == usuario_id,
            LancamentoParceiro.status == "pendente",
        )
        .count()
    )


def buscar_pendente_por_id(db: Session, registro_id: UUID, usuario_id: UUID) -> LancamentoParceiro | None:
    return (
        db.query(LancamentoParceiro)
        .filter(
            LancamentoParceiro.id == registro_id,
            LancamentoParceiro.usuario_parceiro_id == usuario_id,
        )
        .first()
    )
