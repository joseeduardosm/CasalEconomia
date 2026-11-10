"""
Roteador de autenticação do CasalEconomia.
Expõe as rotas de registro e login de usuários, retornando fichas JWT.

pq existe: APIRouter do FastAPI agrupa rotas relacionadas sob um prefixo comum,
           mantendo o código organizado por domínio.
para que no projeto: centraliza /auth/registrar e /auth/entrar, gerenciando
                     criação de conta e emissão de fichas de acesso.
"""

import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.database import obter_sessao
from app.repositories import usuario as repo_usuario
from app.schemas.auth import EntradaCadastro, EntradaLogin, RespostaToken
from app.services import auth as servico_auth

roteador = APIRouter(prefix="/auth", tags=["autenticação"])


def _extrair_id_usuario(authorization: str = Header(...)) -> uuid.UUID:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Ficha ausente ou mal formatada.")
    token = authorization.removeprefix("Bearer ")
    return servico_auth.verificar_token(token)


def obter_usuario_atual(
    usuario_id: uuid.UUID = Depends(_extrair_id_usuario),
    db: Session = Depends(obter_sessao),
):
    """Dependência que retorna o objeto Usuario autenticado."""
    usuario = repo_usuario.buscar_por_email(db, None, usuario_id=usuario_id)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário não encontrado.")
    return usuario


@roteador.post("/registrar", status_code=status.HTTP_201_CREATED, response_model=RespostaToken)
def registrar(entrada: EntradaCadastro, db: Session = Depends(obter_sessao)):
    """Registra um novo usuário e retorna o token JWT."""
    if repo_usuario.buscar_por_email(db, entrada.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="E-mail já cadastrado.")

    senha_hash = servico_auth.gerar_hash_senha(entrada.senha)
    novo_usuario = repo_usuario.criar(db, nome=entrada.nome, email=entrada.email, senha_hash=senha_hash)
    token = servico_auth.gerar_token(novo_usuario.id)
    return RespostaToken(access_token=token)


@roteador.post("/entrar", response_model=RespostaToken)
def entrar(entrada: EntradaLogin, db: Session = Depends(obter_sessao)):
    """Autentica um usuário existente e retorna o token JWT."""
    usuario = repo_usuario.buscar_por_email(db, entrada.email)
    if not usuario or not servico_auth.verificar_senha(entrada.senha, usuario.senha_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="E-mail ou senha incorretos.")

    token = servico_auth.gerar_token(usuario.id)
    return RespostaToken(access_token=token)
