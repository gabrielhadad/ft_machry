from db.database_config import db


class Usuario(db.Model):
    """Usuário autenticável do sistema."""

    __tablename__ = "usuario"
    __table_args__ = (
        db.CheckConstraint(
            "papel IN ('ADMIN', 'OWNER', 'USER')",
            name="ck_usuario_papel",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.Text, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    papel = db.Column(db.Text, nullable=False, default="USER", server_default="USER")
    foto_url = db.Column(db.Text)
    ativo = db.Column(db.Integer, nullable=False, default=1, server_default="1")
    deve_trocar_senha = db.Column(db.Integer, nullable=False, default=0, server_default="0")
    login_falhas = db.Column(db.Integer, nullable=False, default=0, server_default="0")
    bloqueado_ate = db.Column(db.Text)
    ultimo_login_em = db.Column(db.Text)
    senha_alterada_em = db.Column(db.Text)
    criado_em = db.Column(
        db.Text,
        nullable=False,
        server_default=db.text("(CAST(CURRENT_TIMESTAMP AS TEXT))"),
    )


class Auditoria(db.Model):
    """Trilha de eventos de segurança e administração."""

    __tablename__ = "auditoria"

    id = db.Column(db.Integer, primary_key=True)
    evento = db.Column(db.String(80), nullable=False, index=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"))
    username = db.Column(db.String(80))
    ip = db.Column(db.String(64))
    metodo = db.Column(db.String(12))
    caminho = db.Column(db.String(255))
    detalhes = db.Column(db.Text)
    criado_em = db.Column(
        db.Text,
        nullable=False,
        server_default=db.text("(CAST(CURRENT_TIMESTAMP AS TEXT))"),
        index=True,
    )
