import { useState, type FormEvent } from 'react'
import type { Usuario } from '../../../types'
import { mensagemDeErro } from '../../../utils/erros'
import { entrar } from '../api/authApi'

export function LoginForm({ onLogin }: { onLogin: (usuario: Usuario) => void }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function submit(event: FormEvent) {
    event.preventDefault()
    setError('')
    setLoading(true)
    try {
      onLogin(await entrar(username, password))
    } catch (reason) {
      setError(mensagemDeErro(reason, 'Não foi possível entrar.'))
    } finally {
      setLoading(false)
    }
  }

  return <form className="login-card" onSubmit={submit}>
    <span className="eyebrow">ACESSO AO SISTEMA</span>
    <h2>Bem-vindo</h2>
    <p>Entre com o usuário fornecido pela proprietária.</p>
    {error && <p className="form-error">{error}</p>}
    <label>
      Usuário
      <input autoComplete="username" autoFocus required value={username} onChange={(event) => setUsername(event.target.value)} placeholder="Seu usuário" />
    </label>
    <label>
      Senha
      <input autoComplete="current-password" required type="password" value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Sua senha" />
    </label>
    <button className="primary login-submit" disabled={loading}>{loading ? 'Entrando…' : 'Entrar'}</button>
    <small className="login-help">Em caso de dificuldade, fale com a proprietária ou o gestor.</small>
  </form>
}
