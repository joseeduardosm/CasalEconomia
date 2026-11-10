"""
Repositório de usuários do CasalEconomia.
Centraliza todas as operações de banco relacionadas à tabela `users`.

pq existe: Padrão Repositório isola o acesso ao banco do restante da lógica —
           as camadas acima (serviços, roteadores) não conhecem SQL diretamente.
para que no projeto: busca usuário por e-mail (usado no login) e cria novos
                     registros na tabela `users` (usado no cadastro).
"""

from uuid import UUID
from sqlalchemy.orm import Session

from app.models.usuario import Usuario


def buscar_por_email(db: Session, email: str | None, usuario_id: UUID | None = None) -> Usuario | None:
    if usuario_id is not None:
        return db.query(Usuario).filter(Usuario.id == usuario_id).first()
    return db.query(Usuario).filter(Usuario.email == email).first()


def criar(db: Session, nome: str, email: str, senha_hash: str) -> Usuario:
    """Persiste um novo usuário no banco e retorna a instância criada."""
    novo_usuario = Usuario(nome=nome, email=email, senha_hash=senha_hash)
    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)
    return novo_usuario
