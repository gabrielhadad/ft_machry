import type { StatusItem } from '../../types'

export const statusLabels: Record<StatusItem, string> = {
  DISPONIVEL: 'Disponível',
  RESERVADA: 'Reservada',
  EM_USO: 'Em uso',
  CONSUMIDA: 'Consumida',
}

export const movimentoLabels: Record<string, string> = {
  ENTRADA: 'Entrada',
  SAIDA: 'Saída',
  PRODUCAO: 'Produção',
  CONSUMO_PRODUCAO: 'Consumo na produção',
  TRANSFERENCIA: 'Transferência',
  TRANSFORMACAO: 'Transformação',
  AJUSTE_ENTRADA: 'Ajuste de entrada',
  AJUSTE_SAIDA: 'Ajuste de saída',
}
