import { EmptyState } from '../../../components/ui'
import type { FichaTecnica, SolicitacaoProducao } from '../../../types'
import { formatarData } from '../../../utils/datas'
import { moeda, numero } from '../../../utils/formatacao'

const statusQuePodemIniciar = ['ABERTA', 'EM_SEPARACAO']

/** Custo gravado na conclusão, com o custo dos lotes naquele momento. */
function custoReal(item: SolicitacaoProducao, unidade?: string) {
  if (item.custo_total_realizado == null) return '—'
  const incompleto = item.custo_realizado_completo === false
  return <span title={incompleto ? 'Algum lote consumido não tinha custo; o valor cobre só a parte conhecida' : undefined}>
    {moeda.format(item.custo_total_realizado)}{incompleto ? '*' : ''}
    {item.custo_unitario_realizado != null && <small className="custo-por-unidade">
      {moeda.format(item.custo_unitario_realizado)}/{unidade ?? 'un'}
    </small>}
  </span>
}

interface FilaDeProducaoProps {
  solicitacoes: SolicitacaoProducao[]
  fichas: FichaTecnica[]
  ocupado: boolean
  podeAtualizar: boolean
  mostrarCusto: boolean
  onStatus: (id: number, status: string) => Promise<void>
  onViewSheet: (ficha: FichaTecnica) => void
}

export function FilaDeProducao({
  solicitacoes,
  fichas,
  ocupado,
  podeAtualizar,
  mostrarCusto,
  onStatus,
  onViewSheet,
}: FilaDeProducaoProps) {
  const fichaPorId = new Map(fichas.map((ficha) => [ficha.id, ficha]))

  const acaoDa = (item: SolicitacaoProducao) => {
    if (!podeAtualizar) return '—'
    if (statusQuePodemIniciar.includes(item.status)) {
      return <button className="text-button" disabled={ocupado} onClick={() => void onStatus(item.id, 'EM_PRODUCAO')}>Iniciar</button>
    }
    if (item.status === 'EM_PRODUCAO') {
      return <button className="text-button" disabled={ocupado} onClick={() => void onStatus(item.id, 'CONCLUIDA')}>Concluir</button>
    }
    return '—'
  }

  return <section className="panel">
    <div className="table-wrap">
      <table>
        <thead>
          <tr><th>Solicitação</th><th>Produto</th><th>Quantidade</th><th>Status</th><th>Criada em</th><th>Concluída em</th>{mostrarCusto && <th>Custo real</th>}<th>Ação</th></tr>
        </thead>
        <tbody>
          {solicitacoes.map((item) => {
            const ficha = fichaPorId.get(item.ficha_tecnica_id)
            return <tr key={item.id}>
              <td>#{item.id}</td>
              <td>{ficha
                ? <button className="text-button sheet-link" onClick={() => onViewSheet(ficha)}>{ficha.produto}</button>
                : <strong>Ficha #{item.ficha_tecnica_id}</strong>}</td>
              <td>{numero.format(item.quantidade_planejada)} {ficha?.unidade_rendimento ?? ''}</td>
              <td><span className={`badge status-${item.status.toLowerCase()}`}>{item.status.replaceAll('_', ' ')}</span></td>
              <td>{formatarData(item.criado_em)}</td>
              <td>{formatarData(item.concluido_em)}</td>
              {mostrarCusto && <td>{custoReal(item, ficha?.unidade_rendimento)}</td>}
              <td>{acaoDa(item)}</td>
            </tr>
          })}
        </tbody>
      </table>
    </div>
    {!solicitacoes.length && <EmptyState title="Nenhum preparo na fila" text="O gestor ainda não definiu a produção." />}
  </section>
}
