import { LoginForm } from '../../features/auth'
import { BrandMark, useBranding } from '../../features/branding'
import type { Usuario } from '../../types'

const destaques = [
  { numero: '01', titulo: 'Planejamento claro', texto: 'Cada pessoa vê exatamente o que precisa fazer.' },
  { numero: '02', titulo: 'Receitas padronizadas', texto: 'Etapas e quantidades sempre disponíveis.' },
]

export function LoginPage({ onLogin }: { onLogin: (usuario: Usuario) => void }) {
  const branding = useBranding()
  return <main className="login-page">
    <section className="login-brand">
      <BrandMark className="login-mark" variant="horizontal" />
      <span className="eyebrow">{branding.subtitulo}</span>
      <h1>Organize o trabalho de hoje.</h1>
      <p>Estoque, fichas técnicas e produção em um só lugar para toda a equipe.</p>
      {destaques.map((destaque) => <div className="login-feature" key={destaque.numero}>
        <span>{destaque.numero}</span>
        <div>
          <strong>{destaque.titulo}</strong>
          <small>{destaque.texto}</small>
        </div>
      </div>)}
    </section>
    <section className="login-panel">
      <LoginForm onLogin={onLogin} />
    </section>
  </main>
}
