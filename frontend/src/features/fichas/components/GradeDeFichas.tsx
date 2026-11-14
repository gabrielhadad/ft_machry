import { useState } from 'react'
import { EmptyState, Pagination } from '../../../components/ui'
import type { FichaTecnica } from '../../../types'
import { numero } from '../../../utils/formatacao'
import { ativarComTeclado } from '../../../utils/teclado'

const POR_PAGINA = 12

export function GradeDeFichas({ fichas, onView }: { fichas: FichaTecnica[]; onView: (ficha: FichaTecnica) => void }) {
  const [pagina, setPagina] = useState(1)
  const totalPaginas = Math.max(1, Math.ceil(fichas.length / POR_PAGINA))
  const paginaAtual = Math.min(pagina, totalPaginas)
  const visiveis = fichas.slice((paginaAtual - 1) * POR_PAGINA, paginaAtual * POR_PAGINA)

  const mudarPagina = (valor: number) => {
    setPagina(valor)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  if (!fichas.length) {
    return <section className="panel">
      <EmptyState title="Nenhuma ficha cadastrada" text="Crie a primeira ficha técnica da cozinha." />
    </section>
  }

  return <>
    <div className="recipe-grid">
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
        </div>
        <ol className="phase-list">
          {ficha.fases.map((fase) => <li key={fase.id}>
            <span>{fase.ordem}</span>
            {fase.fase}
            <small>{fase.tempo_previsto_min} min</small>
          </li>)}
        </ol>
        <span className="card-link">Ver ficha completa →</span>
      </article>)}
    </div>
    <Pagination page={paginaAtual} perPage={POR_PAGINA} total={fichas.length} label="Paginação de fichas técnicas" onChange={mudarPagina} />
  </>
}
