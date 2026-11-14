import { Metric } from '../../../components/ui'
import type { SolicitacaoProducao } from '../../../types'

const statusFinais = ['CONCLUIDA', 'CANCELADA']

export function MetricasDeProducao({ solicitacoes }: { solicitacoes: SolicitacaoProducao[] }) {
  const emAndamento = solicitacoes.filter((item) => !statusFinais.includes(item.status)).length
  const concluidas = solicitacoes.filter((item) => item.status === 'CONCLUIDA').length
  return <section className="metrics">
    <Metric label="SOLICITAÇÕES" value={solicitacoes.length} detail="total registrado" />
    <Metric label="EM ANDAMENTO" value={emAndamento} detail="aguardando conclusão" />
    <Metric label="CONCLUÍDAS" value={concluidas} detail="produções finalizadas" />
  </section>
}
