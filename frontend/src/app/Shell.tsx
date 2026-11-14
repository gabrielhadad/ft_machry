import { useState, type ReactNode } from 'react'
import { BrandMark, useBranding } from '../features/branding'
import type { PapelUsuario, Usuario } from '../types'
import type { Rota, View } from './router'

const nomeDoPapel: Record<PapelUsuario, string> = {
  OWNER: 'Proprietária',
  ADMIN: 'Gestor',
  USER: 'Cozinha',
}

interface ShellProps {
  rotas: Rota[]
  viewAtual: View
  titulo: string
  menuOpen: boolean
  usuario: Usuario
  onNavigate: (view: View) => void
  onMenuToggle: () => void
  onLogout: () => void
  onAtualizar: () => void
  children: ReactNode
}

export function Shell({ rotas, viewAtual, titulo, menuOpen, usuario, onNavigate, onMenuToggle, onLogout, onAtualizar, children }: ShellProps) {
  const branding = useBranding()
  const [cliquesEmAtualizar, setCliquesEmAtualizar] = useState(0)

  const atualizar = () => {
    setCliquesEmAtualizar((cliques) => cliques + 1)
    onAtualizar()
  }

  return <div className="layout">
    <aside className={`sidebar ${menuOpen ? 'open' : ''}`}>
      <div className="brand">
        <BrandMark className="brand-mark" />
        <div>
          <strong>{branding.nome}</strong>
          <small>{branding.subtitulo}</small>
        </div>
      </div>
      <p className="nav-caption">OPERAÇÃO</p>
      <nav>
        {rotas.map((rota) => <button className={`nav ${viewAtual === rota.view ? 'active' : ''}`} key={rota.view} onClick={() => onNavigate(rota.view)} type="button">
          <span aria-hidden="true">{rota.icone}</span>
          {rota.titulo}
        </button>)}
      </nav>
      <div className="account">
        <div className="account-avatar">{usuario.nome.charAt(0).toUpperCase()}</div>
        <div>
          <strong>{usuario.nome}</strong>
          <small>{nomeDoPapel[usuario.papel]}</small>
        </div>
        <button onClick={onLogout} type="button">Sair</button>
      </div>
    </aside>
    <main>
      <header>
        <button className="menu" onClick={onMenuToggle} aria-label="Abrir menu" type="button">☰</button>
        <div>
          <small>ÁREA ATUAL</small>
          <strong>{titulo}</strong>
        </div>
        <button
          key={cliquesEmAtualizar}
          className={`secondary outline small refresh-button ${cliquesEmAtualizar ? 'clicado' : ''}`}
          type="button"
          onClick={atualizar}
        >
          Atualizar
        </button>
      </header>
      <div className="content">{children}</div>
    </main>
    {menuOpen && <button className="sidebar-scrim" onClick={onMenuToggle} aria-label="Fechar menu" type="button" />}
  </div>
}
