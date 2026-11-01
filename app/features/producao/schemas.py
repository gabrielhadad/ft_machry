"""Schemas Pydantic de entrada e saída da API de produção."""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


PrioridadeProducao = Literal["BAIXA", "NORMAL", "ALTA", "URGENTE"]
StatusProducao = Literal["ABERTA", "EM_SEPARACAO", "EM_PRODUCAO", "CONCLUIDA", "CANCELADA"]


def _normalizar_data_hora(valor: Optional[str], campo: str) -> Optional[str]:
    if valor is None:
        return None
    valor = valor.strip()
    if not valor:
        return None
    try:
        momento = datetime.fromisoformat(valor)
    except ValueError as exc:
        raise ValueError(f"{campo} deve estar em formato ISO 8601") from exc
    return momento.isoformat(timespec="seconds")


def _normalizar_texto(valor: Optional[str]) -> Optional[str]:
    if valor is None:
        return None
    valor = valor.strip()
    return valor or None


class SolicitacaoCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ficha_tecnica_id: int = Field(gt=0)
    quantidade_planejada: Optional[float] = Field(default=None, gt=0, allow_inf_nan=False)
    prioridade: PrioridadeProducao = "NORMAL"
    previsto_para: Optional[str] = None
    responsavel_id: Optional[int] = Field(default=None, gt=0)
    observacao: Optional[str] = Field(default=None, max_length=2000)

    @field_validator("previsto_para")
    @classmethod
    def validar_previsto_para(cls, valor: Optional[str]) -> Optional[str]:
        return _normalizar_data_hora(valor, "previsto_para")

    @field_validator("observacao")
    @classmethod
    def normalizar_observacao(cls, valor: Optional[str]) -> Optional[str]:
        return _normalizar_texto(valor)


class SolicitacaoStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: StatusProducao
    localizacao_destino_id: Optional[int] = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validar_destino(self):
        if self.localizacao_destino_id is not None and self.status != "CONCLUIDA":
            raise ValueError("localizacao_destino_id só pode ser informado ao concluir")
        return self


class FaseExecucaoUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sp_fase_id: int = Field(gt=0)
    tempo_realizado_min: Optional[int] = Field(default=None, ge=0)
    observacao: Optional[str] = Field(default=None, max_length=2000)
    iniciado_em: Optional[str] = None
    finalizado_em: Optional[str] = None

    @field_validator("observacao")
    @classmethod
    def normalizar_observacao(cls, valor: Optional[str]) -> Optional[str]:
        return _normalizar_texto(valor)

    @field_validator("iniciado_em")
    @classmethod
    def validar_inicio(cls, valor: Optional[str]) -> Optional[str]:
        return _normalizar_data_hora(valor, "iniciado_em")

    @field_validator("finalizado_em")
    @classmethod
    def validar_fim(cls, valor: Optional[str]) -> Optional[str]:
        return _normalizar_data_hora(valor, "finalizado_em")

    @model_validator(mode="after")
    def validar_intervalo(self):
        if self.iniciado_em and self.finalizado_em:
            inicio = datetime.fromisoformat(self.iniciado_em)
            fim = datetime.fromisoformat(self.finalizado_em)
            if fim < inicio:
                raise ValueError("finalizado_em não pode ser anterior a iniciado_em")
        return self


class PerdaProducaoInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sp_componente_id: int = Field(gt=0)
    quantidade: float = Field(gt=0, allow_inf_nan=False)
    motivo: str = Field(min_length=1, max_length=500)

    @field_validator("motivo")
    @classmethod
    def normalizar_motivo(cls, valor: str) -> str:
        valor = valor.strip()
        if not valor:
            raise ValueError("motivo da perda é obrigatório")
        return valor


class ExecucaoProducaoUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    quantidade_produzida: Optional[float] = Field(default=None, ge=0, allow_inf_nan=False)
    observacao_execucao: Optional[str] = Field(default=None, max_length=2000)
    fases: list[FaseExecucaoUpdate] = Field(default_factory=list)
    perdas: list[PerdaProducaoInput] = Field(default_factory=list)

    @field_validator("observacao_execucao")
    @classmethod
    def normalizar_observacao(cls, valor: Optional[str]) -> Optional[str]:
        return _normalizar_texto(valor)

    @model_validator(mode="after")
    def validar_conteudo(self):
        ids = [fase.sp_fase_id for fase in self.fases]
        if len(ids) != len(set(ids)):
            raise ValueError("a mesma fase não pode aparecer duas vezes na execução")
        if (
            self.quantidade_produzida is None
            and self.observacao_execucao is None
            and not self.fases
            and not self.perdas
        ):
            raise ValueError("informe ao menos um dado de execução")
        return self


class SolicitacaoProducaoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ficha_tecnica_id: int
    usuario_id: int
    responsavel_id: Optional[int] = None
    quantidade_planejada: float
    quantidade_produzida: Optional[float] = None
    prioridade: str
    previsto_para: Optional[str] = None
    observacao: Optional[str] = None
    observacao_execucao: Optional[str] = None
    status: str
    criado_em: str
    iniciado_em: Optional[str] = None
    concluido_em: Optional[str] = None
    perda_rendimento: Optional[float] = None


class ComponenteSolicitacaoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sp_componente_id: int
    solicitacao_producao_id: int
    produto_id: int
    componente: str
    unidade_medida: str
    fase_ordem: Optional[int] = None
    fase: Optional[str] = None
    quantidade_prevista: float
    quantidade_realizada: float
    custo_realizado: Optional[float] = None


class FaseSolicitacaoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sp_fase_id: int
    fase_id: int
    ordem: int
    fase: str
    tempo_previsto_min: int
    tempo_realizado_min: Optional[int] = None
    observacao: Optional[str] = None
    iniciado_em: Optional[str] = None
    finalizado_em: Optional[str] = None


class LoteProduzidoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    solicitacao_producao_id: int
    lote_id: int
    quantidade: float
    criado_em: str


class SolicitacaoDetalheOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    solicitacao: SolicitacaoProducaoOut
    componentes: list[ComponenteSolicitacaoOut]
    fases: list[FaseSolicitacaoOut]
    lotes_produzidos: list[LoteProduzidoOut]
