import { api, apiListAll } from '../../../services/api'
import type { ItemLote, Lote, Movimento } from '../../../types'
import type { NovoItem } from '../types'

export interface NovaMovimentacao {
  tipo: string
  lote_id: number
  usuario_id: number
  quantidade?: number | null
  item_ids?: number[] | null
  motivo?: string | null
  observacao?: string | null
  lote_destino_id?: number | null
  localizacao_destino_id?: number | null
  quantidade_destino?: number | null
}

export interface NovoLote {
  produto_id: number
  localizacao_id: number
  data_producao: string | null
  data_validade: string | null
  custo_unitario: number | null
  fornecedor: string | null
  nota_fiscal: string | null
  itens: NovoItem[]
  usuario_id: number
  observacao: string | null
}

export interface AlteracaoDoLote {
  localizacao_id: number
  data_producao: string | null
  custo_unitario: number | null
  fornecedor: string | null
  nota_fiscal: string | null
  data_validade?: string | null
}

export function listarItensDoLote(loteId: number) {
  return apiListAll<ItemLote>(`/api/estoque/lotes/${loteId}/itens`)
}

export function abrirItem(itemId: number) {
  return api(`/api/estoque/itens/${itemId}/abrir`, { method: 'POST' })
}

export function registrarMovimentacao(dados: NovaMovimentacao) {
  return api('/api/estoque/movimentacoes', { method: 'POST', body: JSON.stringify(dados) })
}

export function listarMovimentacoes(loteId?: number) {
  const rota = loteId ? `/api/estoque/movimentacoes?lote_id=${loteId}` : '/api/estoque/movimentacoes'
  return apiListAll<Movimento>(rota)
}

export function criarLote(dados: NovoLote) {
  return api<Lote>('/api/estoque/lotes', { method: 'POST', body: JSON.stringify(dados) })
}

export function atualizarLote(loteId: number, dados: AlteracaoDoLote) {
  return api(`/api/estoque/lotes/${loteId}`, { method: 'PUT', body: JSON.stringify(dados) })
}

export function adicionarItensAoLote(loteId: number, dados: { usuario_id: number; itens: NovoItem[]; observacao: string | null }) {
  return api<ItemLote[]>(`/api/estoque/lotes/${loteId}/itens`, { method: 'POST', body: JSON.stringify(dados) })
}
