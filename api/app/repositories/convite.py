"""
Repositório de acesso a dados para convites e conexões do casal.

pq existe: Repository Pattern isola as consultas SQL do restante da aplicação,
           permitindo trocar o banco sem alterar regras de negócio.
para que no projeto: centraliza buscas e inserções nas tabelas convites
                     e conexoes_casal, usadas pelo serviço de convite.
"""

from uuid import UUID
from sqlalchemy.orm import Session
from app.models.convite import Convite, ConexaoCasal


def buscar_por_token(db: Session, token: UUID) -> Convite | None:
    return db.query(Convite).filter(Convite.token == token).first()


def criar_convite(db: Session, nome: str, email: str, remetente_id: UUID) -> Convite:
    convite = Convite(nome_convidado=nome, email_convidado=email, remetente_id=remetente_id)
    db.add(convite)
    db.commit()
    db.refresh(convite)
    return convite


def marcar_usado(db: Session, convite: Convite) -> None:
    from datetime import datetime, timezone
    convite.usado_em = datetime.now(timezone.utc)
    db.commit()


def criar_conexao(db: Session, uid1: UUID, uid2: UUID) -> ConexaoCasal:
    conexao = ConexaoCasal(usuario_id_1=uid1, usuario_id_2=uid2)
    db.add(conexao)
    db.commit()
    db.refresh(conexao)
    return conexao


def buscar_conexao(db: Session, usuario_id: UUID) -> ConexaoCasal | None:
    return (
        db.query(ConexaoCasal)
        .filter(
            (ConexaoCasal.usuario_id_1 == usuario_id)
            | (ConexaoCasal.usuario_id_2 == usuario_id)
        )
        .first()
    )
