import { EmptyState } from '../../../components/ui'
import type { FichaTecnica } from '../../../types'
import { numero } from '../../../utils/formatacao'
import { ativarComTeclado } from '../../../utils/teclado'

const QUANTIDADE_RECENTE = 6

interface FichasRecentesProps {
  fichas: FichaTecnica[]
  canManage: boolean
  onNew: () => void
  onView: (ficha: FichaTecnica) => void
}

export function FichasRecentes({ fichas, canManage, onNew, onView }: FichasRecentesProps) {
  return <section className="panel">
    <div className="panel-title">
      <div>
        <span className="eyebrow">RECEITAS</span>
        <h2>Fichas recentes</h2>
      </div>
      {canManage && <button className="text-button" onClick={onNew}>Adicionar ficha →</button>}
    </div>
    {fichas.length
      ? <div className="recipe-grid">
        {fichas.slice(0, QUANTIDADE_RECENTE).map((ficha) => <article
          className="recipe-card clickable-card"
          key={ficha.id}
          role="button"
          tabIndex={0}
          onClick={() => onView(ficha)}
          onKeyDown={ativarComTeclado(() => onView(ficha))}
        >
          <span className="type">FICHA #{ficha.id}</span>
          <h3>{ficha.produto}</h3>
          <p>{ficha.observacao || 'Receita padronizada para a equipe.'}</p>
          <div>
            <span>{ficha.fases.length} fases</span>
            <span>{ficha.componentes.length} componentes</span>
            <span>{numero.format(ficha.rendimento)} {ficha.unidade_rendimento}</span>
          </div>
          <span className="card-link">Ver ficha completa →</span>
        </article>)}
      </div>
      : <EmptyState title="Nenhuma ficha cadastrada" text="Cadastre a primeira receita para padronizar o preparo." />}
  </section>
}
