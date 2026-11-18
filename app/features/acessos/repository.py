from sqlalchemy.orm import selectinload

from app.utils.interfaces.repository import RepositorioBase
from app.utils.paginacao import PaginacaoQuery, paginar
from db.database_config import db

from .models import GrupoAcesso, GrupoAcessoPermissao, Permissao, UsuarioGrupoAcesso


class AcessoRepository(RepositorioBase):
    def listar_permissoes(self, paginacao: PaginacaoQuery):
        return paginar(db.select(Permissao).order_by(Permissao.id), paginacao)

    def permissoes_por_codigos(self, codigos: list[str]) -> list[Permissao]:
        if not codigos:
            return []
        consulta = db.select(Permissao).where(Permissao.codigo.in_(codigos)).order_by(Permissao.id)
        return list(db.session.execute(consulta).scalars())

    def listar_codigos_do_usuario(self, usuario_id: int) -> list[str]:
        consulta = (
            db.select(Permissao.codigo)
            .join(GrupoAcessoPermissao, GrupoAcessoPermissao.permissao_id == Permissao.id)
            .join(
                UsuarioGrupoAcesso,
                UsuarioGrupoAcesso.grupo_acesso_id == GrupoAcessoPermissao.grupo_acesso_id,
            )
            .where(UsuarioGrupoAcesso.usuario_id == usuario_id)
            .distinct()
            .order_by(Permissao.codigo)
        )
        return list(db.session.execute(consulta).scalars())

    def listar_grupos(self, paginacao: PaginacaoQuery):
        return paginar(
            db.select(GrupoAcesso)
            .options(selectinload(GrupoAcesso.permissoes))
            .order_by(GrupoAcesso.nome, GrupoAcesso.id),
            paginacao,
        )

    def grupos_por_ids(self, ids: list[int]) -> list[GrupoAcesso]:
        if not ids:
            return []
        consulta = db.select(GrupoAcesso).where(GrupoAcesso.id.in_(ids)).order_by(GrupoAcesso.nome)
        return list(db.session.execute(consulta).scalars())

    def obter_grupo(self, grupo_id: int) -> GrupoAcesso | None:
        return db.session.get(GrupoAcesso, grupo_id)

    def obter_grupo_por_nome(self, nome: str) -> GrupoAcesso | None:
        return db.session.execute(
            db.select(GrupoAcesso).where(db.func.lower(GrupoAcesso.nome) == nome.lower())
        ).scalar_one_or_none()

    def obter_grupo_protegido(self) -> GrupoAcesso | None:
        return db.session.execute(
            db.select(GrupoAcesso).where(GrupoAcesso.protegido == 1).order_by(GrupoAcesso.id)
        ).scalars().first()

    def contar_usuarios_por_grupo(self) -> dict[int, int]:
        consulta = db.select(
            UsuarioGrupoAcesso.grupo_acesso_id, db.func.count(UsuarioGrupoAcesso.usuario_id)
        ).group_by(UsuarioGrupoAcesso.grupo_acesso_id)
        return {grupo_id: total for grupo_id, total in db.session.execute(consulta).all()}

    def contar_usuarios_ativos(self, grupo_id: int) -> int:
        from app.features.usuarios.models import Usuario

        consulta = (
            db.select(db.func.count(Usuario.id))
            .join(UsuarioGrupoAcesso, UsuarioGrupoAcesso.usuario_id == Usuario.id)
            .where(UsuarioGrupoAcesso.grupo_acesso_id == grupo_id, Usuario.ativo == 1)
        )
        return db.session.execute(consulta).scalar_one()

    def inserir_grupo(self, grupo: GrupoAcesso) -> GrupoAcesso:
        db.session.add(grupo)
        db.session.flush()
        return grupo

    def remover_grupo(self, grupo: GrupoAcesso) -> None:
        db.session.delete(grupo)
        db.session.flush()
