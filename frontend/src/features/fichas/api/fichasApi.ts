import { api } from '../../../services/api'

export interface DadosDaFicha {
  produto_id: number
  rendimento: number
  observacao: string | null
  fases: { fase_id: number; ordem: number; tempo_previsto_min: number }[]
  componentes: { produto_id: number; quantidade: number; fase_ordem: number | null }[]
}

export interface ResultadoDaImportacaoDeFichas {
  total: number
  fases_criadas: string[]
  ignoradas: string[]
}

export function criarFicha(dados: DadosDaFicha) {
  return api('/api/fichas-tecnicas', { method: 'POST', body: JSON.stringify(dados) })
}

export function atualizarFicha(id: number, dados: DadosDaFicha) {
  return api(`/api/fichas-tecnicas/${id}`, { method: 'PUT', body: JSON.stringify(dados) })
}

export function excluirFicha(id: number) {
  return api(`/api/fichas-tecnicas/${id}`, { method: 'DELETE' })
}

export function importarFichas(fichas: unknown[]) {
  return api<ResultadoDaImportacaoDeFichas>('/api/fichas-tecnicas/lote', { method: 'POST', body: JSON.stringify({ fichas }) })
}
