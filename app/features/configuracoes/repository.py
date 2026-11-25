from app.utils.interfaces.repository import RepositorioBase
from db.database_config import db

from .models import ConfiguracaoSistema


class ConfiguracaoRepository(RepositorioBase):
    def valores(self) -> dict[str, str]:
        return {
            item.chave: item.valor
            for item in db.session.query(ConfiguracaoSistema).all()
        }

    def gravar(self, chave: str, valor: str) -> None:
        item = db.session.get(ConfiguracaoSistema, chave)
        if item is None:
            db.session.add(ConfiguracaoSistema(chave=chave, valor=valor))
        else:
            item.valor = valor
        db.session.flush()
