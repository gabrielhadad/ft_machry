import { useMemo, useState } from 'react'
import { SearchSelect } from '../../../components/ui'
import type { Lote, Movimento, Produto } from '../../../types'
import { formatarDataHora } from '../../../utils/datas'

const tiposDeMovimento = ['ENTRADA', 'SAIDA', 'AJUSTE_ENTRADA', 'AJUSTE_SAIDA', 'TRANSFERENCIA', 'TRANSFORMACAO']

interface TabelaDeMovimentacoesProps {
  movimentos: Movimento[]
  lotes: Lote[]
  produtos: Produto[]
  erro: string
}

export function TabelaDeMovimentacoes({ movimentos, lotes, produtos, erro }: TabelaDeMovimentacoesProps) {
  const [lote, setLote] = useState('')
  const [tipo, setTipo] = useState('')
  const [produto, setProduto] = useState('')
  const [de, setDe] = useState('')
  const [ate, setAte] = useState('')
  const [usuario, setUsuario] = useState('')

  const lotePorId = useMemo(() => new Map(lotes.map((item) => [item.id, item])), [lotes])
  const produtoPorId = useMemo(() => new Map(produtos.map((item) => [item.id, item])), [produtos])

  const filtrados = useMemo(() => movimentos.filter((movimento) => {
    const dia = movimento.criado_em.slice(0, 10)
    if (lote && movimento.lote_id !== Number(lote)) return false
    if (tipo && movimento.tipo !== tipo) return false
    if (usuario && movimento.usuario_id !== Number(usuario)) return false
    if (produto && lotePorId.get(movimento.lote_id)?.produto_id !== Number(produto)) return false
    if (de && dia < de) return false
    if (ate && dia > ate) return false
    return true
  }), [movimentos, lote, tipo, usuario, produto, de, ate, lotePorId])

  const todos = { value: '', label: 'Todos' }
  const opcoesDeProduto = [todos, ...produtos.map((item) => ({ value: String(item.id), label: item.nome }))]
  const opcoesDeLote = [todos, ...lotes.map((item) => ({ value: String(item.id), label: `#${item.id} — ${item.produto}` }))]
  const opcoesDeTipo = [todos, ...tiposDeMovimento.map((item) => ({ value: item, label: item }))]

  const nomeDoProduto = (movimento: Movimento) => {
    const produtoId = lotePorId.get(movimento.lote_id)?.produto_id ?? 0
    return produtoPorId.get(produtoId)?.nome || '—'
  }

  return <section className="panel">
    <div className="filter-grid">
      <label>
        Produto
        <SearchSelect ariaLabel="Produto" value={produto} onChange={setProduto} options={opcoesDeProduto} />
      </label>
      <label>
        Lote
        <SearchSelect ariaLabel="Lote" value={lote} onChange={setLote} options={opcoesDeLote} />
      </label>
      <label>
        Tipo
        <SearchSelect ariaLabel="Tipo" value={tipo} onChange={setTipo} options={opcoesDeTipo} />
      </label>
      <label>
        ID do usuário
        <input type="number" min="1" value={usuario} onChange={(event) => setUsuario(event.target.value)} placeholder="Todos" />
      </label>
      <label>
        De
        <input type="date" value={de} onChange={(event) => setDe(event.target.value)} />
      </label>
      <label>
        Até
        <input type="date" value={ate} onChange={(event) => setAte(event.target.value)} />
      </label>
    </div>
    {erro && <p className="form-error">{erro}</p>}
    <p className="helper">{filtrados.length} registro(s) exibido(s). Os filtros de data e produto atuam sobre os registros recebidos.</p>
    <div className="table-wrap">
      <table>
        <thead>
          <tr><th>Data</th><th>Tipo</th><th>Produto</th><th>Origem</th><th>Destino</th><th>Quantidade</th><th>Usuário</th><th>Motivo / observação</th></tr>
        </thead>
        <tbody>
          {filtrados.map((movimento) => <tr key={movimento.id}>
            <td>{formatarDataHora(movimento.criado_em)}</td>
            <td>{movimento.tipo.replaceAll('_', ' ')}</td>
            <td>{nomeDoProduto(movimento)}</td>
            <td>#{movimento.lote_id}</td>
            <td>{movimento.lote_destino_id ? `#${movimento.lote_destino_id}` : '—'}</td>
            <td>{movimento.quantidade}{movimento.quantidade_destino ? ` → ${movimento.quantidade_destino}` : ''}</td>
            <td>#{movimento.usuario_id}</td>
            <td>{[movimento.motivo, movimento.observacao].filter(Boolean).join(' · ') || '—'}</td>
          </tr>)}
        </tbody>
      </table>
    </div>
  </section>
}
