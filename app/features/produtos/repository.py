from contextlib import contextmanager

from db.database_config import db

from .models import GrupoProduto, Produto


class ProdutoRepository:
    @contextmanager
    def transacao(self):
        try:
            yield db.session
        except Exception:
            db.session.rollback()
            raise
        else:
            db.session.commit()

    def listar_ativos(self) -> list[Produto]:
        return (
            db.session.query(Produto)
            .filter(Produto.ativo == 1)
            .order_by(Produto.nome)
            .all()
        )

    def obter_ativo(self, produto_id: int) -> Produto | None:
        return db.session.query(Produto).filter_by(id=produto_id, ativo=1).first()

    def grupo_existe(self, grupo_id: int) -> bool:
        return db.session.get(GrupoProduto, grupo_id) is not None

    def possui_ficha(self, produto_id: int) -> bool:
        from app.features.fichas_tecnicas.models import FichaTecnica

        return (
            db.session.query(FichaTecnica.id)
            .filter(FichaTecnica.produto_id == produto_id)
            .first()
            is not None
        )


    def possui_lote_com_conservacao_incompativel(
        self, produto_id: int, nova_conservacao: str
    ) -> bool:
        """Impede que uma alteração no catálogo invalide lotes já armazenados."""
        from app.features.estoque.models import Localizacao, Lote

        return (
            db.session.query(Lote.id)
            .join(Localizacao, Localizacao.id == Lote.localizacao_id)
            .filter(
                Lote.produto_id == produto_id,
                Localizacao.tipo != nova_conservacao,
            )
            .first()
            is not None
        )

    def possui_lote_sem_validade(self, produto_id: int) -> bool:
        """Detecta lotes históricos incompatíveis com validade obrigatória."""
        from app.features.estoque.models import Lote

        return (
            db.session.query(Lote.id)
            .filter(
                Lote.produto_id == produto_id,
                Lote.data_validade.is_(None),
            )
            .first()
            is not None
        )

    def inserir(self, campos: dict) -> Produto:
        produto = Produto(**campos)
        db.session.add(produto)
        db.session.flush()
        return produto

    def atualizar(self, produto: Produto, campos: dict) -> Produto:
        for campo, valor in campos.items():
            setattr(produto, campo, valor)
        db.session.flush()
        return produto

    def desativar(self, produto: Produto) -> None:
        produto.ativo = 0
        db.session.flush()
