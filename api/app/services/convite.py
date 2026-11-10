"""
Regras de negócio para criação e aceitação de convites entre parceiros.

pq existe: Service Layer concentra a lógica de negócio fora das rotas HTTP,
           tornando o código testável e reutilizável.
para que no projeto: orquestra a criação do convite com link único, validação
                     do ficha e registro da conexão do casal quando aceito.
"""

from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.convite import Convite
from app.repositories import convite as repo_convite
from app.repositories import usuario as repo_usuario
from app.services.auth import gerar_hash_senha


def criar_convite(db: Session, nome: str, email: str, remetente_id: UUID) -> Convite:
    convite = repo_convite.criar_convite(db, nome=nome, email=email, remetente_id=remetente_id)
    return convite


def buscar_convite(db: Session, token: UUID) -> Convite:
    convite = repo_convite.buscar_por_token(db, token)
    if not convite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Convite não encontrado.")
    if convite.usado_em is not None:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Este convite já foi utilizado.")
    return convite


def aceitar_convite(db: Session, token: UUID, senha: str) -> None:
    convite = buscar_convite(db, token)

    if repo_usuario.buscar_por_email(db, convite.email_convidado):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe uma conta com este e-mail.",
        )

    # Bloqueia se o remetente já tem conexão
    if repo_convite.buscar_conexao(db, convite.remetente_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="O remetente já está vinculado a um parceiro.",
        )

    novo_usuario = repo_usuario.criar(
        db,
        nome=convite.nome_convidado,
        email=convite.email_convidado,
        senha_hash=gerar_hash_senha(senha),
    )

    repo_convite.criar_conexao(db, uid1=convite.remetente_id, uid2=novo_usuario.id)
    repo_convite.marcar_usado(db, convite)
