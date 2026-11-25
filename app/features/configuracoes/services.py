from .repository import ConfiguracaoRepository
from .schemas import Configuracoes, ConfiguracoesInput


class ConfiguracaoService:
    def __init__(self, repository: ConfiguracaoRepository | None = None) -> None:
        self.repository = repository or ConfiguracaoRepository()

    def obter(self) -> Configuracoes:
        """Valores gravados por cima dos padrões; chaves desconhecidas são ignoradas."""
        gravados = self.repository.valores()
        campos = Configuracoes.model_fields
        return Configuracoes.model_validate(
            {chave: valor for chave, valor in gravados.items() if chave in campos}
        )

    def atualizar(self, dados: ConfiguracoesInput) -> Configuracoes:
        with self.repository.transacao():
            for chave, valor in dados.model_dump(exclude_none=True).items():
                self.repository.gravar(chave, str(valor))
        return self.obter()
