import type { Conservacao, TipoProduto } from './produto'

export interface ItemInventario {
  produto_id: number
  produto: string
  tipo_produto: TipoProduto
  unidade_medida: string
  lote_id: number
  quantidade: number
  data_validade: string | null
  localizacao: string
}

export interface Localizacao {
  id: number
  nome: string
  tipo: Conservacao
  parent_id: number | null
  foto_url: string | null
}

export interface Lote {
  id: number
  produto_id: number
  produto: string
  localizacao_id: number
  localizacao: string
  quantidade: number
  data_producao: string | null
  data_validade: string | null
  custo_unitario: number | null
  fornecedor: string | null
  nota_fiscal: string | null
  criado_em: string
  itens_total: number
  itens_disponiveis: number
  itens_reservados: number
  itens_em_uso: number
  itens_consumidos: number
  itens_vencidos: number
}

export type StatusItem = 'DISPONIVEL' | 'RESERVADA' | 'EM_USO' | 'CONSUMIDA'

export interface ItemLote {
  id: number
  lote_id: number
  lote_origem_id: number
  sequencia: number
  codigo: string
  quantidade: number
  saldo: number
  fabricante: string | null
  data_fabricacao: string | null
  data_validade: string | null
  status: StatusItem
  solicitacao_producao_id: number | null
  aberto_em: string | null
  criado_em: string
}

export interface Movimento {
  id: number
  tipo: string
  lote_id: number
  lote_destino_id: number | null
  quantidade: number
  quantidade_destino: number | null
  motivo: string | null
  usuario_id: number
  observacao: string | null
  criado_em: string
}
