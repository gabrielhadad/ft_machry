"""Regras de negócio de produção, orquestrando o repository."""
from __future__ import annotations

from decimal import Decimal

from app.features.estoque.repository import EstoqueRepository
from app.features.estoque.services import EstoqueService
from app.utils.errors import RegistroNaoEncontrado

from . import models, schemas
from .repository import ProducaoRepository


class ProducaoService:
    def __init__(self, repository: ProducaoRepository) -> None:
        self.repository = repository

    def listar_solicitacoes(self) -> list[models.SolicitacaoProducao]:
        return self.repository.listar_solicitacoes()

    def criar_solicitacao(
        self, dados: schemas.SolicitacaoCreate, usuario_id: int
    ) -> models.SolicitacaoProducao:
        ficha = self.repository.obter_ficha(dados.ficha_tecnica_id)
        if ficha is None:
            raise RegistroNaoEncontrado("ficha técnica não encontrada")

        quantidade_planejada = Decimal(
            str(
                dados.quantidade_planejada
                if dados.quantidade_planejada is not None
                else ficha.rendimento
            )
        )
        if quantidade_planejada <= 0:
            raise ValueError("quantidade planejada deve ser maior que zero")

        if dados.responsavel_id is not None:
            responsavel = self.repository.obter_usuario_ativo(dados.responsavel_id)
            if responsavel is None:
                raise RegistroNaoEncontrado("responsável não encontrado ou inativo")

        return self.repository.criar_solicitacao(
            ficha=ficha,
            usuario_id=usuario_id,
            quantidade_planejada=quantidade_planejada,
            prioridade=dados.prioridade,
            previsto_para=dados.previsto_para,
            responsavel_id=dados.responsavel_id,
            observacao=dados.observacao,
        )

    def atualizar_status(
        self, sp_id: int, status: str, usuario_id: int,
        localizacao_destino_id: int | None = None,
    ) -> models.SolicitacaoProducao:
        if status == "CONCLUIDA":
            return self._concluir_com_consumo(
                sp_id, usuario_id, localizacao_destino_id
            )

        solicitacao = self.repository.obter_solicitacao(sp_id)
        if solicitacao is None:
            raise RegistroNaoEncontrado("solicitação não encontrada")
        self._validar_transicao(solicitacao, status)
        return self.repository.atualizar_status(solicitacao, status)

    def _concluir_com_consumo(
        self, sp_id: int, usuario_id: int, localizacao_destino_id: int | None
    ) -> models.SolicitacaoProducao:
        # O lock da solicitação serializa tentativas concorrentes de conclusão.
        # A mesma sessão SQLAlchemy é compartilhada por produção e estoque.
        with self.repository.transacao():
            solicitacao = self.repository.obter_solicitacao(
                sp_id, para_atualizacao=True
            )
            if solicitacao is None:
                raise RegistroNaoEncontrado("solicitação não encontrada")
            self._validar_transicao(solicitacao, "CONCLUIDA")

            componentes = self.repository.listar_componentes_modelo(sp_id)
            estoque = EstoqueService(EstoqueRepository())
            estoque.consumir_componentes_producao(
                solicitacao_id=sp_id,
                componentes=componentes,
                usuario_id=usuario_id,
            )

            # Compatibilidade: produções antigas que não registraram quantidade real
            # assumem o planejado. Quando a cozinha informou o realizado, ele vence.
            if solicitacao.quantidade_produzida is None:
                solicitacao.quantidade_produzida = solicitacao.quantidade_planejada

            ficha = self.repository.obter_ficha(solicitacao.ficha_tecnica_id)
            estoque.registrar_produto_final(
                solicitacao_id=sp_id,
                produto_id=ficha.produto_id,
                quantidade=Decimal(str(solicitacao.quantidade_produzida)),
                usuario_id=usuario_id,
                localizacao_destino_id=localizacao_destino_id,
            )
            self.repository.definir_status(solicitacao, "CONCLUIDA")

        return solicitacao

    @staticmethod
    def _validar_transicao(solicitacao: models.SolicitacaoProducao, status: str) -> None:
        permitidos = {
            "ABERTA": {"EM_SEPARACAO", "EM_PRODUCAO", "CANCELADA"},
            "EM_SEPARACAO": {"EM_PRODUCAO", "CANCELADA"},
            "EM_PRODUCAO": {"CONCLUIDA", "CANCELADA"},
            "CONCLUIDA": set(),
            "CANCELADA": set(),
        }
        if status not in permitidos[solicitacao.status]:
            raise ValueError(f"não é possível alterar de {solicitacao.status} para {status}")

    def registrar_execucao(
        self, sp_id: int, dados: schemas.ExecucaoProducaoUpdate, usuario_id: int
    ) -> models.SolicitacaoDetalhe:
        solicitacao = self.repository.obter_solicitacao(sp_id)
        if solicitacao is None:
            raise RegistroNaoEncontrado("solicitação não encontrada")
        if solicitacao.status != "EM_PRODUCAO":
            raise ValueError("a execução só pode ser registrada com a produção EM_PRODUCAO")

        fases_por_id = {
            fase.id: fase for fase in self.repository.listar_fases_modelo(sp_id)
        }
        atualizacoes: list[tuple[models.SpFase, schemas.FaseExecucaoUpdate]] = []
        for fase_dados in dados.fases:
            fase = fases_por_id.get(fase_dados.sp_fase_id)
            if fase is None:
                raise ValueError(
                    f"a fase {fase_dados.sp_fase_id} não pertence à solicitação"
                )
            atualizacoes.append((fase, fase_dados))

        componentes_por_id = {
            componente.id: componente
            for componente in self.repository.listar_componentes_modelo(sp_id)
        }
        perdas: list[tuple[models.SpComponente, schemas.PerdaProducaoInput]] = []
        for perda in dados.perdas:
            componente = componentes_por_id.get(perda.sp_componente_id)
            if componente is None:
                raise ValueError(
                    f"o componente {perda.sp_componente_id} não pertence à solicitação"
                )
            perdas.append((componente, perda))

        quantidade_produzida = (
            Decimal(str(dados.quantidade_produzida))
            if dados.quantidade_produzida is not None
            else None
        )
        with self.repository.transacao():
            self.repository.salvar_execucao(
                solicitacao,
                quantidade_produzida=quantidade_produzida,
                observacao_execucao=dados.observacao_execucao,
                fases=atualizacoes,
            )
            if perdas:
                EstoqueService(EstoqueRepository()).registrar_perdas_producao(
                    solicitacao_id=sp_id,
                    perdas=perdas,
                    usuario_id=usuario_id,
                )
        return self.obter_detalhe(sp_id)

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
