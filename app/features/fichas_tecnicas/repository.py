from decimal import Decimal

from sqlalchemy.orm import selectinload

from app.features.produtos.models import Produto
from app.utils.dinheiro import ZERO, custo_unitario, para_decimal
from app.utils.paginacao import PaginacaoQuery, paginar
from app.utils.interfaces.repository import RepositorioBase
from db.database_config import db

from .models import (
    FaseProducao,
    FichaTecnica,
    FichaTecnicaComponente,
    FichaTecnicaFase,
)


class FichaTecnicaRepository(RepositorioBase):
    @staticmethod
    def _carregamento_completo():
        return (
            selectinload(FichaTecnica.produto),
            selectinload(FichaTecnica.fases).selectinload(FichaTecnicaFase.fase),
            selectinload(FichaTecnica.componentes).selectinload(
                FichaTecnicaComponente.produto
            ),
            selectinload(FichaTecnica.componentes).selectinload(
                FichaTecnicaComponente.fase
            ),
        )

    def _consulta_completa(self):
        return db.session.query(FichaTecnica).options(*self._carregamento_completo())

    def listar(self, paginacao: PaginacaoQuery):
        return paginar(
            db.select(FichaTecnica)
            .options(*self._carregamento_completo())
            .join(FichaTecnica.produto)
            .order_by(Produto.nome, FichaTecnica.id),
            paginacao,
        )

    def obter(self, ficha_id: int) -> FichaTecnica | None:
        return self._consulta_completa().filter(FichaTecnica.id == ficha_id).first()

    def obter_produto(self, produto_id: int) -> Produto | None:
        return db.session.get(Produto, produto_id)

    def ficha_do_produto(self, produto_id: int) -> FichaTecnica | None:
        return db.session.query(FichaTecnica).filter_by(produto_id=produto_id).first()

    def fases_catalogo(self, paginacao: PaginacaoQuery):
        return paginar(
            db.select(FaseProducao).order_by(FaseProducao.nome, FaseProducao.id), paginacao
        )

    def fases_catalogo_por_ids(self, ids: set[int]) -> dict[int, FaseProducao]:
        if not ids:
            return {}
        fases = db.session.query(FaseProducao).filter(FaseProducao.id.in_(ids)).all()
        return {fase.id: fase for fase in fases}

    def produtos_ativos(self) -> list[Produto]:
        return db.session.query(Produto).filter(Produto.ativo == 1).all()

    def fases_todas(self) -> list[FaseProducao]:
        return db.session.query(FaseProducao).all()

    def criar_fase(self, nome: str) -> FaseProducao:
        fase = FaseProducao(nome=nome)
        db.session.add(fase)
        db.session.flush()
        return fase

    def produtos_ativos_por_ids(self, ids: set[int]) -> dict[int, Produto]:
        produtos = (
            db.session.query(Produto)
            .filter(Produto.id.in_(ids), Produto.ativo == 1)
            .all()
        )
        return {produto.id: produto for produto in produtos}

    def inserir(self, *, produto_id, rendimento, observacao) -> FichaTecnica:
        ficha = FichaTecnica(
            produto_id=produto_id, rendimento=rendimento, observacao=observacao
        )
        db.session.add(ficha)
        db.session.flush()
        return ficha

    def substituir_conteudo(self, ficha: FichaTecnica, dados) -> None:
        ficha.produto_id = dados.produto_id
        ficha.rendimento = dados.rendimento
        ficha.observacao = dados.observacao

        ficha.componentes.clear()
        ficha.fases.clear()
        db.session.flush()

        fases_por_ordem = {}
        for dados_fase in sorted(dados.fases, key=lambda item: item.ordem):
            fase = FichaTecnicaFase(
                fase_id=dados_fase.fase_id,
                ordem=dados_fase.ordem,
                tempo_previsto_min=dados_fase.tempo_previsto_min,
            )
            ficha.fases.append(fase)
            fases_por_ordem[dados_fase.ordem] = fase

        db.session.flush()
        for dados_componente in dados.componentes:
            ficha.componentes.append(
                FichaTecnicaComponente(
                    produto_id=dados_componente.produto_id,
                    quantidade=dados_componente.quantidade,
                    fase=fases_por_ordem.get(dados_componente.fase_ordem),
                )
            )
        db.session.flush()

    def custos_ponderados_pelo_saldo(self, produto_ids: set[int]) -> dict[int, Decimal]:
        """Média do custo dos lotes com saldo, ponderada pela quantidade de cada um.

        Sem saldo, vale o custo do lote mais recente. Produtos sem custo ficam de fora.
        """
        if not produto_ids:
            return {}
        from app.features.estoque.models import Lote

        lotes = (
            db.session.query(Lote.produto_id, Lote.quantidade, Lote.custo_unitario)
            .filter(Lote.produto_id.in_(produto_ids), Lote.custo_unitario.isnot(None))
            .order_by(Lote.criado_em, Lote.id)
            .all()
        )
        ultimo: dict[int, Decimal] = {}
        soma: dict[int, list[Decimal]] = {}
        for produto_id, quantidade, custo in lotes:
            custo = para_decimal(custo)
            ultimo[produto_id] = custo
            if quantidade and quantidade > 0:
                total = soma.setdefault(produto_id, [ZERO, ZERO])
                total[0] += para_decimal(quantidade) * custo
                total[1] += para_decimal(quantidade)
        custos = dict(ultimo)
        for produto_id, (valor, quantidade) in soma.items():
            custos[produto_id] = valor / quantidade
        return {produto_id: custo_unitario(valor) for produto_id, valor in custos.items()}

    def custos_ponderados_moveis(self, produto_ids: set[int]) -> dict[int, Decimal]:
        """Custo médio ponderado móvel de cada produto, calculado pelo histórico.

        Repassa as movimentações em ordem cronológica. Cada entrada com custo
        recalcula a média: (saldo * média + quantidade * custo) / (saldo + quantidade).
        Saídas só reduzem o saldo e não mudam a média; transferências não mudam
        nenhum dos dois. Usa o custo gravado na movimentação (o do lote naquele
        momento). Lotes sem custo ficam fora do cálculo. Produtos sem nenhuma
        entrada com custo não aparecem no resultado.
        """
        if not produto_ids:
            return {}
        from sqlalchemy import func
        from sqlalchemy.orm import aliased

        from app.features.estoque.models import Lote, MovimentacaoEstoque
        from app.utils.enums import TipoMovimentacao

        origem, destino = aliased(Lote), aliased(Lote)
        movimentos = (
            db.session.query(
                MovimentacaoEstoque.tipo,
                MovimentacaoEstoque.quantidade,
                MovimentacaoEstoque.quantidade_destino,
                origem.produto_id,
                func.coalesce(MovimentacaoEstoque.custo_unitario, origem.custo_unitario),
                destino.produto_id,
                destino.custo_unitario,
            )
            .join(origem, MovimentacaoEstoque.lote_id == origem.id)
            .outerjoin(destino, MovimentacaoEstoque.lote_destino_id == destino.id)
            .filter(
                (origem.produto_id.in_(produto_ids)) | (destino.produto_id.in_(produto_ids)),
                MovimentacaoEstoque.tipo != TipoMovimentacao.TRANSFERENCIA,
            )
            .order_by(MovimentacaoEstoque.criado_em, MovimentacaoEstoque.id)
            .all()
        )

        saldo: dict[int, Decimal] = {}
        media: dict[int, Decimal] = {}

        def entrar(produto_id, quantidade, custo):
            if custo is None or produto_id not in produto_ids:
                return
            atual = max(saldo.get(produto_id, ZERO), ZERO)
            quantidade = para_decimal(quantidade)
            novo = atual + quantidade
            if novo <= 0:
                return
            media[produto_id] = (
                atual * media.get(produto_id, ZERO) + quantidade * para_decimal(custo)
            ) / novo
            saldo[produto_id] = novo

        def sair(produto_id, quantidade, custo):
            if custo is None or produto_id not in produto_ids:
                return
            saldo[produto_id] = max(saldo.get(produto_id, ZERO) - para_decimal(quantidade), ZERO)

        for tipo, quantidade, quantidade_destino, prod_origem, custo_origem, prod_destino, custo_destino in movimentos:
            if tipo in TipoMovimentacao.que_somam_na_origem():
                entrar(prod_origem, quantidade, custo_origem)
            elif tipo in TipoMovimentacao.que_subtraem_da_origem():
                sair(prod_origem, quantidade, custo_origem)
            if tipo == TipoMovimentacao.TRANSFORMACAO and prod_destino is not None:
                entrar(prod_destino, quantidade_destino or quantidade, custo_destino)
        return {produto_id: custo_unitario(valor) for produto_id, valor in media.items()}

    def remover(self, ficha: FichaTecnica) -> None:
        db.session.delete(ficha)
        db.session.flush()

    def possui_solicitacao(self, ficha_id: int) -> bool:
        from app.features.producao.models import SolicitacaoProducao

        return (
            db.session.query(SolicitacaoProducao.id)
            .filter(SolicitacaoProducao.ficha_tecnica_id == ficha_id)
            .first()
            is not None
        )
