from pydantic import BaseModel, ConfigDict, Field, field_validator


class PermissaoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    codigo: str
    recurso: str
    acao: str
    descricao: str


class GrupoAcessoResumo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str


class GrupoAcessoCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nome: str = Field(min_length=2, max_length=80)
    descricao: str | None = Field(default=None, max_length=300)
    permissoes: list[str] = Field(default_factory=list)

    @field_validator("nome")
    @classmethod
    def limpar_nome(cls, valor: str) -> str:
        return valor.strip()

    @field_validator("permissoes")
    @classmethod
    def remover_repetidas(cls, valores: list[str]) -> list[str]:
        return list(dict.fromkeys(valores))


class GrupoAcessoUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nome: str | None = Field(default=None, min_length=2, max_length=80)
    descricao: str | None = Field(default=None, max_length=300)
    permissoes: list[str] | None = None

    @field_validator("nome")
    @classmethod
    def limpar_nome(cls, valor: str | None) -> str | None:
        return valor.strip() if valor is not None else None

    @field_validator("permissoes")
    @classmethod
    def remover_repetidas(cls, valores: list[str] | None) -> list[str] | None:
        return list(dict.fromkeys(valores)) if valores is not None else None


class GrupoAcessoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    descricao: str | None
    protegido: int
    permissoes: list[PermissaoOut]
