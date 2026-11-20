"""Regras de negócio para cadastro de praças e alocação de cozinheiros."""

from flask_sqlalchemy.pagination import Pagination

from app.utils.enums import GrupoPadrao
from app.utils.errors import Conflito, RegistroNaoEncontrado
from app.utils.paginacao import PaginacaoQuery

from .models import Praca
from .repository import PracaRepository
from .schemas import PracaCreate, PracaUpdate


class PracaService:
    def __init__(self, repository: PracaRepository) -> None:
        self.repository = repository

    def listar(self, paginacao: PaginacaoQuery) -> Pagination:
        return self.repository.listar(paginacao)

    def listar_cozinheiros(self, paginacao: PaginacaoQuery) -> Pagination:
        return self.repository.listar_cozinheiros_ativos(paginacao)

    def obter(self, praca_id: int, para_atualizacao: bool = False) -> Praca:
        praca = self.repository.obter(praca_id, para_atualizacao=para_atualizacao)
        if praca is None:
            raise RegistroNaoEncontrado("praça não encontrada")
        return praca

    def criar(self, dados: PracaCreate) -> Praca:
        with self.repository.transacao():
            self._validar_nome_disponivel(dados.nome)
            cozinheiros = self._cozinheiros_validos(dados.cozinheiros)
            return self.repository.inserir(
                Praca(nome=dados.nome, descricao=dados.descricao, cozinheiros=cozinheiros)
            )

    def atualizar(self, praca_id: int, dados: PracaUpdate) -> Praca:
        with self.repository.transacao():
            praca = self.obter(praca_id, para_atualizacao=True)
            campos = dados.model_fields_set
            if not campos:
                raise ValueError("informe ao menos um campo para atualizar")
            if "nome" in campos:
                if dados.nome is None:
                    raise ValueError("nome não pode ser nulo")
                self._validar_nome_disponivel(dados.nome, exceto_id=praca.id)
                praca.nome = dados.nome
            if "descricao" in campos:
                praca.descricao = dados.descricao
            if "cozinheiros" in campos:
                if dados.cozinheiros is None:
                    raise ValueError("cozinheiros não pode ser nulo")
                praca.cozinheiros = self._cozinheiros_validos(dados.cozinheiros)
            if "ativo" in campos:
                if dados.ativo is None:
                    raise ValueError("ativo não pode ser nulo")
                if dados.ativo == 1 and not praca.ativo:
                    # Reativação exige uma equipe elegível no momento da operação.
                    praca.cozinheiros = self._cozinheiros_validos(
                        [usuario.id for usuario in praca.cozinheiros]
                    )
                praca.ativo = dados.ativo
            return praca

    def desativar(self, praca_id: int) -> None:
        with self.repository.transacao():
            praca = self.obter(praca_id, para_atualizacao=True)
            # Não apaga vínculos: produções antigas precisam manter a referência.
            praca.ativo = 0

    def _validar_nome_disponivel(self, nome: str, exceto_id: int | None = None) -> None:
        existente = self.repository.obter_por_nome(nome)
        if existente is not None and existente.id != exceto_id:
            raise Conflito("já existe uma praça com este nome")

    def _cozinheiros_validos(self, ids: list[int]):
        if not ids:
            raise ValueError("a praça precisa ter pelo menos um cozinheiro")
        usuarios = self.repository.cozinheiros_por_ids(ids)
        encontrados = {usuario.id for usuario in usuarios}
        ausentes = set(ids) - encontrados
        if ausentes:
            raise ValueError(f"cozinheiro não encontrado: {min(ausentes)}")
        for usuario in usuarios:
            if not usuario.ativo:
                raise ValueError(f"cozinheiro inativo: {usuario.id}")
            if not any(grupo.nome == GrupoPadrao.COZINHA.value for grupo in usuario.grupos):
                raise ValueError(f"usuário não pertence ao grupo Cozinha: {usuario.id}")
        return usuarios
