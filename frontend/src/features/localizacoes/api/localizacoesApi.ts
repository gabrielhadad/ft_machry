import { api } from '../../../services/api'
import type { Conservacao } from '../../../types'

export interface DadosDaLocalizacao {
  nome: string
  tipo: Conservacao
  parent_id: number | null
}

export function criarLocalizacao(dados: DadosDaLocalizacao) {
  return api('/api/estoque/localizacoes', { method: 'POST', body: JSON.stringify(dados) })
}

export function atualizarLocalizacao(id: number, dados: DadosDaLocalizacao) {
  return api(`/api/estoque/localizacoes/${id}`, { method: 'PUT', body: JSON.stringify(dados) })
}

export function excluirLocalizacao(id: number) {
  return api(`/api/estoque/localizacoes/${id}`, { method: 'DELETE' })
}
