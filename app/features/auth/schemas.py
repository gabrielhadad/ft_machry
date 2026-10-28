from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LoginInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=200)

    @field_validator("username")
    @classmethod
    def normalizar_username(cls, valor: str) -> str:
        return valor.strip().lower()


class UsuarioCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nome: str = Field(min_length=2, max_length=120)
    username: str = Field(pattern=r"^[a-zA-Z0-9._-]+$", min_length=3, max_length=80)
    password: str = Field(min_length=8, max_length=200)
    papel: Literal["OWNER", "ADMIN", "USER"]

    @field_validator("nome", "username")
    @classmethod
    def limpar_texto(cls, valor: str) -> str:
        return valor.strip()


class UsuarioUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nome: str | None = Field(default=None, min_length=2, max_length=120)
    password: str | None = Field(default=None, min_length=8, max_length=200)
    papel: Literal["OWNER", "ADMIN", "USER"] | None = None
    ativo: int | None = Field(default=None, ge=0, le=1)
