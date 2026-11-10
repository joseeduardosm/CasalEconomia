"""
Ponto de entrada da API CasalEconomia.
Instancia o FastAPI, configura CORS e registra os routers da aplicação.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import configuracoes
from app.routers.auth import roteador as roteador_auth

# Instância principal da aplicação — nome obrigatório: `aplicacao`
aplicacao = FastAPI(
    title="CasalEconomia API",
    description="API de controle financeiro para casais.",
    version="0.1.0",
)

# Lê as origens permitidas do .env e converte para lista
origens_permitidas = [origem.strip() for origem in configuracoes.CORS_ORIGINS.split(",")]

# Configuração de CORS para permitir o front-end Angular acessar a API
aplicacao.add_middleware(
    CORSMiddleware,
    allow_origins=origens_permitidas,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


aplicacao.include_router(roteador_auth)


@aplicacao.get("/saude", tags=["saúde"])
def verificar_saude():
    """Rota de verificação de saúde da API — sem autenticação."""
    return {"status": "ok"}
