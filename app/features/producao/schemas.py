"""Schemas Pydantic de saída da API de produção."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.utils.enums import StatusSolicitacao


class SolicitacaoCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ficha_tecnica_id: int = Field(gt=0)
    quantidade_planejada: Optional[float] = Field(default=None, gt=0, allow_inf_nan=False)
    localizacao_destino_id: Optional[int] = Field(default=None, gt=0)


class SolicitacaoStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: StatusSolicitacao


class SolicitacaoProducaoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ficha_tecnica_id: int
    usuario_id: int
    quantidade_planejada: float
    localizacao_destino_id: Optional[int] = None
    status: str
    criado_em: str
    concluido_em: Optional[str] = None
    custo_total_realizado: Optional[float] = None
    custo_unitario_realizado: Optional[float] = None
    custo_realizado_completo: Optional[bool] = None


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

    ordem: int
    fase: str
    tempo_previsto_min: int
    tempo_realizado_min: Optional[int] = None


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
