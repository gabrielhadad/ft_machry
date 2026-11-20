import { api, apiListAll } from '../../../services/api'
import type { CozinheiroResumo, Praca } from '../../../types'

export interface NovaPraca {
  nome: string
  descricao: string | null
  cozinheiros: number[]
}

export type AlteracaoDePraca = Partial<NovaPraca> & { ativo?: number }

export function listarCozinheiros() {
  return apiListAll<CozinheiroResumo>('/api/pracas/cozinheiros')
}

export function criarPraca(dados: NovaPraca) {
  return api<Praca>('/api/pracas', { method: 'POST', body: JSON.stringify(dados) })
}

export function atualizarPraca(id: number, dados: AlteracaoDePraca) {
  return api<Praca>(`/api/pracas/${id}`, { method: 'PUT', body: JSON.stringify(dados) })
}

export function desativarPraca(id: number) {
  return api<void>(`/api/pracas/${id}`, { method: 'DELETE' })
}
