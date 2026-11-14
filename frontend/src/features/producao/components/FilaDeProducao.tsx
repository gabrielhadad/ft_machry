import { EmptyState } from '../../../components/ui'
import type { FichaTecnica, SolicitacaoProducao } from '../../../types'
import { formatarData } from '../../../utils/datas'
import { numero } from '../../../utils/formatacao'

const statusQuePodemIniciar = ['ABERTA', 'EM_SEPARACAO']

interface FilaDeProducaoProps {
  solicitacoes: SolicitacaoProducao[]
  fichas: FichaTecnica[]
  ocupado: boolean
  onStatus: (id: number, status: string) => Promise<void>
  onViewSheet: (ficha: FichaTecnica) => void
}

export function FilaDeProducao({ solicitacoes, fichas, ocupado, onStatus, onViewSheet }: FilaDeProducaoProps) {
  const fichaPorId = new Map(fichas.map((ficha) => [ficha.id, ficha]))

  const acaoDa = (item: SolicitacaoProducao) => {
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
          <tr><th>Solicitação</th><th>Produto</th><th>Quantidade</th><th>Status</th><th>Criada em</th><th>Concluída em</th><th>Ação</th></tr>
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
              <td>{acaoDa(item)}</td>
            </tr>
          })}
        </tbody>
      </table>
    </div>
    {!solicitacoes.length && <EmptyState title="Nenhum preparo na fila" text="O gestor ainda não definiu a produção." />}
  </section>
}
