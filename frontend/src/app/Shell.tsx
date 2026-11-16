import { useState, type ReactNode } from 'react'
import { BrandMark, useBranding } from '../features/branding'
import type { UsuarioLogado } from '../types'
import type { Rota, View } from './router'

interface ShellProps {
  rotas: Rota[]
  viewAtual: View
  titulo: string
  menuOpen: boolean
  usuario: UsuarioLogado
  onNavigate: (view: View) => void
  onMenuToggle: () => void
  onLogout: () => void
  onAtualizar: () => void
  children: ReactNode
}

function nomesDosGrupos(usuario: UsuarioLogado) {
  return usuario.grupos.map((grupo) => grupo.nome).join(', ') || 'Sem grupo de acesso'
}

export function Shell({
  rotas,
  viewAtual,
  titulo,
  menuOpen,
  usuario,
  onNavigate,
  onMenuToggle,
  onLogout,
  onAtualizar,
  children,
}: ShellProps) {
  const branding = useBranding()
  const [cliquesEmAtualizar, setCliquesEmAtualizar] = useState(0)

  const atualizar = () => {
    setCliquesEmAtualizar((cliques) => cliques + 1)
    onAtualizar()
  }

  const classeDoBotaoAtualizar =
    `secondary outline small refresh-button ${cliquesEmAtualizar ? 'clicado' : ''}`

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
        {rotas.map((rota) => <button
          className={`nav ${viewAtual === rota.view ? 'active' : ''}`}
          key={rota.view}
          onClick={() => onNavigate(rota.view)}
          type="button"
        >
          <span aria-hidden="true">{rota.icone}</span>
          {rota.titulo}
        </button>)}
      </nav>
      <div className="account">
        <div className="account-avatar">{usuario.nome.charAt(0).toUpperCase()}</div>
        <div>
          <strong>{usuario.nome}</strong>
          <small>{nomesDosGrupos(usuario)}</small>
        </div>
        <button onClick={onLogout} type="button">Sair</button>
      </div>
    </aside>
    <main>
      <header>
        <button className="menu" onClick={onMenuToggle} aria-label="Abrir menu" type="button">
          ☰
        </button>
        <div>
          <small>ÁREA ATUAL</small>
          <strong>{titulo}</strong>
        </div>
        <button
          key={cliquesEmAtualizar}
          className={classeDoBotaoAtualizar}
          type="button"
          onClick={atualizar}
        >
          Atualizar
        </button>
      </header>
      <div className="content">{children}</div>
    </main>
    {menuOpen && <button
      className="sidebar-scrim"
      onClick={onMenuToggle}
      aria-label="Fechar menu"
      type="button"
    />}
  </div>
}
