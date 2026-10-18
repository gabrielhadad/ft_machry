from db.database_config import db


class ItemInventario(db.Model):
    """Mapeamento read-only da view vw_inventario."""

    __tablename__ = "vw_inventario"

    lote_id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, nullable=False)
    produto = db.Column(db.String, nullable=False)
    tipo_produto = db.Column(db.String, nullable=False)
    unidade_medida = db.Column(db.String, nullable=False)
    quantidade = db.Column(db.Numeric, nullable=False)
    data_validade = db.Column(db.String)
    localizacao = db.Column(db.String, nullable=False)

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class MovimentacaoEstoque(db.Model):
    """Mapeamento da tabela movimentacao_estoque."""

    __tablename__ = "movimentacao_estoque"

    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String, nullable=False)
    lote_id = db.Column(db.Integer, nullable=False)
    lote_destino_id = db.Column(db.Integer)
    quantidade = db.Column(db.Numeric, nullable=False)
    quantidade_destino = db.Column(db.Numeric)
    motivo = db.Column(db.Text)
    usuario_id = db.Column(db.Integer, nullable=False)
    solicitacao_producao_id = db.Column(db.Integer)
    sp_componente_id = db.Column(db.Integer)
    observacao = db.Column(db.Text)
    criado_em = db.Column(db.String, nullable=False)

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
