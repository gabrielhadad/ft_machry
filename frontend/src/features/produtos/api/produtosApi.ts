import { api } from '../../../services/api'
import type { Conservacao, TipoProduto } from '../../../types'

export interface DadosDoProduto {
  nome: string
  tipo: TipoProduto
  unidade_medida: string
  subdivisao: string | null
  conservacao: Conservacao
  validade_obrigatoria: number
  validade_padrao_dias: number | null
}

export interface ResultadoDaImportacaoDeProdutos {
  total: number
  ignorados: string[]
}

export function criarProduto(dados: DadosDoProduto) {
  return api('/api/produtos', { method: 'POST', body: JSON.stringify(dados) })
}

export function atualizarProduto(id: number, dados: DadosDoProduto) {
  return api(`/api/produtos/${id}`, { method: 'PUT', body: JSON.stringify(dados) })
}

export function excluirProduto(id: number) {
  return api(`/api/produtos/${id}`, { method: 'DELETE' })
}

export function importarProdutos(produtos: Record<string, unknown>[]) {
  return api<ResultadoDaImportacaoDeProdutos>('/api/produtos/lote', { method: 'POST', body: JSON.stringify({ produtos }) })
}
