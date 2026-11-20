"""Consultas e persistência das praças operacionais."""

from sqlalchemy.orm import selectinload

from app.features.acessos.models import GrupoAcesso, UsuarioGrupoAcesso
from app.features.usuarios.models import Usuario
from app.utils.enums import GrupoPadrao
from app.utils.interfaces.repository import RepositorioBase
from app.utils.paginacao import PaginacaoQuery, paginar
from db.database_config import db

from .models import Praca


class PracaRepository(RepositorioBase):
    def listar(self, paginacao: PaginacaoQuery):
        return paginar(
            db.select(Praca)
            .options(selectinload(Praca.cozinheiros))
            .order_by(Praca.nome, Praca.id),
            paginacao,
        )

    def obter(self, praca_id: int, para_atualizacao: bool = False) -> Praca | None:
        consulta = (
            db.select(Praca)
            .where(Praca.id == praca_id)
            .options(selectinload(Praca.cozinheiros))
        )
        if para_atualizacao:
            consulta = consulta.with_for_update()
        return db.session.execute(consulta).scalar_one_or_none()

    def obter_por_nome(self, nome: str) -> Praca | None:
        return db.session.execute(
            db.select(Praca).where(db.func.lower(Praca.nome) == nome.lower())
        ).scalar_one_or_none()

    def cozinheiros_por_ids(self, ids: list[int]) -> list[Usuario]:
        if not ids:
            return []
        consulta = (
            db.select(Usuario)
            .options(selectinload(Usuario.grupos))
            .where(Usuario.id.in_(ids))
            .order_by(Usuario.nome, Usuario.id)
        )
        return list(db.session.execute(consulta).scalars())

    def listar_cozinheiros_ativos(self, paginacao: PaginacaoQuery):
        consulta = (
            db.select(Usuario)
            .join(UsuarioGrupoAcesso, UsuarioGrupoAcesso.usuario_id == Usuario.id)
            .join(GrupoAcesso, GrupoAcesso.id == UsuarioGrupoAcesso.grupo_acesso_id)
            .where(Usuario.ativo == 1, GrupoAcesso.nome == GrupoPadrao.COZINHA.value)
            .order_by(Usuario.nome, Usuario.id)
        )
        return paginar(consulta, paginacao)

    def inserir(self, praca: Praca) -> Praca:
        db.session.add(praca)
        db.session.flush()
        return praca
