import { useMemo, useState } from 'react'
import { EmptyState, Pagination, SearchSelect } from '../../../components/ui'
import type { FichaTecnica } from '../../../types'
import { numero } from '../../../utils/formatacao'
import { ativarComTeclado } from '../../../utils/teclado'
import { normalizeSearch } from '../../../utils/texto'

const POR_PAGINA = 12

type Ordem = 'nome' | 'nome-desc' | 'recentes' | 'antigas' | 'tempo' | 'tempo-desc' | 'componentes' | 'rendimento-desc'

const ordens: Array<[Ordem, string]> = [
  ['nome', 'Nome (A–Z)'],
  ['nome-desc', 'Nome (Z–A)'],
  ['recentes', 'Mais recentes'],
  ['antigas', 'Mais antigas'],
  ['tempo', 'Menor tempo total'],
  ['tempo-desc', 'Maior tempo total'],
  ['componentes', 'Mais componentes'],
  ['rendimento-desc', 'Maior rendimento'],
]

const tempoTotal = (ficha: FichaTecnica) => ficha.fases.reduce((total, fase) => total + fase.tempo_previsto_min, 0)
const porNome = (a: FichaTecnica, b: FichaTecnica) => a.produto.localeCompare(b.produto, 'pt-BR')

const comparadores: Record<Ordem, (a: FichaTecnica, b: FichaTecnica) => number> = {
  nome: porNome,
  'nome-desc': (a, b) => porNome(b, a),
  recentes: (a, b) => b.id - a.id,
  antigas: (a, b) => a.id - b.id,
  tempo: (a, b) => tempoTotal(a) - tempoTotal(b) || porNome(a, b),
  'tempo-desc': (a, b) => tempoTotal(b) - tempoTotal(a) || porNome(a, b),
  componentes: (a, b) => b.componentes.length - a.componentes.length || porNome(a, b),
  'rendimento-desc': (a, b) => b.rendimento - a.rendimento || porNome(a, b),
}

function textoDeBusca(ficha: FichaTecnica) {
  return normalizeSearch([
    `#${ficha.id}`,
    ficha.produto,
    ficha.observacao ?? '',
    ...ficha.componentes.map((item) => item.produto),
    ...ficha.fases.map((fase) => fase.fase),
  ].join(' '))
}

function opcoesUnicas(valores: Array<[number, string]>) {
  const mapa = new Map(valores)
  return [...mapa].map(([value, label]) => ({ value, label })).sort((a, b) => a.label.localeCompare(b.label, 'pt-BR'))
}

export function GradeDeFichas({ fichas, onView }: { fichas: FichaTecnica[]; onView: (ficha: FichaTecnica) => void }) {
  const [busca, setBusca] = useState('')
  const [componente, setComponente] = useState(0)
  const [fase, setFase] = useState(0)
  const [ordem, setOrdem] = useState<Ordem>('nome')
  const [pagina, setPagina] = useState(1)

  const componentes = useMemo(() => opcoesUnicas(
    fichas.flatMap((ficha) => ficha.componentes.map((item): [number, string] => [item.produto_id, item.produto])),
  ), [fichas])
  const fases = useMemo(() => opcoesUnicas(
    fichas.flatMap((ficha) => ficha.fases.map((item): [number, string] => [item.fase_id, item.fase])),
  ), [fichas])
  const indice = useMemo(() => new Map(fichas.map((ficha) => [ficha.id, textoDeBusca(ficha)])), [fichas])

  const filtradas = useMemo(() => {
    const termos = normalizeSearch(busca).split(/\s+/).filter(Boolean)
    return fichas.filter((ficha) => {
      if (componente && !ficha.componentes.some((item) => item.produto_id === componente)) return false
      if (fase && !ficha.fases.some((item) => item.fase_id === fase)) return false
      const texto = indice.get(ficha.id) ?? ''
      return termos.every((termo) => texto.includes(termo))
    }).sort(comparadores[ordem])
  }, [fichas, indice, busca, componente, fase, ordem])

  const totalPaginas = Math.max(1, Math.ceil(filtradas.length / POR_PAGINA))
  const paginaAtual = Math.min(pagina, totalPaginas)
  const visiveis = filtradas.slice((paginaAtual - 1) * POR_PAGINA, paginaAtual * POR_PAGINA)
  const temFiltro = Boolean(busca.trim() || componente || fase)

  const mudarPagina = (valor: number) => {
    setPagina(valor)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
  const filtrar = <T,>(definir: (valor: T) => void) => (valor: T) => {
    definir(valor)
    setPagina(1)
  }
  const limpar = () => {
    setBusca('')
    setComponente(0)
    setFase(0)
    setPagina(1)
  }

  if (!fichas.length) {
    return <section className="panel">
      <EmptyState title="Nenhuma ficha cadastrada" text="Crie a primeira ficha técnica da cozinha." />
    </section>
  }

  return <>
    <section className="panel recipe-filters-panel">
      <div className="catalog-filters recipe-filters">
        <label className="recipe-filter-search">
          Pesquisar
          <input
            type="search"
            value={busca}
            onChange={(event) => filtrar(setBusca)(event.target.value)}
            placeholder="Nome, ingrediente, etapa, observação ou #id"
          />
        </label>
        <label>
          Contém ingrediente ou preparo
          <SearchSelect
            ariaLabel="Contém ingrediente ou preparo"
            value={componente}
            onChange={filtrar(setComponente)}
            options={[{ value: 0, label: 'Todos' }, ...componentes]}
          />
        </label>
        <label>
          Etapa
          <SearchSelect
            ariaLabel="Etapa"
            value={fase}
            onChange={filtrar(setFase)}
            options={[{ value: 0, label: 'Todas' }, ...fases]}
          />
        </label>
        <label>
          Ordenar por
          <select value={ordem} onChange={(event) => filtrar(setOrdem)(event.target.value as Ordem)}>
            {ordens.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
        </label>
        {temFiltro && <button type="button" className="secondary outline" onClick={limpar}>Limpar filtros</button>}
        <span className="catalog-total" aria-live="polite">{filtradas.length} de {fichas.length} ficha(s)</span>
      </div>
    </section>

    {!filtradas.length
      ? <section className="panel">
        <EmptyState title="Nenhuma ficha encontrada" text="Ajuste a pesquisa ou limpe os filtros." />
      </section>
      : <div className="recipe-grid">
        {visiveis.map((ficha) => <article
          className="recipe-card panel clickable-card"
          key={ficha.id}
          role="button"
          tabIndex={0}
          onClick={() => onView(ficha)}
          onKeyDown={ativarComTeclado(() => onView(ficha))}
        >
          <span className="type">#{ficha.id}</span>
          <h3>{ficha.produto}</h3>
          <p title={ficha.observacao || undefined}>{ficha.observacao || 'Sem observações.'}</p>
          <div>
            <span>{numero.format(ficha.rendimento)} {ficha.unidade_rendimento}</span>
            <span>{ficha.fases.length} fases</span>
            <span>{tempoTotal(ficha)} min</span>
          </div>
          <ol className="phase-list">
            {ficha.fases.map((item) => <li key={item.id}>
              <span>{item.ordem}</span>
              {item.fase}
              <small>{item.tempo_previsto_min} min</small>
            </li>)}
          </ol>
          <span className="card-link">Ver ficha completa →</span>
        </article>)}
      </div>}
    <Pagination page={paginaAtual} perPage={POR_PAGINA} total={filtradas.length} label="Paginação de fichas técnicas" onChange={mudarPagina} />
  </>
}
