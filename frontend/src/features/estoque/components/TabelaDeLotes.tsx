import { useState } from 'react'
import { EmptyState, SearchSelect } from '../../../components/ui'
import type { Lote, TipoProduto } from '../../../types'
import { formatarData } from '../../../utils/datas'
import { normalizeSearch } from '../../../utils/texto'
import { tipoProdutoLabels } from '../../produtos'
import type { Contexto, FiltroSituacao } from '../types'
import { caminhoLocalizacao, dataEntrada, situacaoDo } from '../utils/lote'
import { ResumoItens } from './ResumoItens'

type FiltroDeTipo = TipoProduto | 'TODOS'

const abasDeTipo: Array<[FiltroDeTipo, string]> = [
  ['TODOS', 'Todos'],
  ['INSUMO', 'Insumos'],
  ['INTERMEDIARIO', 'Intermediários'],
  ['FINAL', 'Produtos finais'],
]

const opcoesDeSituacao: { value: FiltroSituacao; label: string }[] = [
  { value: 'TODAS', label: 'Todas' },
  { value: 'EM_DIA', label: 'Em dia' },
  { value: 'ATENCAO', label: 'Atenção' },
  { value: 'VENCIDO', label: 'Vencidos' },
  { value: 'SEM_VALIDADE', label: 'Sem validade' },
  { value: 'ESGOTADO', label: 'Esgotados' },
]

interface TabelaDeLotesProps {
  lotes: Lote[]
  contexto: Contexto
  onVerItens: (loteId: number) => void
}

export function TabelaDeLotes({ lotes, contexto, onVerItens }: TabelaDeLotesProps) {
  const [tipo, setTipo] = useState<FiltroDeTipo>('TODOS')
  const [situacao, setSituacao] = useState<FiltroSituacao>('TODAS')
  const [busca, setBusca] = useState('')

  const situacoes = new Map(lotes.map((lote) => [lote.id, situacaoDo(lote)]))
  const termo = normalizeSearch(busca).replace(/^#/, '')
  const visiveis = lotes
    .filter((lote) => situacao === 'ESGOTADO' ? lote.quantidade <= 0 : lote.quantidade > 0)
    .filter((lote) => situacao === 'TODAS' || situacao === 'ESGOTADO' || situacoes.get(lote.id)?.tipo === situacao)
    .filter((lote) => tipo === 'TODOS' || contexto.produtosPorId.get(lote.produto_id)?.tipo === tipo)
    .filter((lote) => !termo || String(lote.id) === termo || normalizeSearch(lote.produto).includes(termo))
    .sort((a, b) => (a.data_validade ?? '9999').localeCompare(b.data_validade ?? '9999') || a.id - b.id)

  return <section className="panel">
    <div className="stock-toolbar">
      <div className="stock-tabs">
        {abasDeTipo.map(([valor, label]) =>
          <button type="button" className={tipo === valor ? 'active' : ''} onClick={() => setTipo(valor)} key={valor}>{label}</button>)}
      </div>
      <div className="stock-filters">
        <label>
          Situação
          <SearchSelect<FiltroSituacao> ariaLabel="Situação" value={situacao} onChange={setSituacao} options={opcoesDeSituacao} />
        </label>
        <input value={busca} onChange={(event) => setBusca(event.target.value)} placeholder="Buscar lote ou produto" aria-label="Buscar lote ou produto" />
      </div>
    </div>

    <div className="table-wrap">
      <table className="stock-table">
        <thead>
          <tr><th>Lote</th><th>Produto</th><th>Tipo</th><th>Itens</th><th>Entrada</th><th>Vencimento</th><th>Localização</th><th>Situação</th><th /></tr>
        </thead>
        <tbody>
          {visiveis.map((lote) => {
            const produto = contexto.produtosPorId.get(lote.produto_id)
            const sit = situacoes.get(lote.id)!
            return <tr key={lote.id} className={`row-${sit.tipo.toLowerCase()}`}>
              <td><strong>#{lote.id}</strong></td>
              <td>{lote.produto}</td>
              <td>{produto && <span className={`badge ${produto.tipo.toLowerCase()}`}>{tipoProdutoLabels[produto.tipo]}</span>}</td>
              <td><ResumoItens lote={lote} unidade={produto?.unidade_medida ?? ''} vencido={sit.tipo === 'VENCIDO'} /></td>
              <td>{formatarData(dataEntrada(lote))}</td>
              <td><strong>{formatarData(lote.data_validade)}</strong></td>
              <td>{caminhoLocalizacao(lote.localizacao_id, contexto.locaisPorId, lote.localizacao)}</td>
              <td><span className={`pill ${sit.tipo.toLowerCase()}`}>{sit.texto}</span></td>
              <td><button className="secondary outline small" type="button" onClick={() => onVerItens(lote.id)}>Ver itens</button></td>
            </tr>
          })}
        </tbody>
      </table>
    </div>
    {!visiveis.length && <EmptyState title="Nenhum lote encontrado" text="Ajuste os filtros ou cadastre um novo lote." />}
    <div className="stock-legend">
      <span><i className="disponivel" />Disponível</span>
      <span><i className="reservada" />Reservado</span>
      <span><i className="em_uso" />Em uso</span>
      <span><i className="consumida" />Consumido</span>
      <span><i className="vencido" />Vencido</span>
    </div>
  </section>
}
