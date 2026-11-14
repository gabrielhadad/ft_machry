import { Metric } from '../../../components/ui'
import type { Lote } from '../../../types'
import type { Situacao } from '../types'
import { DIAS_ATENCAO, itensAtivos, situacaoDo } from '../utils/lote'

export function MetricasDeEstoque({ lotes }: { lotes: Lote[] }) {
  const comSaldo = lotes.filter((lote) => lote.quantidade > 0)
  const contar = (alvo: Situacao) => comSaldo.filter((lote) => situacaoDo(lote).tipo === alvo).length
  const emAtencao = contar('ATENCAO')
  const vencidos = contar('VENCIDO')
  const lotesAtivos = comSaldo.length - vencidos
  const unidadesCadastradas = comSaldo.reduce((total, lote) => total + itensAtivos(lote), 0)

  return <section className="metrics four">
    <Metric label="LOTES ATIVOS" value={lotesAtivos} detail="com saldo disponível e dentro de validade" />
    <Metric label="UNIDADES CADASTRADAS" value={unidadesCadastradas} detail="itens rastreados individualmente" />
    <article className="metric warning">
      <span>ATENÇÃO À VALIDADE</span>
      <strong>{emAtencao}</strong>
      <small>{emAtencao === 1 ? 'lote vence' : 'lotes vencem'} em até {DIAS_ATENCAO} dias</small>
    </article>
    <article className="metric danger">
      <span>VENCIDOS</span>
      <strong>{vencidos}</strong>
      <small>{vencidos === 1 ? 'lote' : 'lotes'} para descarte</small>
    </article>
  </section>
}
