export interface SolicitacaoProducao {
  id: number
  ficha_tecnica_id: number
  usuario_id: number
  quantidade_planejada: number
  localizacao_destino_id: number | null
  praca_id: number | null
  praca: { id: number; nome: string; ativo: number } | null
  status: string
  criado_em: string
  concluido_em: string | null
}
