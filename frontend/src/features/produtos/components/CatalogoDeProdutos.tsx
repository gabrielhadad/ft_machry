import { useMemo, useState } from 'react'
import { EmptyState, Pagination, SearchSelect } from '../../../components/ui'
import type { Produto, TipoProduto } from '../../../types'
import { normalizeSearch } from '../../../utils/texto'
import { tipoProdutoLabels } from '../rotulos'

type FiltroDeTipo = TipoProduto | 'TODOS'

const POR_PAGINA = 20

const abas: Array<[FiltroDeTipo, string]> = [
  ['TODOS', 'Todos'],
  ['INSUMO', 'Insumos'],
  ['INTERMEDIARIO', 'Intermediários'],
  ['FINAL', 'Produtos finais'],
]

export function CatalogoDeProdutos({ produtos, onEdit }: { produtos: Produto[]; onEdit: (produto: Produto) => void }) {
  const [query, setQuery] = useState('')
  const [tipo, setTipo] = useState<FiltroDeTipo>('TODOS')
  const [subdivisao, setSubdivisao] = useState('')
  const [pagina, setPagina] = useState(1)

  const counts = useMemo(() => ({
    TODOS: produtos.length,
    INSUMO: produtos.filter((item) => item.tipo === 'INSUMO').length,
    INTERMEDIARIO: produtos.filter((item) => item.tipo === 'INTERMEDIARIO').length,
    FINAL: produtos.filter((item) => item.tipo === 'FINAL').length,
  }), [produtos])

  const subdivisoes = useMemo(() => [...new Set(produtos
    .filter((item) => tipo === 'TODOS' || item.tipo === tipo)
    .map((item) => item.subdivisao?.trim())
    .filter((value): value is string => Boolean(value)))]
    .sort((a, b) => a.localeCompare(b, 'pt-BR')), [produtos, tipo])

  const filtered = useMemo(() => {
    const search = normalizeSearch(query)
    return produtos.filter((item) => {
      if (tipo !== 'TODOS' && item.tipo !== tipo) return false
      if (subdivisao && item.subdivisao !== subdivisao) return false
      return !search || normalizeSearch(`${item.nome} ${item.subdivisao ?? ''} ${item.unidade_medida}`).includes(search)
    }).sort((a, b) => a.nome.localeCompare(b.nome, 'pt-BR'))
  }, [produtos, tipo, subdivisao, query])

  const totalPaginas = Math.max(1, Math.ceil(filtered.length / POR_PAGINA))
  const paginaAtual = Math.min(pagina, totalPaginas)
  const visiveis = filtered.slice((paginaAtual - 1) * POR_PAGINA, paginaAtual * POR_PAGINA)

  const alterarTipo = (novo: FiltroDeTipo) => {
    setTipo(novo)
    setSubdivisao('')
    setPagina(1)
  }

  return <section className="panel catalog-panel">
    <div className="catalog-tabs" role="group" aria-label="Tipo de produto">
      {abas.map(([value, label]) => (
        <button key={value} type="button" aria-pressed={tipo === value} className={tipo === value ? 'active' : ''} onClick={() => alterarTipo(value)}>
          {label}<span>{counts[value]}</span>
        </button>
      ))}
    </div>
    <div className="catalog-filters">
      <label>
        Pesquisar produto
        <input value={query} onChange={(event) => { setQuery(event.target.value); setPagina(1) }} placeholder="Nome, subdivisão ou unidade" />
      </label>
      <label>
        Subdivisão
        <SearchSelect
          ariaLabel="Subdivisão"
          value={subdivisao}
          onChange={(value) => { setSubdivisao(value); setPagina(1) }}
          options={[{ value: '', label: 'Todas' }, ...subdivisoes.map((value) => ({ value, label: value }))]}
        />
      </label>
      <span className="catalog-total" aria-live="polite">{filtered.length} produto(s)</span>
    </div>
    <div className="table-wrap">
      <table>
        <thead>
          <tr><th>Produto</th><th>Tipo</th><th>Subdivisão</th><th>Unidade</th><th>Conservação</th><th>Validade padrão</th><th>Ação</th></tr>
        </thead>
        <tbody>
          {visiveis.map((produto) => <tr key={produto.id}>
            <td><strong>{produto.nome}</strong><small className="catalog-id">#{produto.id}</small></td>
            <td><span className={`badge ${produto.tipo.toLowerCase()}`}>{tipoProdutoLabels[produto.tipo]}</span></td>
            <td>{produto.subdivisao || '—'}</td>
            <td>{produto.unidade_medida}</td>
            <td>{produto.conservacao.toLowerCase()}</td>
            <td>{produto.validade_padrao_dias == null ? '—' : `${produto.validade_padrao_dias} dias`}</td>
            <td><button className="text-button" onClick={() => onEdit(produto)}>Editar</button></td>
          </tr>)}
        </tbody>
      </table>
    </div>
    {!filtered.length && <EmptyState title="Nenhum produto encontrado" text={produtos.length ? 'Ajuste a busca, a categoria ou a subdivisão.' : 'Cadastre o primeiro produto para começar.'} />}
    <Pagination page={paginaAtual} perPage={POR_PAGINA} total={filtered.length} label="Paginação de produtos" onChange={setPagina} />
  </section>
}
