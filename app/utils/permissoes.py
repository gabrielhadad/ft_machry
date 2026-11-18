from app.utils.constantes import Constantes
from app.utils.enums import AcaoPermissao, GrupoPadrao, RecursoPermissao


def codigo_de_permissao(recurso: RecursoPermissao, acao: AcaoPermissao) -> str:
    if acao not in recurso.acoes:
        raise ValueError(f"a permissão {recurso}:{acao} não existe no catálogo")
    return f"{recurso}:{acao}"


def catalogo_de_permissoes() -> list[dict]:
    permissoes = []
    for recurso in RecursoPermissao:
        for acao in recurso.acoes:
            permissoes.append(
                {
                    "codigo": codigo_de_permissao(recurso, acao),
                    "recurso": recurso.value,
                    "acao": acao.value,
                    "descricao": f"{acao.rotulo} {recurso.rotulo.lower()}",
                }
            )
    return permissoes


def permissoes_do_grupo_padrao(grupo: GrupoPadrao) -> list[str]:
    return [
        codigo_de_permissao(recurso, acao)
        for recurso, acoes in grupo.acoes_por_recurso.items()
        for acao in acoes
    ]


def exigir_permissao(recurso: RecursoPermissao, acao: AcaoPermissao):
    codigo = codigo_de_permissao(recurso, acao)

    def marcar(funcao):
        setattr(funcao, Constantes.ATRIBUTO_DE_PERMISSAO_DA_ROTA, codigo)
        return funcao

    return marcar


def permissao_exigida(funcao) -> str | None:
    return getattr(funcao, Constantes.ATRIBUTO_DE_PERMISSAO_DA_ROTA, None)
