import { api } from '../../../services/api'

export interface NovaSolicitacao {
  ficha_tecnica_id: number
  quantidade_planejada: number
  localizacao_destino_id: number
  praca_id?: number | null
}

export function criarSolicitacao(dados: NovaSolicitacao) {
  return api('/api/producao/solicitacoes', { method: 'POST', body: JSON.stringify(dados) })
}

export function alterarStatusDaSolicitacao(id: number, status: string) {
  return api(`/api/producao/solicitacoes/${id}/status`, { method: 'PUT', body: JSON.stringify({ status }) })
}

export function alterarPracaDaSolicitacao(id: number, pracaId: number | null) {
  return api(`/api/producao/solicitacoes/${id}/praca`, {
    method: 'PUT',
    body: JSON.stringify({ praca_id: pracaId }),
  })
}
