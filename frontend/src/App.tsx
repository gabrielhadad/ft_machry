import { useCallback, useEffect, useState } from 'react'
import { api } from './api'
import { Shell } from './components'
import { ProductModal, SheetModal } from './forms'
import { DashboardPage, PlannedPage, ProductionPage, ProductsPage, SheetsPage, StockPage } from './pages'
import type { FaseCatalogo, FichaTecnica, ItemInventario, Produto, SolicitacaoProducao, View } from './types'

export function App() {
  const [view, setView] = useState<View>('inicio')
  const [menuOpen, setMenuOpen] = useState(false)
  const [produtos, setProdutos] = useState<Produto[]>([])
  const [fichas, setFichas] = useState<FichaTecnica[]>([])
  const [fases, setFases] = useState<FaseCatalogo[]>([])
  const [inventario, setInventario] = useState<ItemInventario[]>([])
  const [solicitacoes, setSolicitacoes] = useState<SolicitacaoProducao[]>([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')
  const [productModal, setProductModal] = useState<Produto | 'new' | null>(null)
  const [sheetModal, setSheetModal] = useState<FichaTecnica | 'new' | null>(null)
  const [toast, setToast] = useState<{ text: string; error?: boolean } | null>(null)

  const load = useCallback(async () => {
    setLoadError('')
    try {
      const [loadedProducts, loadedSheets, loadedPhases, loadedStock, loadedProduction] = await Promise.all([
        api<Produto[]>('/api/produtos'), api<FichaTecnica[]>('/api/fichas-tecnicas'), api<FaseCatalogo[]>('/api/fichas-tecnicas/fases'), api<ItemInventario[]>('/api/estoque/inventario'), api<SolicitacaoProducao[]>('/api/producao/solicitacoes'),
      ])
      setProdutos(loadedProducts); setFichas(loadedSheets); setFases(loadedPhases); setInventario(loadedStock); setSolicitacoes(loadedProduction)
    } catch (reason) { setLoadError(reason instanceof Error ? reason.message : 'Não foi possível carregar o sistema.') } finally { setLoading(false) }
  }, [])
  useEffect(() => { void load() }, [load])
  useEffect(() => { if (!toast) return; const timeout = window.setTimeout(() => setToast(null), 3200); return () => window.clearTimeout(timeout) }, [toast])
  const navigate = (target: View) => { setView(target); setMenuOpen(false); window.scrollTo({ top: 0, behavior: 'smooth' }) }
  const mutationDone = async (message: string) => { setProductModal(null); setSheetModal(null); await load(); setToast({ text: message }) }

  let page
  if (loading) page = <section className="panel load-error">Carregando dados da operação…</section>
  else if (loadError) page = <section className="panel load-error"><strong>Não foi possível acessar a API</strong><p>{loadError}</p><button className="primary" onClick={() => { setLoading(true); void load() }}>Tentar novamente</button></section>
  else if (view === 'inicio') page = <DashboardPage produtos={produtos} fichas={fichas} inventario={inventario} onNewSheet={() => setSheetModal('new')} onEditSheet={setSheetModal} />
  else if (view === 'produtos') page = <ProductsPage produtos={produtos} onNew={() => setProductModal('new')} onEdit={setProductModal} />
  else if (view === 'fichas') page = <SheetsPage fichas={fichas} onNew={() => setSheetModal('new')} onEdit={setSheetModal} />
  else if (view === 'estoque') page = <StockPage inventario={inventario} />
  else if (view === 'producao') page = <ProductionPage solicitacoes={solicitacoes} fichas={fichas} />
  else page = <PlannedPage view={view} />

  return <><Shell view={view} menuOpen={menuOpen} apiOnline={!loadError} onNavigate={navigate} onMenuToggle={() => setMenuOpen((open) => !open)}>{page}</Shell>
    {productModal && <ProductModal produto={productModal === 'new' ? null : productModal} onClose={() => setProductModal(null)} onSaved={() => void mutationDone('Produto salvo com sucesso.')} onDeleted={() => void mutationDone('Produto excluído.')} />}
    {sheetModal && <SheetModal ficha={sheetModal === 'new' ? null : sheetModal} produtos={produtos} catalogoFases={fases} onClose={() => setSheetModal(null)} onSaved={() => void mutationDone('Ficha técnica salva com sucesso.')} onDeleted={() => void mutationDone('Ficha técnica excluída.')} />}
    {toast && <div className={`toast show ${toast.error ? 'error' : ''}`}>{toast.text}</div>}
  </>
}
