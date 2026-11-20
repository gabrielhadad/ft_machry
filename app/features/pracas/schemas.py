"""Entradas e respostas da API de praças."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator


UsuarioId = Annotated[int, Field(gt=0)]


class PracaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nome: str = Field(min_length=2, max_length=120)
    descricao: str | None = None
    cozinheiros: list[UsuarioId] = Field(min_length=1)

    @field_validator("nome", mode="before")
    @classmethod
    def limpar_nome(cls, valor):
        return valor.strip() if isinstance(valor, str) else valor

    @field_validator("descricao")
    @classmethod
    def limpar_descricao(cls, valor: str | None) -> str | None:
        return valor.strip() or None if valor is not None else None

    @field_validator("cozinheiros")
    @classmethod
    def ids_unicos(cls, valores: list[int]) -> list[int]:
        if len(valores) != len(set(valores)):
            raise ValueError("não é permitido repetir o mesmo cozinheiro")
        return valores


class PracaUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nome: str | None = Field(default=None, min_length=2, max_length=120)
    descricao: str | None = None
    ativo: int | None = Field(default=None, ge=0, le=1)
    cozinheiros: list[UsuarioId] | None = Field(default=None, min_length=1)

    @field_validator("nome", mode="before")
    @classmethod
    def limpar_nome(cls, valor):
        return valor.strip() if isinstance(valor, str) else valor

    @field_validator("descricao")
    @classmethod
    def limpar_descricao(cls, valor: str | None) -> str | None:
        return valor.strip() or None if valor is not None else None

    @field_validator("cozinheiros")
    @classmethod
    def ids_unicos(cls, valores: list[int] | None) -> list[int] | None:
        if valores is not None and len(valores) != len(set(valores)):
            raise ValueError("não é permitido repetir o mesmo cozinheiro")
        return valores


class CozinheiroResumo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    username: str


class PracaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    descricao: str | None
    ativo: int
    criado_em: str
    cozinheiros: list[CozinheiroResumo]
