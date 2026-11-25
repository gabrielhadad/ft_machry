export interface SolicitacaoProducao {
  id: number
  ficha_tecnica_id: number
  usuario_id: number
  quantidade_planejada: number
  localizacao_destino_id: number | null
  status: string
  criado_em: string
  concluido_em: string | null
  custo_total_realizado?: number | null
  custo_unitario_realizado?: number | null
  custo_realizado_completo?: boolean | null
}
