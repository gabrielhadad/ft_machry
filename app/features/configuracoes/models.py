from db.database_config import db


class ConfiguracaoSistema(db.Model):
    """Configurações gerais do sistema, guardadas como pares chave e valor."""

    __tablename__ = "configuracao_sistema"

    chave = db.Column(db.Text, primary_key=True)
    valor = db.Column(db.Text, nullable=False)
