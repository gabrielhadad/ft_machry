from flask_sqlalchemy.pagination import Pagination
from werkzeug.security import generate_password_hash

from app.features.acessos.models import GrupoAcesso
from app.features.acessos.repository import AcessoRepository
from app.utils.enums import GrupoPadrao
from app.utils.errors import Conflito, RegistroNaoEncontrado
from app.utils.paginacao import PaginacaoQuery

from .models import Usuario
from .repository import UsuarioRepository
from .schemas import UsuarioCreate, UsuarioUpdate


class UsuarioService:
    def __init__(self, repository: UsuarioRepository, acessos: AcessoRepository) -> None:
        self.repository = repository
        self.acessos = acessos

    def listar(self, paginacao: PaginacaoQuery) -> Pagination:
        return self.repository.listar(paginacao)

    def obter(self, usuario_id: int) -> Usuario:
        usuario = self.repository.obter(usuario_id)
        if usuario is None:
            raise RegistroNaoEncontrado("usuário não encontrado")
        return usuario

    def criar(self, dados: UsuarioCreate) -> Usuario:
        username = dados.username.lower()
        with self.repository.transacao():
            if self.repository.obter_por_username(username):
                raise Conflito("nome de usuário já cadastrado")
            return self.repository.inserir(
                {
                    "nome": dados.nome,
                    "username": username,
                    "senha_hash": generate_password_hash(dados.password),
                    "grupos": self._grupos(dados.grupos),
                }
            )

    def atualizar(self, usuario_id: int, dados: UsuarioUpdate, usuario_logado_id: int) -> Usuario:
        with self.repository.transacao():
            usuario = self.obter(usuario_id)
            if dados.nome is not None:
                usuario.nome = dados.nome.strip()
            if dados.password is not None:
                usuario.senha_hash = generate_password_hash(dados.password)
            if dados.grupos is not None:
                usuario.grupos = self._grupos(dados.grupos)
            if dados.ativo is not None:
                if usuario.id == usuario_logado_id and not dados.ativo:
                    raise Conflito("a conta em uso não pode ser desativada")
                usuario.ativo = dados.ativo
            self._garantir_administrador_ativo()
            self._garantir_pracas_com_cozinheiro_ativo(usuario)
            return usuario

    def remover(self, usuario_id: int, usuario_logado_id: int) -> None:
        with self.repository.transacao():
            usuario = self.obter(usuario_id)
            if usuario.id == usuario_logado_id:
                raise Conflito("a conta em uso não pode ser excluída")
            self.repository.desativar(usuario)
            self._garantir_administrador_ativo()
            self._garantir_pracas_com_cozinheiro_ativo(usuario)

    def _grupos(self, ids: list[int]) -> list[GrupoAcesso]:
        grupos = self.acessos.grupos_por_ids(ids)
        if len(grupos) != len(ids):
            raise ValueError("grupo de acesso não encontrado")
        return grupos

    def _garantir_administrador_ativo(self) -> None:
        grupo = self.acessos.obter_grupo_protegido()
        if grupo is not None and self.acessos.contar_usuarios_ativos(grupo.id) == 0:
            raise Conflito(f"o grupo {grupo.nome} precisa manter ao menos um usuário ativo")

    def _garantir_pracas_com_cozinheiro_ativo(self, usuario: Usuario) -> None:
        # Não permite deixar uma praça ativa sem nenhum cozinheiro elegível.
        for praca in usuario.pracas:
            if not praca.ativo:
                continue
            elegiveis = [
                membro for membro in praca.cozinheiros
                if membro.ativo and any(
                    grupo.nome == GrupoPadrao.COZINHA.value for grupo in membro.grupos
                )
            ]
            if not elegiveis:
                raise Conflito(
                    f"a praça {praca.nome} precisa manter ao menos um cozinheiro ativo"
                )
