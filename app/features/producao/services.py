"""Regras de negócio de produção, orquestrando o repository."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from flask_sqlalchemy.pagination import Pagination

from app.features.estoque.models import ItemLote, Lote
from app.features.estoque.repository import EstoqueRepository
from app.utils.enums import GrupoPadrao, StatusItem, StatusSolicitacao, TipoMovimentacao
from app.utils.errors import Conflito, RegistroNaoEncontrado
from app.utils.paginacao import PaginacaoQuery

from . import models
from .repository import ProducaoRepository


@dataclass
class UsoPlanejado:
    lote: Lote
    quantidade: float
    itens: list[tuple[ItemLote, float]] | None


class ProducaoService:
    def __init__(self, repository: ProducaoRepository) -> None:
        self.repository = repository

    def listar_solicitacoes(
        self, paginacao: PaginacaoQuery, praca_id: int | None = None
    ) -> Pagination:
        return self.repository.listar_solicitacoes(paginacao, praca_id)

    def criar_solicitacao(
        self,
        ficha_id: int,
        usuario_id: int,
        quantidade_planejada: float | None = None,
        localizacao_destino_id: int | None = None,
        praca_id: int | None = None,
    ) -> models.SolicitacaoProducao:
        with self.repository.transacao():
            ficha = self.repository.obter_ficha(ficha_id)
            if ficha is None:
                raise RegistroNaoEncontrado("ficha técnica não encontrada")
            quantidade = quantidade_planejada or float(ficha.rendimento)
            localizacao = (
                self.repository.obter_localizacao(localizacao_destino_id)
                if localizacao_destino_id is not None
                else self.repository.primeira_localizacao_compativel(
                    ficha.produto.conservacao
                )
            )
            if localizacao is None:
                raise ValueError("localização de destino não encontrada")
            if localizacao.tipo != ficha.produto.conservacao:
                raise ValueError(
                    "localização de destino incompatível com a conservação do produto final"
                )
            if praca_id is not None:
                self._validar_praca_ativa(praca_id)
            return self.repository.criar_solicitacao(
                ficha, usuario_id, quantidade, localizacao.id, praca_id
            )

    def _validar_praca_ativa(self, praca_id: int) -> None:
        # O bloqueio evita novas atribuições durante uma desativação concorrente.
        praca = self.repository.obter_praca(praca_id, para_atualizacao=True)
        if praca is None:
            raise ValueError("praça não encontrada")
        if not praca.ativo:
            raise ValueError("não é possível atribuir uma praça inativa")
        if not any(
            usuario.ativo and any(
                grupo.nome == GrupoPadrao.COZINHA.value for grupo in usuario.grupos
            )
            for usuario in praca.cozinheiros
        ):
            raise ValueError("praça não possui cozinheiros ativos do grupo Cozinha")

    def alterar_praca(
        self, solicitacao_id: int, praca_id: int | None
    ) -> models.SolicitacaoProducao:
        with self.repository.transacao():
            solicitacao = self.repository.obter_solicitacao(
                solicitacao_id, para_atualizacao=True
            )
            if solicitacao is None:
                raise RegistroNaoEncontrado("solicitação não encontrada")
            if solicitacao.status not in (
                StatusSolicitacao.ABERTA,
                StatusSolicitacao.EM_SEPARACAO,
            ):
                raise Conflito("não é possível alterar a praça após o início da produção")
            if praca_id is not None:
                self._validar_praca_ativa(praca_id)
            # Desatribuir é permitido apenas antes do início da produção.
            solicitacao.praca_id = praca_id
            return solicitacao

    def atualizar_status(
        self, sp_id: int, status: StatusSolicitacao, usuario_id: int
    ) -> models.SolicitacaoProducao:
        if status == StatusSolicitacao.CONCLUIDA:
            return self._concluir(sp_id, usuario_id)
        # Compartilha o lock da solicitação com a troca de praça.
        with self.repository.transacao():
            solicitacao = self.repository.obter_solicitacao(
                sp_id, para_atualizacao=True
            )
            if solicitacao is None:
                raise RegistroNaoEncontrado("solicitação não encontrada")
            if status not in StatusSolicitacao.proximos(solicitacao.status):
                raise ValueError(
                    f"não é possível alterar de {solicitacao.status} para {status}"
                )
            self.repository.marcar_status(solicitacao, status)
            return solicitacao

    def _concluir(
        self, solicitacao_id: int, usuario_id: int
    ) -> models.SolicitacaoProducao:
        estoque = EstoqueRepository()
        with self.repository.transacao():
            solicitacao = self.repository.obter_solicitacao(
                solicitacao_id, para_atualizacao=True
            )
            if solicitacao is None:
                raise RegistroNaoEncontrado("solicitação não encontrada")
            if solicitacao.status != StatusSolicitacao.EM_PRODUCAO:
                raise ValueError(
                    f"não é possível concluir uma produção em {solicitacao.status}"
                )
            if estoque.obter_usuario_ativo(usuario_id) is None:
                raise ValueError("usuário não encontrado ou inativo")

            componentes = self.repository.componentes_da_solicitacao(
                solicitacao.id
            )
            planos = [
                (componente, self._planejar_consumo(estoque, componente))
                for componente in componentes
            ]
            custo_total = 0.0
            custo_completo = True
            for componente, usos in planos:
                for uso in usos:
                    movimento = estoque.inserir_movimentacao(
                        tipo=TipoMovimentacao.CONSUMO_PRODUCAO,
                        lote_origem=uso.lote,
                        lote_destino=None,
                        quantidade=uso.quantidade,
                        quantidade_destino=None,
                        motivo="Consumo da produção",
                        usuario_id=usuario_id,
                        observacao=f"Solicitação de produção #{solicitacao.id}",
                    )
                    movimento.solicitacao_producao_id = solicitacao.id
                    movimento.sp_componente_id = componente.id
                    if uso.itens is not None:
                        self._baixar_itens(estoque, movimento.id, uso.itens)
                        self._recalcular_lote_com_itens(estoque, uso.lote)
                    if uso.lote.custo_unitario is None:
                        custo_completo = False
                    else:
                        custo_total += uso.quantidade * float(uso.lote.custo_unitario)

            ficha = self.repository.obter_ficha(solicitacao.ficha_tecnica_id)
            produto_final = ficha.produto
            hoje = date.today()
            if produto_final.validade_obrigatoria and not produto_final.validade_padrao_dias:
                raise ValueError(
                    "produto final exige validade; configure a validade padrão antes de concluir"
                )
            validade = (
                (hoje + timedelta(days=produto_final.validade_padrao_dias)).isoformat()
                if produto_final.validade_padrao_dias is not None
                else None
            )
            quantidade_final = float(solicitacao.quantidade_planejada)
            lote_final = estoque.inserir_lote(
                produto_id=ficha.produto_id,
                localizacao_id=solicitacao.localizacao_destino_id,
                data_producao=hoje.isoformat(),
                data_validade=validade,
                custo_unitario=(
                    custo_total / quantidade_final if custo_completo else None
                ),
            )
            producao = estoque.inserir_movimentacao(
                tipo=TipoMovimentacao.PRODUCAO,
                lote_origem=lote_final,
                lote_destino=None,
                quantidade=quantidade_final,
                quantidade_destino=None,
                motivo=None,
                usuario_id=usuario_id,
                observacao=f"Produção concluída na solicitação #{solicitacao.id}",
            )
            producao.solicitacao_producao_id = solicitacao.id
            self.repository.marcar_status(solicitacao, StatusSolicitacao.CONCLUIDA)
            return solicitacao

    def _planejar_consumo(self, estoque: EstoqueRepository, componente):
        restante = float(componente.quantidade_prevista)
        usos: list[UsoPlanejado] = []
        for lote_row in estoque.lotes_fefo_disponiveis(componente.produto_id):
            lote = estoque.obter_lote(lote_row["id"], para_atualizacao=True)
            if estoque.lote_tem_itens(lote.id):
                itens = estoque.itens_fefo(lote.id)
                disponivel = sum(float(item.saldo) for item in itens)
                usar = min(restante, disponivel)
                usos_itens: list[tuple[ItemLote, float]] = []
                falta_no_lote = usar
                for item in itens:
                    if falta_no_lote <= 0:
                        break
                    quantidade = min(float(item.saldo), falta_no_lote)
                    usos_itens.append((item, quantidade))
                    falta_no_lote = round(falta_no_lote - quantidade, 6)
            else:
                usar = min(restante, float(lote.quantidade))
                usos_itens = None
            if usar > 0:
                usos.append(UsoPlanejado(lote, usar, usos_itens))
                restante = round(restante - usar, 6)
            if restante <= 0:
                break
        if restante > 0:
            produto = estoque.obter_produto(componente.produto_id)
            raise ValueError(
                f"estoque insuficiente de {produto.nome}: faltam {restante:g} "
                f"{produto.unidade_medida}"
            )
        return usos

    def _baixar_itens(
        self,
        estoque: EstoqueRepository,
        movimentacao_id: int,
        itens: list[tuple[ItemLote, float]],
    ) -> None:
        agora = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        for item, quantidade in itens:
            estoque.vincular_item(movimentacao_id, item.id, quantidade)
            item.saldo = round(float(item.saldo) - quantidade, 6)
            if item.saldo <= 0:
                item.saldo = 0
                item.status = StatusItem.CONSUMIDA
            else:
                item.status = StatusItem.EM_USO
                item.aberto_em = item.aberto_em or agora

    def _recalcular_lote_com_itens(
        self, estoque: EstoqueRepository, lote: Lote
    ) -> None:
        itens = estoque.itens_ativos(lote.id)
        lote.quantidade = round(sum(float(item.saldo) for item in itens), 6)
        validades = [item.data_validade for item in itens if item.data_validade]
        if validades:
            lote.data_validade = min(validades)

    def obter_detalhe(self, sp_id: int) -> models.SolicitacaoDetalhe:
        solicitacao = self.repository.obter_solicitacao(sp_id)
        if solicitacao is None:
            raise RegistroNaoEncontrado("solicitação não encontrada")

        return models.SolicitacaoDetalhe(
            solicitacao=solicitacao,
            componentes=[
                models.ComponenteSolicitacao.from_row(r)
                for r in self.repository.listar_componentes(sp_id)
            ],
            fases=[
                models.FaseSolicitacao.from_row(r)
                for r in self.repository.listar_fases(sp_id)
            ],
            lotes_produzidos=[
                models.LoteProduzido.from_row(r)
                for r in self.repository.listar_lotes_produzidos(sp_id)
            ],
        )
