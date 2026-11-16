import type { FichaTecnica } from '../../../types'
import { numero } from '../../../utils/formatacao'
import { BrandMark, useBranding } from '../../branding'
import { useUsuarios } from '../../usuarios'
import { PhaseAssignee } from './PhaseAssignee'
import { PhaseTimer } from './Phasetimer'

export function SheetDocument({ ficha }: { ficha: FichaTecnica }) {
  const branding = useBranding()
  const { usuarios } = useUsuarios(0)
  const fases = [...ficha.fases].sort((a, b) => a.ordem - b.ordem)
  const semEtapa = ficha.componentes.filter((item) => item.fase_ordem == null)
  const tempoTotal = fases.reduce((total, fase) => total + fase.tempo_previsto_min, 0)

  return <article className="sheet-document">
    <header className="sheet-document-head">
      <BrandMark className="sheet-brand-mark" variant="print" />
      <strong>FICHA TÉCNICA #{ficha.id}</strong>
    </header>
    <div className="sheet-title-block">
      <span className="eyebrow">RECEITA PADRONIZADA</span>
      <h1>{ficha.produto}</h1>
      <div className="sheet-summary">
        <span>Rendimento</span>
        <strong>{numero.format(ficha.rendimento)} {ficha.unidade_rendimento}</strong>
        <span>Tempo total</span>
        <strong>{tempoTotal} min</strong>
      </div>
    </div>
    <section className="sheet-section">
      <h2>Componentes</h2>
      <table>
        <thead>
          <tr><th>Ingrediente ou preparo</th><th>Quantidade</th><th>Etapa</th></tr>
        </thead>
        <tbody>
          {ficha.componentes.map((item) => <tr key={item.id}>
            <td>{item.produto}</td>
            <td>{numero.format(item.quantidade)} {item.unidade_medida}</td>
            <td>{item.fase_ordem == null ? 'Geral' : `Etapa ${item.fase_ordem}`}</td>
          </tr>)}
        </tbody>
      </table>
    </section>
    <section className="sheet-section">
      <h2>Modo de preparo</h2>
      <ol className="sheet-steps">
        {fases.map((fase) => {
          const componentes = ficha.componentes.filter((item) => item.fase_ordem === fase.ordem)
          return <li key={fase.id}>
            <span>{fase.ordem}</span>
            <div>
              <h3>
                {fase.fase}
                <div className="phase-controls">
                  <PhaseAssignee timerId={`${ficha.id}-${fase.id}`} usuarios={usuarios} />
                  <PhaseTimer
                    key={`${ficha.id}-${fase.id}`}
                    timerId={`${ficha.id}-${fase.id}`}
                    fichaId={ficha.id}
                    produtoNome={ficha.produto}
                    faseNome={fase.fase}
                    faseOrdem={fase.ordem}
                    minutosPrevistos={fase.tempo_previsto_min}
                  />
                </div>
              </h3>
              {componentes.length > 0 && <p>{componentes.map((item) => `${item.produto} (${numero.format(item.quantidade)} ${item.unidade_medida})`).join(' · ')}</p>}
            </div>
          </li>
        })}
      </ol>
      {semEtapa.length > 0 && <p className="sheet-general-components"><strong>Componentes gerais:</strong> {semEtapa.map((item) => item.produto).join(', ')}.</p>}
    </section>
    <section className="sheet-section sheet-notes">
      <h2>Observações</h2>
      <p>{ficha.observacao || 'Sem observações adicionais.'}</p>
    </section>
    <footer className="sheet-document-foot">Documento gerado pelo {branding.nome} · Ficha #{ficha.id}</footer>
  </article>
}