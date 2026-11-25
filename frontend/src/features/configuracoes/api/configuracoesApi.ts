import { api } from '../../../services/api'

export type MetodoCustoMedio = 'PONDERADO_SALDO' | 'PONDERADO_MOVEL'

export interface Configuracoes {
  metodo_custo_medio: MetodoCustoMedio
}

export function buscarConfiguracoes() {
  return api<Configuracoes>('/api/configuracoes')
}

export function salvarConfiguracoes(dados: Partial<Configuracoes>) {
  return api<Configuracoes>('/api/configuracoes', { method: 'PUT', body: JSON.stringify(dados) })
}
