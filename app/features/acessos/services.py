from flask_sqlalchemy.pagination import Pagination

from app.utils.errors import Conflito, RegistroNaoEncontrado
from app.utils.paginacao import PaginacaoQuery

from .models import GrupoAcesso, Permissao
from .repository import AcessoRepository
from .schemas import GrupoAcessoCreate, GrupoAcessoUpdate


class AcessoService:
    def __init__(self, repository: AcessoRepository) -> None:
        self.repository = repository

    def listar_permissoes(self, paginacao: PaginacaoQuery) -> Pagination:
        return self.repository.listar_permissoes(paginacao)

    def listar_grupos(self, paginacao: PaginacaoQuery) -> Pagination:
        return self.repository.listar_grupos(paginacao)

    def contar_usuarios_por_grupo(self) -> dict[int, int]:
        return self.repository.contar_usuarios_por_grupo()

    def obter_grupo(self, grupo_id: int) -> GrupoAcesso:
        grupo = self.repository.obter_grupo(grupo_id)
        if grupo is None:
            raise RegistroNaoEncontrado("grupo de acesso não encontrado")
        return grupo

    def criar_grupo(self, dados: GrupoAcessoCreate) -> GrupoAcesso:
        with self.repository.transacao():
            if self.repository.obter_grupo_por_nome(dados.nome):
                raise Conflito("já existe um grupo de acesso com este nome")
            grupo = GrupoAcesso(nome=dados.nome, descricao=dados.descricao)
            grupo.permissoes = self._permissoes(dados.permissoes)
            return self.repository.inserir_grupo(grupo)

    def atualizar_grupo(self, grupo_id: int, dados: GrupoAcessoUpdate) -> GrupoAcesso:
        with self.repository.transacao():
            grupo = self.obter_grupo(grupo_id)
            if grupo.protegido:
                raise Conflito(f"o grupo {grupo.nome} é protegido e não pode ser alterado")
            if dados.nome is not None:
                existente = self.repository.obter_grupo_por_nome(dados.nome)
                if existente is not None and existente.id != grupo.id:
                    raise Conflito("já existe um grupo de acesso com este nome")
                grupo.nome = dados.nome
            if dados.descricao is not None:
                grupo.descricao = dados.descricao
            if dados.permissoes is not None:
                grupo.permissoes = self._permissoes(dados.permissoes)
            return grupo

    def remover_grupo(self, grupo_id: int) -> None:
        with self.repository.transacao():
            grupo = self.obter_grupo(grupo_id)
            if grupo.protegido:
                raise Conflito(f"o grupo {grupo.nome} é protegido e não pode ser excluído")
            self.repository.remover_grupo(grupo)

    def _permissoes(self, codigos: list[str]) -> list[Permissao]:
        permissoes = self.repository.permissoes_por_codigos(codigos)
        encontrados = {permissao.codigo for permissao in permissoes}
        for codigo in codigos:
            if codigo not in encontrados:
                raise ValueError(f"permissão desconhecida: {codigo}")
        return permissoes
