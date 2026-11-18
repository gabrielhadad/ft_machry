from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.features.acessos.schemas import GrupoAcessoResumo


class UsuarioCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nome: str = Field(min_length=2, max_length=120)
    username: str = Field(pattern=r"^[a-zA-Z0-9._-]+$", min_length=3, max_length=80)
    password: str = Field(min_length=8, max_length=200)
    grupos: list[int] = Field(default_factory=list)

    @field_validator("nome", "username")
    @classmethod
    def limpar_texto(cls, valor: str) -> str:
        return valor.strip()

    @field_validator("grupos")
    @classmethod
    def remover_repetidos(cls, valores: list[int]) -> list[int]:
        return list(dict.fromkeys(valores))


class UsuarioUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nome: str | None = Field(default=None, min_length=2, max_length=120)
    password: str | None = Field(default=None, min_length=8, max_length=200)
    grupos: list[int] | None = None
    ativo: int | None = Field(default=None, ge=0, le=1)

    @field_validator("grupos")
    @classmethod
    def remover_repetidos(cls, valores: list[int] | None) -> list[int] | None:
        return list(dict.fromkeys(valores)) if valores is not None else None


class UsuarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    username: str
    ativo: int
    grupos: list[GrupoAcessoResumo]
