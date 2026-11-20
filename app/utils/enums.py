from __future__ import annotations

from enum import StrEnum


class EnumBase(StrEnum):
    @classmethod
    def valores(cls) -> tuple[str, ...]:
        return tuple(membro.value for membro in cls)


class TipoProduto(EnumBase):
    INSUMO = "INSUMO"
    INTERMEDIARIO = "INTERMEDIARIO"
    FINAL = "FINAL"


class TipoConservacao(EnumBase):
    CONGELADO = "CONGELADO"
    RESFRIADO = "RESFRIADO"
    SECO = "SECO"


class UnidadeMedida(EnumBase):
    KG = "kg"
    G = "g"
    MG = "mg"
    L = "L"
    ML = "ml"
    UN = "un"
    PCT = "pct"
    CX = "cx"
    DZ = "dz"
    PC = "pç"


class TipoMovimentacao(EnumBase):
    ENTRADA = "ENTRADA"
    SAIDA = "SAIDA"
    AJUSTE_ENTRADA = "AJUSTE_ENTRADA"
    AJUSTE_SAIDA = "AJUSTE_SAIDA"
    TRANSFERENCIA = "TRANSFERENCIA"
    TRANSFORMACAO = "TRANSFORMACAO"
    PRODUCAO = "PRODUCAO"
    CONSUMO_PRODUCAO = "CONSUMO_PRODUCAO"

    @classmethod
    def manuais(cls) -> set[TipoMovimentacao]:
        return {
            cls.ENTRADA,
            cls.SAIDA,
            cls.AJUSTE_ENTRADA,
            cls.AJUSTE_SAIDA,
            cls.TRANSFERENCIA,
            cls.TRANSFORMACAO,
        }

    @classmethod
    def que_somam_na_origem(cls) -> set[TipoMovimentacao]:
        return {cls.ENTRADA, cls.PRODUCAO, cls.AJUSTE_ENTRADA}

    @classmethod
    def que_subtraem_da_origem(cls) -> set[TipoMovimentacao]:
        return {
            cls.SAIDA,
            cls.CONSUMO_PRODUCAO,
            cls.TRANSFERENCIA,
            cls.TRANSFORMACAO,
            cls.AJUSTE_SAIDA,
        }

    @classmethod
    def com_destino(cls) -> set[TipoMovimentacao]:
        return {cls.TRANSFERENCIA, cls.TRANSFORMACAO}

    @classmethod
    def que_exigem_saida(cls) -> set[TipoMovimentacao]:
        return {cls.SAIDA, cls.AJUSTE_SAIDA, cls.TRANSFERENCIA, cls.TRANSFORMACAO}

    @classmethod
    def que_exigem_motivo(cls) -> set[TipoMovimentacao]:
        return {cls.SAIDA, cls.AJUSTE_ENTRADA, cls.AJUSTE_SAIDA}


class StatusItem(EnumBase):
    DISPONIVEL = "DISPONIVEL"
    RESERVADA = "RESERVADA"
    EM_USO = "EM_USO"
    CONSUMIDA = "CONSUMIDA"

    @classmethod
    def ativos(cls) -> set[StatusItem]:
        return {cls.DISPONIVEL, cls.RESERVADA, cls.EM_USO}

    @classmethod
    def livres(cls) -> set[StatusItem]:
        return {cls.DISPONIVEL, cls.EM_USO}


class StatusSolicitacao(EnumBase):
    ABERTA = "ABERTA"
    EM_SEPARACAO = "EM_SEPARACAO"
    EM_PRODUCAO = "EM_PRODUCAO"
    CONCLUIDA = "CONCLUIDA"
    CANCELADA = "CANCELADA"

    @classmethod
    def proximos(cls, atual: str) -> set[StatusSolicitacao]:
        transicoes = {
            cls.ABERTA: {cls.EM_SEPARACAO, cls.EM_PRODUCAO, cls.CANCELADA},
            cls.EM_SEPARACAO: {cls.EM_PRODUCAO, cls.CANCELADA},
            cls.EM_PRODUCAO: {cls.CONCLUIDA, cls.CANCELADA},
            cls.CONCLUIDA: set(),
            cls.CANCELADA: set(),
        }
        return transicoes[cls(atual)]


class AcaoPermissao(EnumBase):
    LER = "ler"
    CRIAR = "criar"
    ATUALIZAR = "atualizar"
    EXCLUIR = "excluir"

    @classmethod
    def sem_exclusao(cls) -> tuple[AcaoPermissao, ...]:
        return (cls.LER, cls.CRIAR, cls.ATUALIZAR)

    @property
    def rotulo(self) -> str:
        return {
            AcaoPermissao.LER: "Visualizar",
            AcaoPermissao.CRIAR: "Criar",
            AcaoPermissao.ATUALIZAR: "Atualizar",
            AcaoPermissao.EXCLUIR: "Excluir",
        }[self]


class RecursoPermissao(EnumBase):
    PRODUTOS = "produtos"
    FICHAS_TECNICAS = "fichas_tecnicas"
    ESTOQUE = "estoque"
    LOCALIZACOES = "localizacoes"
    PRODUCAO = "producao"
    PRACAS = "pracas"
    USUARIOS = "usuarios"
    GRUPOS_ACESSO = "grupos_acesso"

    @property
    def rotulo(self) -> str:
        return {
            RecursoPermissao.PRODUTOS: "Produtos",
            RecursoPermissao.FICHAS_TECNICAS: "Fichas técnicas",
            RecursoPermissao.ESTOQUE: "Estoque",
            RecursoPermissao.LOCALIZACOES: "Localizações",
            RecursoPermissao.PRODUCAO: "Produção",
            RecursoPermissao.PRACAS: "Praças",
            RecursoPermissao.USUARIOS: "Usuários",
            RecursoPermissao.GRUPOS_ACESSO: "Grupos de acesso",
        }[self]

    @property
    def acoes(self) -> tuple[AcaoPermissao, ...]:
        sem_exclusao = {
            RecursoPermissao.ESTOQUE,
            RecursoPermissao.PRODUCAO,
        }
        if self in sem_exclusao:
            return AcaoPermissao.sem_exclusao()
        return tuple(AcaoPermissao)


class GrupoPadrao(EnumBase):
    ADMINISTRADOR = "Administrador"
    GESTOR = "Gestor"
    COZINHA = "Cozinha"

    @property
    def protegido(self) -> bool:
        return self is GrupoPadrao.ADMINISTRADOR

    @property
    def descricao(self) -> str:
        return {
            GrupoPadrao.ADMINISTRADOR: (
                "Acesso total ao sistema, inclusive a usuários e grupos de acesso."
            ),
            GrupoPadrao.GESTOR: (
                "Opera estoque, localizações e produção; consulta produtos e fichas técnicas."
            ),
            GrupoPadrao.COZINHA: (
                "Acompanha a fila de produção, atualiza o andamento e consulta fichas técnicas."
            ),
        }[self]

    @property
    def acoes_por_recurso(self) -> dict[RecursoPermissao, tuple[AcaoPermissao, ...]]:
        if self is GrupoPadrao.ADMINISTRADOR:
            return {recurso: recurso.acoes for recurso in RecursoPermissao}
        if self is GrupoPadrao.GESTOR:
            return {
                RecursoPermissao.PRODUTOS: (AcaoPermissao.LER,),
                RecursoPermissao.FICHAS_TECNICAS: (AcaoPermissao.LER,),
                RecursoPermissao.ESTOQUE: AcaoPermissao.sem_exclusao(),
                RecursoPermissao.LOCALIZACOES: tuple(AcaoPermissao),
                RecursoPermissao.PRODUCAO: AcaoPermissao.sem_exclusao(),
                RecursoPermissao.PRACAS: tuple(AcaoPermissao),
            }
        return {
            RecursoPermissao.FICHAS_TECNICAS: (AcaoPermissao.LER,),
            RecursoPermissao.PRODUCAO: (AcaoPermissao.LER, AcaoPermissao.ATUALIZAR),
            RecursoPermissao.PRACAS: (AcaoPermissao.LER,),
        }


class PapelAntigo(EnumBase):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    USER = "USER"

    @property
    def grupo(self) -> GrupoPadrao:
        return {
            PapelAntigo.OWNER: GrupoPadrao.ADMINISTRADOR,
            PapelAntigo.ADMIN: GrupoPadrao.GESTOR,
            PapelAntigo.USER: GrupoPadrao.COZINHA,
        }[self]
