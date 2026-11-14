import { useState } from 'react'
import { PageHeading } from '../../components/ui'
import { CatalogoDeProdutos, ProductImportModal, ProductModal } from '../../features/produtos'
import type { Mutacao } from '../../stores/dados'
import type { Produto } from '../../types'

interface ProdutosPageProps {
  produtos: Produto[]
  aoAlterar: (mutacao: Mutacao, mensagem: string) => Promise<void>
}

export function ProdutosPage({ produtos, aoAlterar }: ProdutosPageProps) {
  const [editando, setEditando] = useState<Produto | 'new' | null>(null)
  const [importando, setImportando] = useState(false)

  const concluir = (mensagem: string) => {
    setEditando(null)
    setImportando(false)
    void aoAlterar('produto', mensagem)
  }

  const mensagemDaImportacao = (total: number, ignorados: string[]) => {
    const avisoDeIgnorados = ignorados.length ? ` ${ignorados.length} já cadastrado(s) foram ignorados.` : ''
    return `${total} produto(s) importado(s).${avisoDeIgnorados}`
  }

  const acoes = <div className="heading-actions">
    <button className="secondary outline" onClick={() => setImportando(true)}>Importar CSV</button>
    <button className="primary" onClick={() => setEditando('new')}>Novo produto</button>
  </div>

  return <>
    <PageHeading eyebrow="CATÁLOGO" title="Produtos" description="Catálogo organizado por insumos, preparos intermediários e produtos finais." action={acoes} />
    <CatalogoDeProdutos produtos={produtos} onEdit={setEditando} />

    {editando && <ProductModal
      produto={editando === 'new' ? null : editando}
      onClose={() => setEditando(null)}
      onSaved={() => concluir('Produto salvo com sucesso.')}
      onDeleted={() => concluir('Produto excluído.')}
    />}

    {importando && <ProductImportModal
      onClose={() => setImportando(false)}
      onSaved={(total, ignorados) => concluir(mensagemDaImportacao(total, ignorados))}
    />}
  </>
}
