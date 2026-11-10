"""
Repositório de acesso a dados para a entidade Usuário.
Centraliza todas as operações de banco relacionadas à tabela `users`.
"""

from sqlalchemy.orm import Session

from app.models.usuario import Usuario


def buscar_por_email(db: Session, email: str) -> Usuario | None:
    """Retorna o usuário com o e-mail informado, ou None se não existir."""
    return db.query(Usuario).filter(Usuario.email == email).first()


def criar(db: Session, nome: str, email: str, senha_hash: str) -> Usuario:
    """Persiste um novo usuário no banco e retorna a instância criada."""
    novo_usuario = Usuario(nome=nome, email=email, senha_hash=senha_hash)
    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)
    return novo_usuario
