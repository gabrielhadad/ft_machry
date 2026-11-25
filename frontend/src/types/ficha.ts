export interface FaseCatalogo {
  id: number
  nome: string
}

export interface FichaFase {
  id: number
  fase_id: number
  fase: string
  ordem: number
  tempo_previsto_min: number
}

export interface FichaComponente {
  id: number
  produto_id: number
  produto: string
  unidade_medida: string
  quantidade: number
  ficha_tecnica_fase_id: number | null
  fase_ordem: number | null
  custo_unitario?: number | null
  custo?: number | null
  custo_fefo?: number | null
  custo_fefo_completo?: boolean
  falta_estoque?: number
}

export interface FichaTecnica {
  id: number
  produto_id: number
  produto: string
  unidade_rendimento: string
  rendimento: number
  observacao: string | null
  fases: FichaFase[]
  componentes: FichaComponente[]
  custo_total?: number | null
  custo_completo?: boolean
  custo_total_fefo?: number | null
  custo_fefo_completo?: boolean
}
