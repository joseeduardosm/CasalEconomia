"""
Repositório de usuários do CasalEconomia.
Centraliza todas as operações de banco relacionadas à tabela `users`.

pq existe: Padrão Repositório isola o acesso ao banco do restante da lógica —
           as camadas acima (serviços, roteadores) não conhecem SQL diretamente.
para que no projeto: busca usuário por e-mail (usado no login) e cria novos
                     registros na tabela `users` (usado no cadastro).
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
