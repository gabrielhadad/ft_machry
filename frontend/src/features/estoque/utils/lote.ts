import type { ItemLote, Localizacao, Lote } from '../../../types'
import { DIA_MS, diasAte, formatarDiaMes, inicioDoDia, paraData } from '../../../utils/datas'
import type { Situacao } from '../types'

export const DIAS_ATENCAO = 10

export const dataEntrada = (lote: Lote) => lote.data_producao ?? lote.criado_em

export const temItens = (lote: Lote) => lote.itens_total > 0

export const itensAtivos = (lote: Lote) => lote.itens_total - lote.itens_consumidos - lote.itens_vencidos

export const itemVencido = (item: ItemLote) => item.status !== 'CONSUMIDA' && (diasAte(item.data_validade) ?? 0) < 0

export function situacaoDo(lote: Lote): { tipo: Situacao; texto: string } {
  if (lote.quantidade <= 0) return { tipo: 'ESGOTADO', texto: 'Esgotado' }
  const dias = diasAte(lote.data_validade)
  if (dias === null) return { tipo: 'SEM_VALIDADE', texto: 'Sem validade' }
  if (dias < 0) return { tipo: 'VENCIDO', texto: `Vencido há ${-dias} ${-dias === 1 ? 'dia' : 'dias'}` }
  if (dias === 0) return { tipo: 'ATENCAO', texto: 'Vence hoje' }
  if (dias <= DIAS_ATENCAO) return { tipo: 'ATENCAO', texto: `Atenção · ${dias} ${dias === 1 ? 'dia' : 'dias'}` }
  return { tipo: 'EM_DIA', texto: `Em dia · ${dias} dias` }
}

export function caminhoLocalizacao(id: number, porId: Map<number, Localizacao>, fallback: string) {
  const partes: string[] = []
  const visitados = new Set<number>()
  let atual = porId.get(id)
  while (atual && !visitados.has(atual.id)) {
    visitados.add(atual.id)
    partes.unshift(atual.nome)
    atual = atual.parent_id ? porId.get(atual.parent_id) : undefined
  }
  return partes.length ? partes.join(' · ') : fallback
}

export function ordemDeUso(a: ItemLote, b: ItemLote) {
  if (a.status !== b.status && (a.status === 'EM_USO' || b.status === 'EM_USO')) return a.status === 'EM_USO' ? -1 : 1
  const validadeA = a.data_validade ?? '9999-12-31'
  const validadeB = b.data_validade ?? '9999-12-31'
  return validadeA.localeCompare(validadeB) || a.codigo.localeCompare(b.codigo)
}

export function vidaUtil(lote: Lote) {
  const inicio = paraData(dataEntrada(lote))
  const fim = paraData(lote.data_validade)
  if (!inicio || !fim) return null
  const total = Math.max(1, Math.round((inicioDoDia(fim) - inicioDoDia(inicio)) / DIA_MS))
  const decorridos = Math.min(total, Math.max(0, Math.round((inicioDoDia(new Date()) - inicioDoDia(inicio)) / DIA_MS)))
  return { total, decorridos }
}

export function destinoDoItem(item: ItemLote) {
  if (item.status === 'EM_USO') return item.aberto_em ? `Aberta em ${formatarDiaMes(item.aberto_em)}` : 'Aberta'
  if (item.status === 'RESERVADA') return item.solicitacao_producao_id ? `Produção #${item.solicitacao_producao_id}` : 'Reservada'
  if (item.status === 'CONSUMIDA') return 'Consumida'
  return '—'
}
