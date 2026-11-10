"""
Regras de negócio para lançamentos financeiros — incluindo parcelamento,
compartilhamento com parceiro e importação XLSX.

pq existe: Service Layer concentra a lógica de negócio fora das rotas HTTP,
           tornando o código testável e reutilizável.
para que no projeto: orquestra criação de lançamentos avulsos e parcelados,
                     distribuição de centavos, compartilhamento e importação.
"""

import io
from decimal import Decimal, ROUND_DOWN
from datetime import date
from uuid import UUID
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories import lancamento as repo
from app.models.serie_parcelamento import SerieParcelamento
from app.models.lancamento import LancamentoParceiro


FORMAS_INVALIDAS_RECEITA = {"boleto", "cartao_debito", "cartao_credito"}


def calcular_status_receita(lancamento) -> str:
    hoje = date.today()
    pago = lancamento.liquidado or False
    recebido = lancamento.valor_recebido
    venc = lancamento.data_vencimento

    if pago and recebido is not None and recebido < lancamento.valor:
        return "parcialmente_recebido"
    if pago:
        return "recebido"
    if venc and venc > hoje:
        return "previsto"
    return "a_receber"


def enriquecer_lancamento(lanc, include_status: bool = True):
    """Adiciona status_receita ao objeto ORM antes de serializar."""
    if lanc.tipo == "receita" and include_status:
        lanc.status_receita = calcular_status_receita(lanc)
    else:
        lanc.status_receita = None
    return lanc


def _proximo_periodo(periodo: str, delta: int) -> str:
    ano, mes = int(periodo[:4]), int(periodo[5:7])
    mes += delta
    ano += (mes - 1) // 12
    mes = ((mes - 1) % 12) + 1
    return f"{ano:04d}-{mes:02d}"


def _distribuir_centavos(valor_total: Decimal, n_parcelas: int) -> list[Decimal]:
    centavo = Decimal("0.01")
    base = (valor_total / n_parcelas).quantize(centavo, rounding=ROUND_DOWN)
    residuo = valor_total - base * n_parcelas
    n_residuo = int(residuo / centavo)
    parcelas = []
    for i in range(n_parcelas):
        v = base + centavo if i < n_residuo else base
        parcelas.append(v)
    return parcelas


def _verificar_parceiro_por_email(db: Session, email: str, usuario_id: UUID) -> UUID:
    from app.models.convite import ConexaoCasal
    from app.models.usuario import Usuario
    conexao = (
        db.query(ConexaoCasal)
        .filter(
            (ConexaoCasal.usuario_id_1 == usuario_id)
            | (ConexaoCasal.usuario_id_2 == usuario_id)
        )
        .first()
    )
    if not conexao:
        raise HTTPException(status_code=400, detail="Você não tem parceiro conectado.")
    parceiro_id = conexao.usuario_id_2 if conexao.usuario_id_1 == usuario_id else conexao.usuario_id_1
    parceiro = db.query(Usuario).filter(Usuario.id == parceiro_id).first()
    if not parceiro or parceiro.email != email:
        raise HTTPException(status_code=400, detail="O e-mail não pertence ao seu parceiro conectado.")
    return parceiro_id


def _criar_registro_compartilhado(db: Session, lancamento, parceiro_id: UUID) -> None:
    reg = LancamentoParceiro(
        lancamento_id=lancamento.id,
        usuario_dono_id=lancamento.usuario_id,
        usuario_parceiro_id=parceiro_id,
        snapshot_descricao=lancamento.descricao,
        snapshot_valor=lancamento.valor_compartilhado or lancamento.valor,
        snapshot_data=lancamento.data_lancamento,
        snapshot_tipo=lancamento.tipo,
    )
    db.add(reg)
    db.commit()


def criar_lancamento(
    db: Session,
    descricao: str,
    valor: Decimal,
    data_lancamento: date,
    tipo: str,
    usuario_id: UUID,
    cartao_id: Optional[UUID] = None,
    forma_pagamento: Optional[str] = None,
    liquidado: Optional[bool] = None,
    data_vencimento: Optional[date] = None,
    nota: Optional[str] = None,
    categoria: Optional[str] = None,
    valor_aproximado: bool = False,
    parcelado: bool = False,
    total_parcelas: Optional[int] = None,
    parcela_inicio: int = 1,
    periodo_fatura_explicito: Optional[str] = None,
    email_compartilhado: Optional[str] = None,
    percentual_compartilhado: Optional[Decimal] = None,
    fonte: Optional[str] = None,
    valor_recebido: Optional[Decimal] = None,
):
    if tipo not in ("receita", "despesa"):
        raise HTTPException(status_code=400, detail="Tipo deve ser 'receita' ou 'despesa'.")

    if tipo == "receita":
        if parcelado or total_parcelas:
            raise HTTPException(status_code=400, detail="Parcelamento não é suportado para receitas.")
        if cartao_id:
            raise HTTPException(status_code=400, detail="Cartão de crédito não é aceito para receitas.")
        if forma_pagamento and forma_pagamento in FORMAS_INVALIDAS_RECEITA:
            raise HTTPException(status_code=400, detail=f"Forma de pagamento '{forma_pagamento}' não permitida para receitas.")
        if liquidado is None:
            liquidado = False

    parceiro_id = None
    if email_compartilhado:
        parceiro_id = _verificar_parceiro_por_email(db, email_compartilhado, usuario_id)

    if forma_pagamento == "cartao_credito":
        liquidado = None

    # Determina período da fatura base
    if cartao_id:
        from app.services.cartao import calcular_periodo_fatura
        periodo_base = periodo_fatura_explicito or calcular_periodo_fatura(db, cartao_id, data_lancamento)
    else:
        hoje = date.today()
        periodo_base = f"{hoje.year:04d}-{hoje.month:02d}"

    if not parcelado or not total_parcelas or total_parcelas < 2:
        # Lançamento avulso
        valor_comp = None
        if email_compartilhado and percentual_compartilhado:
            valor_comp = (valor * percentual_compartilhado / 100).quantize(Decimal("0.01"), rounding=ROUND_DOWN)

        lanc = repo.criar_lancamento(
            db, descricao=descricao, valor=valor,
            data_lancamento=data_lancamento, tipo=tipo, usuario_id=usuario_id,
            cartao_id=cartao_id, periodo_fatura=periodo_base if cartao_id else None,
            forma_pagamento=forma_pagamento, liquidado=liquidado,
            data_vencimento=data_vencimento, nota=nota, categoria=categoria,
            valor_aproximado=valor_aproximado,
            email_compartilhado=email_compartilhado,
            percentual_compartilhado=percentual_compartilhado,
            valor_compartilhado=valor_comp,
            fonte=fonte, valor_recebido=valor_recebido,
        )
        if parceiro_id:
            _criar_registro_compartilhado(db, lanc, parceiro_id)
        return enriquecer_lancamento(lanc)

    # Parcelamento
    if parcela_inicio < 1 or parcela_inicio > total_parcelas:
        raise HTTPException(status_code=400, detail="parcela_inicio inválida.")

    serie = SerieParcelamento(
        usuario_id=usuario_id,
        total_parcelas=total_parcelas,
        parcela_inicio=parcela_inicio,
        valor_total=valor * total_parcelas,
    )
    db.add(serie)
    db.commit()
    db.refresh(serie)

    n_criar = total_parcelas - parcela_inicio + 1
    valores = _distribuir_centavos(valor * n_criar, n_criar)
    primeira = None

    for i, v in enumerate(valores):
        num_parcela = parcela_inicio + i
        periodo = _proximo_periodo(periodo_base, i)
        valor_comp = None
        if email_compartilhado and percentual_compartilhado:
            valor_comp = (v * percentual_compartilhado / 100).quantize(Decimal("0.01"), rounding=ROUND_DOWN)

        lanc = repo.criar_lancamento(
            db, descricao=descricao, valor=v,
            data_lancamento=data_lancamento, tipo=tipo, usuario_id=usuario_id,
            cartao_id=cartao_id, periodo_fatura=periodo if cartao_id else None,
            forma_pagamento=forma_pagamento, liquidado=liquidado,
            nota=nota, categoria=categoria,
            serie_id=serie.id, parcela_atual=num_parcela,
            email_compartilhado=email_compartilhado,
            percentual_compartilhado=percentual_compartilhado,
            valor_compartilhado=valor_comp,
        )
        if parceiro_id:
            _criar_registro_compartilhado(db, lanc, parceiro_id)
        if primeira is None:
            primeira = lanc
    return enriquecer_lancamento(primeira)


def aceitar_pendente(db: Session, registro_id: UUID, versao_esperada: int, usuario_id: UUID):
    reg = repo.buscar_pendente_por_id(db, registro_id, usuario_id)
    if not reg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro não encontrado.")
    if reg.status != "pendente":
        raise HTTPException(status_code=400, detail="Este registro já foi processado.")
    if reg.versao_fonte != versao_esperada:
        raise HTTPException(status_code=409, detail="Conflito de versão. Recarregue e tente novamente.")

    novo = repo.criar_lancamento(
        db,
        descricao=reg.snapshot_descricao,
        valor=reg.snapshot_valor,
        data_lancamento=reg.snapshot_data,
        tipo=reg.snapshot_tipo,
        usuario_id=usuario_id,
        origem="compartilhado",
        lancamento_origem_id=reg.lancamento_id,
    )
    reg.status = "aceito"
    reg.lancamento_importado_id = novo.id
    db.commit()
    return {"mensagem": "Lançamento aceito com sucesso."}


def ignorar_pendente(db: Session, registro_id: UUID, versao_esperada: int, usuario_id: UUID):
    reg = repo.buscar_pendente_por_id(db, registro_id, usuario_id)
    if not reg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro não encontrado.")
    if reg.status != "pendente":
        raise HTTPException(status_code=400, detail="Este registro já foi processado.")
    if reg.versao_fonte != versao_esperada:
        raise HTTPException(status_code=409, detail="Conflito de versão. Recarregue e tente novamente.")
    reg.status = "ignorado"
    db.commit()
    return {"mensagem": "Lançamento ignorado."}


def gerar_modelo_xlsx() -> bytes:
    """Gera o arquivo XLSX modelo para importação de lançamentos."""
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Lançamentos"
    cabecalho = ["Descrição", "Data (AAAA-MM-DD)", "Valor por Parcela",
                 "Parcela Atual", "Total de Parcelas", "Categoria",
                 "Email Compartilhado", "% Compartilhamento"]
    ws.append(cabecalho)
    ws.append(["Almoço com cliente", "2026-11-10", "85.00", "", "", "Alimentação", "", ""])
    ws.append(["TV 4K", "2026-11-10", "300.00", "1", "4", "Eletrônicos", "", ""])
    ws.append(["Supermercado", "2026-11-10", "250.00", "", "", "Alimentação", "parceiro@email.com", "50"])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def validar_importacao(conteudo: bytes, usuario_id: UUID, db: Session) -> dict:
    """Valida planilha XLSX linha a linha; não persiste nada."""
    from openpyxl import load_workbook
    from datetime import datetime

    wb = load_workbook(filename=io.BytesIO(conteudo), read_only=True, data_only=True)
    ws = wb.active
    linhas_validas = []
    linhas_com_erro = []
    hoje = date.today()

    for idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        if not any(row):
            continue
        descricao, data_raw, valor_raw, parcela_atual_raw, total_parcelas_raw, categoria, email_comp, pct_comp = (
            (row[i] if i < len(row) else None) for i in range(8)
        )
        problemas = []

        if not descricao or not str(descricao).strip():
            problemas.append("Descrição obrigatória")
        elif len(str(descricao)) > 200:
            problemas.append("Descrição muito longa (máx 200 chars)")

        d_lancamento = None
        if not data_raw:
            problemas.append("Data obrigatória")
        else:
            try:
                d_lancamento = date.fromisoformat(str(data_raw).strip()[:10])
                if d_lancamento > hoje.replace(year=hoje.year + 1):
                    problemas.append("Data não pode ser futura além de 1 ano")
            except ValueError:
                problemas.append("Data inválida (use AAAA-MM-DD)")

        valor = None
        if not valor_raw:
            problemas.append("Valor obrigatório")
        else:
            try:
                valor = Decimal(str(valor_raw))
                if valor <= 0 or valor > Decimal("999999.99"):
                    problemas.append("Valor fora do intervalo permitido")
            except Exception:
                problemas.append("Valor inválido")

        parcela_atual = int(parcela_atual_raw) if parcela_atual_raw else None
        total_parcelas = int(total_parcelas_raw) if total_parcelas_raw else None
        if parcela_atual and not total_parcelas:
            problemas.append("Total de Parcelas obrigatório quando Parcela Atual informada")
        if total_parcelas and total_parcelas < 2:
            problemas.append("Total de Parcelas deve ser >= 2")
        if parcela_atual and total_parcelas and parcela_atual > total_parcelas:
            problemas.append("Parcela Atual não pode ser maior que Total de Parcelas")

        if email_comp:
            try:
                _verificar_parceiro_por_email(db, str(email_comp).strip(), usuario_id)
            except HTTPException as e:
                problemas.append(e.detail)
            if not pct_comp:
                problemas.append("% Compartilhamento obrigatório quando Email Compartilhado informado")

        if problemas:
            linhas_com_erro.append({"numero_linha": idx, "problema": "; ".join(problemas)})
        else:
            linhas_validas.append({
                "descricao": str(descricao).strip(),
                "data_lancamento": str(d_lancamento),
                "valor": str(valor),
                "parcela_atual": parcela_atual,
                "total_parcelas": total_parcelas,
                "categoria": str(categoria).strip() if categoria else None,
                "email_compartilhado": str(email_comp).strip() if email_comp else None,
                "percentual_compartilhado": str(pct_comp) if pct_comp else None,
            })
    return {"linhas_validas": linhas_validas, "linhas_com_erro": linhas_com_erro}


def confirmar_importacao(linhas: list[dict], usuario_id: UUID, db: Session) -> int:
    """Persiste as linhas validadas. Retorna a quantidade criada."""
    criados = 0
    for linha in linhas:
        pct = Decimal(linha["percentual_compartilhado"]) if linha.get("percentual_compartilhado") else None
        criar_lancamento(
            db,
            descricao=linha["descricao"],
            valor=Decimal(linha["valor"]),
            data_lancamento=date.fromisoformat(linha["data_lancamento"]),
            tipo="despesa",
            usuario_id=usuario_id,
            categoria=linha.get("categoria"),
            parcelado=bool(linha.get("total_parcelas")),
            total_parcelas=linha.get("total_parcelas"),
            parcela_inicio=linha.get("parcela_atual") or 1,
            email_compartilhado=linha.get("email_compartilhado"),
            percentual_compartilhado=pct,
        )
        criados += 1
    return criados
