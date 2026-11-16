"""Constantes globais compartilhadas entre as features."""


class Constantes:
    POR_PAGINA_PADRAO = 20
    POR_PAGINA_MAXIMO = 500

    ROTAS_PUBLICAS = {"/api/auth/login"}
    PREFIXOS_PUBLICOS = ("/api/branding",)
    ROTAS_DE_SESSAO = {"/api/auth/me", "/api/auth/logout"}
    ATRIBUTO_DE_PERMISSAO_DA_ROTA = "permissao_exigida"

    PREFIXO_CODIGO_ITEM = "FT"

    @staticmethod
    def sql_in(coluna: str, valores: tuple[str, ...]) -> str:
        """Monta a expressão `coluna IN ('A', 'B')` usada nos CHECKs do banco."""
        return f"{coluna} IN ({', '.join(repr(v) for v in valores)})"
