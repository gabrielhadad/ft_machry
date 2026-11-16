from db.database_config import db


class Permissao(db.Model):
    __tablename__ = "permissao"

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.Text, nullable=False, unique=True)
    recurso = db.Column(db.Text, nullable=False)
    acao = db.Column(db.Text, nullable=False)
    descricao = db.Column(db.Text, nullable=False)

    grupos = db.relationship(
        "GrupoAcesso", secondary="grupo_acesso_permissao", back_populates="permissoes"
    )


class GrupoAcesso(db.Model):
    __tablename__ = "grupo_acesso"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.Text, nullable=False, unique=True)
    descricao = db.Column(db.Text)
    protegido = db.Column(db.Integer, nullable=False, default=0, server_default="0")
    criado_em = db.Column(
        db.Text,
        nullable=False,
        server_default=db.text("(CAST(CURRENT_TIMESTAMP AS TEXT))"),
    )

    permissoes = db.relationship(
        "Permissao",
        secondary="grupo_acesso_permissao",
        back_populates="grupos",
        order_by="Permissao.id",
    )
    usuarios = db.relationship(
        "Usuario", secondary="usuario_grupo_acesso", back_populates="grupos"
    )


class GrupoAcessoPermissao(db.Model):
    __tablename__ = "grupo_acesso_permissao"

    grupo_acesso_id = db.Column(
        db.Integer, db.ForeignKey("grupo_acesso.id"), primary_key=True
    )
    permissao_id = db.Column(db.Integer, db.ForeignKey("permissao.id"), primary_key=True)


class UsuarioGrupoAcesso(db.Model):
    __tablename__ = "usuario_grupo_acesso"

    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), primary_key=True)
    grupo_acesso_id = db.Column(
        db.Integer, db.ForeignKey("grupo_acesso.id"), primary_key=True
    )
