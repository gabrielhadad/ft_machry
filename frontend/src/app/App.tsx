import { useCallback, useEffect, useState } from 'react'
import { useSessao } from '../features/auth'
import { BrandMark, useBranding } from '../features/branding'
import { SheetModal } from '../features/fichas'
import { LoginPage } from '../pages/Login/LoginPage'
import { recursosAfetados, useDados, type Mutacao, type Recurso } from '../stores/dados'
import type { FichaTecnica, Usuario } from '../types'
import { mensagemDeErro } from '../utils/erros'
import { escreverNaUrl, podeAcessar, rotaDaView, rotasDoUsuario, viewDaUrl, viewInicial, type ContextoDaPagina, type View } from './router'
import { Shell } from './Shell'

type Toast = { text: string; error?: boolean }

const recursosDoEditorDeFicha: Recurso[] = ['produtos', 'fases']

export function App() {
  const branding = useBranding()
  const [view, setView] = useState<View>(() => viewDaUrl() ?? 'inicio')
  const [menuOpen, setMenuOpen] = useState(false)
  const { dados, estado, atualizando, garantir, recarregar, marcarDesatualizados, limpar } = useDados()
  const [erroTela, setErroTela] = useState('')
  const [tentativa, setTentativa] = useState(0)
  const [sheetModal, setSheetModal] = useState<FichaTecnica | 'new' | null>(null)
  const [toast, setToast] = useState<Toast | null>(null)

  const aoEntrar = useCallback((usuario: Usuario) => {
    const pedida = viewDaUrl()
    const destino = pedida && podeAcessar(rotaDaView(pedida), usuario) ? pedida : viewInicial(usuario)
    setView(destino)
    escreverNaUrl(destino, 'substituir')
  }, [])
  const { usuario, iniciar, logout } = useSessao({ aoEntrar, aoEncerrar: limpar })

  const rota = rotaDaView(view)
  const canManageCatalog = usuario?.papel === 'OWNER'
  const editorDeFichaAberto = sheetModal !== null && canManageCatalog
  const recursosDaTela = usuario ? rota.recursos(usuario) : []
  const recursosDoModal = editorDeFichaAberto ? recursosDoEditorDeFicha : []
  const recursosNecessarios = [...recursosDaTela, ...recursosDoModal]
  const faltamDadosDaTela = recursosDaTela.some((recurso) => estado[recurso] === 'vazio')
  const editorDeFichaPronto = !recursosDoModal.some((recurso) => estado[recurso] === 'vazio')

  useEffect(() => {
    if (!usuario) return
    const tela = rotaDaView(view).recursos(usuario)
    const modal = editorDeFichaAberto ? recursosDoEditorDeFicha : []
    const primeiraCargaDaTela = tela.some((recurso) => estado[recurso] === 'vazio')
    setErroTela('')
    garantir([...tela, ...modal]).catch((reason) => {
      const mensagem = mensagemDeErro(reason, 'Não foi possível carregar os dados.')
      if (primeiraCargaDaTela) setErroTela(mensagem)
      else setToast({ text: mensagem, error: true })
    })
  }, [usuario, view, editorDeFichaAberto, estado, tentativa, garantir])

  useEffect(() => {
    const seguirAUrl = () => setView(viewDaUrl() ?? 'inicio')
    window.addEventListener('popstate', seguirAUrl)
    return () => window.removeEventListener('popstate', seguirAUrl)
  }, [])

  useEffect(() => {
    if (!toast) return
    const timeout = window.setTimeout(() => setToast(null), 3200)
    return () => window.clearTimeout(timeout)
  }, [toast])

  const navigate = (target: View) => {
    setView(target)
    escreverNaUrl(target, 'novo')
    setMenuOpen(false)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const avisarErro = (mensagem: string) => setToast({ text: mensagem, error: true })

  const atualizar = async (mutacao: Mutacao): Promise<boolean> => {
    const afetados = recursosAfetados[mutacao]
    const visiveis = afetados.filter((recurso) => recursosNecessarios.includes(recurso))
    const invisiveis = afetados.filter((recurso) => !recursosNecessarios.includes(recurso))
    marcarDesatualizados(invisiveis)
    try {
      await recarregar(visiveis)
      return true
    } catch (reason) {
      avisarErro(mensagemDeErro(reason, 'Não foi possível atualizar os dados.'))
      return false
    }
  }

  const aoAlterar = async (mutacao: Mutacao, mensagem: string) => {
    setSheetModal(null)
    const atualizado = await atualizar(mutacao)
    if (atualizado) setToast({ text: mensagem })
  }

  if (usuario === undefined) {
    return <div className="app-loading"><BrandMark className="brand-mark" /><span>Carregando {branding.nome}…</span></div>
  }
  if (usuario === null) return <LoginPage onLogin={iniciar} />

  const contexto: ContextoDaPagina = { usuario, dados, aoAlterar, atualizar, abrirFicha: setSheetModal, avisarErro }

  let page
  if (!podeAcessar(rota, usuario)) {
    page = <section className="panel">Acesso restrito.</section>
  } else if (erroTela && faltamDadosDaTela) {
    page = <section className="panel load-error">
      <strong>Não foi possível acessar a API</strong>
      <p>{erroTela}</p>
      <button className="primary" onClick={() => setTentativa((valor) => valor + 1)}>Tentar novamente</button>
    </section>
  } else if (faltamDadosDaTela) {
    page = <section className="panel load-error">Carregando dados da operação…</section>
  } else {
    page = rota.pagina(contexto)
  }

  return <>
    <Shell
      rotas={rotasDoUsuario(usuario)}
      viewAtual={view}
      titulo={rota.titulo}
      menuOpen={menuOpen}
      atualizando={atualizando}
      usuario={usuario}
      onNavigate={navigate}
      onMenuToggle={() => setMenuOpen((open) => !open)}
      onLogout={() => void logout()}
    >
      {page}
    </Shell>

    {sheetModal && editorDeFichaPronto && <SheetModal
      ficha={sheetModal === 'new' ? null : sheetModal}
      produtos={dados.produtos}
      catalogoFases={dados.fases}
      canEdit={canManageCatalog}
      onClose={() => setSheetModal(null)}
      onSaved={() => void aoAlterar('ficha', 'Ficha técnica salva com sucesso.')}
      onDeleted={() => void aoAlterar('ficha', 'Ficha técnica excluída.')}
    />}

    {toast && <div className={`toast show ${toast.error ? 'error' : ''}`}>{toast.text}</div>}
  </>
}
