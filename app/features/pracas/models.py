"""Entidades de praça e vínculo com cozinheiros."""

from db.database_config import db


class Praca(db.Model):
    __tablename__ = "praca"
    __table_args__ = (
        db.CheckConstraint("ativo IN (0, 1)", name="ck_praca_ativo"),
    )

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False, unique=True)
    descricao = db.Column(db.Text)
    ativo = db.Column(db.Integer, nullable=False, default=1, server_default="1")
    criado_em = db.Column(
        db.Text,
        nullable=False,
        server_default=db.text("(CAST(CURRENT_TIMESTAMP AS TEXT))"),
    )

    # Um cozinheiro pode atuar em mais de uma praça.
    cozinheiros = db.relationship(
        "Usuario",
        secondary="praca_usuario",
        back_populates="pracas",
        order_by="Usuario.nome",
    )
    # Cada solicitação fica vinculada a uma única praça (opcional para dados legados).
    solicitacoes = db.relationship("SolicitacaoProducao", back_populates="praca")


class PracaUsuario(db.Model):
    __tablename__ = "praca_usuario"

    praca_id = db.Column(db.Integer, db.ForeignKey("praca.id"), primary_key=True)
    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuario.id"),
        primary_key=True,
        index=True,
    )


# O índice funcional impede nomes equivalentes, mesmo com maiúsculas diferentes.
db.Index("uq_praca_nome_normalizado", db.func.lower(Praca.__table__.c.nome), unique=True)
