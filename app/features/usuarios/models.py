from db.database_config import db


class Usuario(db.Model):
    __tablename__ = "usuario"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.Text, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    foto_url = db.Column(db.Text)
    ativo = db.Column(db.Integer, nullable=False, default=1, server_default="1")
    criado_em = db.Column(
        db.Text,
        nullable=False,
        server_default=db.text("(CAST(CURRENT_TIMESTAMP AS TEXT))"),
    )

    grupos = db.relationship(
        "GrupoAcesso",
        secondary="usuario_grupo_acesso",
        back_populates="usuarios",
        order_by="GrupoAcesso.nome",
    )
