export type TipoProduto = 'INSUMO' | 'INTERMEDIARIO' | 'FINAL'
export type Conservacao = 'SECO' | 'RESFRIADO' | 'CONGELADO'

export interface Produto {
  id: number
  nome: string
  tipo: TipoProduto
  unidade_medida: string
  grupo_id: number | null
  subdivisao: string | null
  conservacao: Conservacao
  validade_obrigatoria: number
  validade_padrao_dias: number | null
  foto_url: string | null
  ativo: number
  criado_em: string
}
