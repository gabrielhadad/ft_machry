from __future__ import annotations

from contextlib import contextmanager
from datetime import date
from typing import Optional

from sqlalchemy import text

from db.database_config import db

from app.features.auth.models import Usuario
from .models import Localizacao, Lote, MovimentacaoEstoque, Produto, ProdutoTransformacao

_TIPOS_SOMAM_NA_ORIGEM = {"ENTRADA", "PRODUCAO", "AJUSTE_ENTRADA"}
_TIPOS_SUBTRAEM_DA_ORIGEM = {"SAIDA", "CONSUMO_PRODUCAO", "TRANSFERENCIA",
                             "TRANSFORMACAO", "AJUSTE_SAIDA", "PERDA"}
_TIPOS_COM_DESTINO = {"TRANSFERENCIA", "TRANSFORMACAO"}


class EstoqueRepository:

    @contextmanager
    def transacao(self):
        try:
            yield db.session
        except Exception:
            db.session.rollback()
            raise
        else:
            db.session.commit()

    # -- inventário / movimentações -----------------------------------------

    def listar_inventario(self, produto_id: Optional[int] = None, lote_id: Optional[int] = None):
        sql = "SELECT * FROM vw_inventario WHERE 1=1"
        params: dict = {}
        if produto_id is not None:
            sql += " AND produto_id = :produto_id"
            params["produto_id"] = produto_id
        if lote_id is not None:
            sql += " AND lote_id = :lote_id"
            params["lote_id"] = lote_id
        sql += " ORDER BY produto, data_validade, lote_id"
        return db.session.execute(text(sql), params).mappings().all()

    def listar_movimentacoes(
        self,
        limite: int = 100,
        lote_id: Optional[int] = None,
        usuario_id: Optional[int] = None,
        tipo: Optional[str] = None,
    ):
        sql = "SELECT * FROM movimentacao_estoque WHERE 1=1"
        params: dict = {"limite": limite}
        if lote_id is not None:
            sql += " AND lote_id = :lote_id"
            params["lote_id"] = lote_id
        if usuario_id is not None:
            sql += " AND usuario_id = :usuario_id"
            params["usuario_id"] = usuario_id
        if tipo is not None:
            sql += " AND tipo = :tipo"
            params["tipo"] = tipo
        sql += " ORDER BY id DESC LIMIT :limite"
        return db.session.execute(text(sql), params).mappings().all()

    def obter_movimentacao(self, mov_id: int) -> Optional[MovimentacaoEstoque]:
        return db.session.get(MovimentacaoEstoque, mov_id)

    def inserir_movimentacao(
        self, *, tipo, lote_origem: Lote, lote_destino: Optional[Lote], quantidade,
        quantidade_destino, motivo, usuario_id, observacao,
        solicitacao_producao_id=None, sp_componente_id=None,
    ) -> MovimentacaoEstoque:
        mov = MovimentacaoEstoque(
            tipo=tipo,
            lote_id=lote_origem.id,
            lote_destino_id=lote_destino.id if lote_destino is not None else None,
            quantidade=quantidade,
            quantidade_destino=quantidade_destino,
            motivo=motivo,
            usuario_id=usuario_id,
            solicitacao_producao_id=solicitacao_producao_id,
            sp_componente_id=sp_componente_id,
            observacao=observacao,
        )
        db.session.add(mov)
        self._aplicar_saldo(
            tipo=tipo, lote_origem=lote_origem, lote_destino=lote_destino,
            quantidade=quantidade, quantidade_destino=quantidade_destino,
        )
        db.session.flush()
        db.session.refresh(mov)
        return mov

    def _aplicar_saldo(self, *, tipo, lote_origem: Lote, lote_destino: Optional[Lote],
                        quantidade, quantidade_destino) -> None:
        if tipo in _TIPOS_SOMAM_NA_ORIGEM:
            lote_origem.quantidade += quantidade
        elif tipo in _TIPOS_SUBTRAEM_DA_ORIGEM:
            lote_origem.quantidade -= quantidade

        if tipo in _TIPOS_COM_DESTINO:
            lote_destino.quantidade += quantidade_destino if quantidade_destino is not None else quantidade

    def transformacao_cadastrada(self, produto_origem_id: int, produto_destino_id: int) -> bool:
        return db.session.get(ProdutoTransformacao, (produto_origem_id, produto_destino_id)) is not None

    def listar_transformacoes(self, produto_origem_id: Optional[int] = None):
        sql = """
            SELECT pt.produto_origem_id, pt.produto_destino_id,
                   p.nome AS produto_destino, p.unidade_medida, p.conservacao
              FROM produto_transformacao pt
              JOIN produto p ON p.id = pt.produto_destino_id
             WHERE p.ativo = 1
        """
        params: dict = {}
        if produto_origem_id is not None:
            sql += " AND pt.produto_origem_id = :produto_origem_id"
            params["produto_origem_id"] = produto_origem_id
        sql += " ORDER BY p.nome, p.id"
        return db.session.execute(text(sql), params).mappings().all()

    def inserir_transformacao(self, produto_origem_id: int, produto_destino_id: int) -> ProdutoTransformacao:
        regra = ProdutoTransformacao(
            produto_origem_id=produto_origem_id, produto_destino_id=produto_destino_id
        )
        db.session.add(regra)
        db.session.flush()
        return regra

    def remover_transformacao(self, produto_origem_id: int, produto_destino_id: int) -> bool:
        regra = db.session.get(
            ProdutoTransformacao, (produto_origem_id, produto_destino_id)
        )
        if regra is None:
            return False
        db.session.delete(regra)
        return True

    # -- localização -----------------------------------------------------------

    def listar_localizacoes(self) -> list[Localizacao]:
        return db.session.query(Localizacao).order_by(Localizacao.nome).all()

    def obter_localizacao(self, loc_id: int) -> Optional[Localizacao]:
        return db.session.get(Localizacao, loc_id)

    def inserir_localizacao(self, *, nome, tipo, parent_id, foto_url) -> Localizacao:
        localizacao = Localizacao(nome=nome, tipo=tipo, parent_id=parent_id, foto_url=foto_url)
        db.session.add(localizacao)
        db.session.flush()
        return localizacao

    def atualizar_localizacao(self, loc_id: int, campos: dict) -> None:
        localizacao = db.session.get(Localizacao, loc_id)
        for campo, valor in campos.items():
            setattr(localizacao, campo, valor)

    def localizacao_tem_filhas(self, loc_id: int) -> bool:
        return (
            db.session.query(Localizacao.id)
            .filter(Localizacao.parent_id == loc_id)
            .first()
            is not None
        )

    def localizacao_tem_lotes(self, loc_id: int) -> bool:
        return (
            db.session.query(Lote.id)
            .filter(Lote.localizacao_id == loc_id)
            .first()
            is not None
        )

    def remover_localizacao(self, loc_id: int) -> bool:
        localizacao = db.session.get(Localizacao, loc_id)
        if localizacao is None:
            return False
        db.session.delete(localizacao)
        return True

    def existe_incompatibilidade_tipo(self, loc_id: int, novo_tipo: str) -> bool:
        return (
            db.session.query(Lote)
            .join(Produto, Produto.id == Lote.produto_id)
            .filter(Lote.localizacao_id == loc_id, Produto.conservacao != novo_tipo)
            .first()
            is not None
        )

    # -- lote --------------------------------------------------------------------

    def listar_lotes(self, produto_id: Optional[int] = None, localizacao_id: Optional[int] = None):
        sql = """SELECT l.*, p.nome AS produto, loc.nome AS localizacao FROM lote l
                 JOIN produto p ON p.id = l.produto_id
                 JOIN localizacao loc ON loc.id = l.localizacao_id WHERE 1=1"""
        params: dict = {}
        if produto_id is not None:
            sql += " AND l.produto_id = :produto_id"
            params["produto_id"] = produto_id
        if localizacao_id is not None:
            sql += " AND l.localizacao_id = :localizacao_id"
            params["localizacao_id"] = localizacao_id
        sql += " ORDER BY l.data_validade IS NULL, l.data_validade, l.id"
        return db.session.execute(text(sql), params).mappings().all()

    def obter_lote(self, lote_id: int, para_atualizacao: bool = False) -> Optional[Lote]:
        return db.session.get(Lote, lote_id, with_for_update=para_atualizacao)

    def buscar_lote_transferencia_compativel(
        self, origem: Lote, localizacao_destino_id: int
    ) -> Optional[Lote]:
        """Reaproveita somente um lote que represente o mesmo lote físico/histórico.

        Produto e localização não bastam: validade, produção e custo também precisam
        coincidir para evitar a mistura de lotes com rastreabilidades diferentes.
        """
        consulta = db.session.query(Lote).filter(
            Lote.id != origem.id,
            Lote.produto_id == origem.produto_id,
            Lote.localizacao_id == localizacao_destino_id,
            Lote.data_producao == origem.data_producao,
            Lote.data_validade == origem.data_validade,
        )
        if origem.custo_unitario is None:
            consulta = consulta.filter(Lote.custo_unitario.is_(None))
        else:
            consulta = consulta.filter(Lote.custo_unitario == origem.custo_unitario)
        return consulta.order_by(Lote.id).first()

    def buscar_lote_transformacao_compativel(
        self, *, produto_destino_id: int, localizacao_destino_id: int,
        data_producao, data_validade, custo_unitario
    ) -> Optional[Lote]:
        consulta = db.session.query(Lote).filter(
            Lote.produto_id == produto_destino_id,
            Lote.localizacao_id == localizacao_destino_id,
            Lote.data_producao == data_producao,
            Lote.data_validade == data_validade,
        )
        if custo_unitario is None:
            consulta = consulta.filter(Lote.custo_unitario.is_(None))
        else:
            consulta = consulta.filter(Lote.custo_unitario == custo_unitario)
        return consulta.order_by(Lote.id).first()

    def inserir_lote(
        self, *, produto_id, localizacao_id, data_producao, data_validade, custo_unitario
    ) -> Lote:
        lote = Lote(
            produto_id=produto_id,
            localizacao_id=localizacao_id,
            quantidade=0,
            data_producao=data_producao,
            data_validade=data_validade,
            custo_unitario=custo_unitario,
        )
        db.session.add(lote)
        db.session.flush()
        db.session.refresh(lote)
        return lote

    def atualizar_lote(self, lote_id: int, campos: dict) -> None:
        lote = db.session.get(Lote, lote_id)
        for campo, valor in campos.items():
            setattr(lote, campo, valor)

    def lotes_fefo_disponiveis(self, produto_id: int):
        return db.session.execute(
            text(
                """SELECT * FROM lote WHERE produto_id = :produto_id AND quantidade > 0
                   AND (data_validade IS NULL OR data_validade >= :hoje)
                   ORDER BY data_validade IS NULL, data_validade, criado_em, id"""
            ),
            {"produto_id": produto_id, "hoje": date.today().isoformat()},
        ).mappings().all()

    def lotes_fefo_para_consumo(self, produto_id: int) -> list[Lote]:
        """Lotes válidos em FEFO, bloqueados durante a baixa quando o banco suporta FOR UPDATE."""
        consulta = (
            db.select(Lote)
            .where(
                Lote.produto_id == produto_id,
                Lote.quantidade > 0,
                db.or_(Lote.data_validade.is_(None), Lote.data_validade >= date.today().isoformat()),
            )
            .order_by(
                Lote.data_validade.is_(None),
                Lote.data_validade,
                Lote.criado_em,
                Lote.id,
            )
            .with_for_update()
        )
        return list(db.session.scalars(consulta).all())

    def existe_consumo_producao(self, solicitacao_id: int) -> bool:
        return db.session.scalar(
            db.select(MovimentacaoEstoque.id)
            .where(
                MovimentacaoEstoque.solicitacao_producao_id == solicitacao_id,
                MovimentacaoEstoque.tipo == "CONSUMO_PRODUCAO",
            )
            .limit(1)
        ) is not None

    def existe_producao(self, solicitacao_id: int) -> bool:
        return db.session.scalar(
            db.select(MovimentacaoEstoque.id)
            .where(
                MovimentacaoEstoque.solicitacao_producao_id == solicitacao_id,
                MovimentacaoEstoque.tipo == "PRODUCAO",
            )
            .limit(1)
        ) is not None

    def primeira_localizacao_compativel(self, tipo: str) -> Optional[Localizacao]:
        return db.session.execute(
            db.select(Localizacao)
            .where(Localizacao.tipo == tipo)
            .order_by(Localizacao.id)
            .limit(1)
        ).scalar_one_or_none()

    # -- entidades de outras features, lidas só para validação cruzada --------

    def obter_produto(self, produto_id: int) -> Optional[Produto]:
        return db.session.get(Produto, produto_id)

    def obter_produto_ativo(self, produto_id: int) -> Optional[Produto]:
        produto = db.session.get(Produto, produto_id)
        return produto if produto is not None and produto.ativo else None

    def obter_usuario_ativo(self, usuario_id: int) -> Optional[Usuario]:
        usuario = db.session.get(Usuario, usuario_id)
        return usuario if usuario is not None and usuario.ativo else None
