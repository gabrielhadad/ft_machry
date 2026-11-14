import { useState } from 'react'
import { PageHeading } from '../../components/ui'
import { GradeDeFichas, SheetImportModal } from '../../features/fichas'
import type { Mutacao } from '../../stores/dados'
import type { FichaTecnica } from '../../types'

interface FichasPageProps {
  fichas: FichaTecnica[]
  canManage: boolean
  onNew: () => void
  onView: (ficha: FichaTecnica) => void
  aoAlterar: (mutacao: Mutacao, mensagem: string) => Promise<void>
}

function mensagemDaImportacao(total: number, fasesCriadas: string[], ignoradas: string[]) {
  const avisoDeFases = fasesCriadas.length ? ` Fases criadas: ${fasesCriadas.join(', ')}.` : ''
  const avisoDeIgnoradas = ignoradas.length ? ` Já tinham ficha: ${ignoradas.join(', ')}.` : ''
  return `${total} ficha(s) importada(s).${avisoDeFases}${avisoDeIgnoradas}`
}

export function FichasPage({ fichas, canManage, onNew, onView, aoAlterar }: FichasPageProps) {
  const [importando, setImportando] = useState(false)

  const acoes = canManage
    ? <div className="heading-actions">
      <button className="secondary outline" onClick={() => setImportando(true)}>Importar CSV</button>
      <button className="primary" onClick={onNew}>Nova ficha</button>
    </div>
    : undefined

  return <>
    <PageHeading eyebrow="PADRONIZAÇÃO" title="Fichas técnicas" description="Rendimento, etapas e componentes de cada preparo da cozinha." action={acoes} />
    <GradeDeFichas fichas={fichas} onView={onView} />

    {importando && <SheetImportModal
      onClose={() => setImportando(false)}
      onSaved={(total, fasesCriadas, ignoradas) => {
        setImportando(false)
        void aoAlterar('ficha', mensagemDaImportacao(total, fasesCriadas, ignoradas))
      }}
    />}
  </>
}
