from pydantic import BaseModel, ConfigDict

from app.utils.enums import MetodoCustoMedio


class Configuracoes(BaseModel):
    metodo_custo_medio: MetodoCustoMedio = MetodoCustoMedio.PONDERADO_MOVEL


class ConfiguracoesInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metodo_custo_medio: MetodoCustoMedio | None = None
