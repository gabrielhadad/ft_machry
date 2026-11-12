import { useState, type FormEvent } from 'react'
import { api, ApiError } from './api'
import type { Usuario } from './types'

const USUARIO_MIN = 3
const SENHA_MIN = 8
const USUARIO_VALIDO = /^[a-zA-Z0-9._-]+$/

type Campo = 'username' | 'password'
type Avisos = Partial<Record<Campo, string>>

function validar(username: string, password: string): Avisos {
  const avisos: Avisos = {}
  const usuario = username.trim()
  if (!usuario) avisos.username = 'Informe o usuário. Ex.: maria.silva'
  else if (usuario.length < USUARIO_MIN) avisos.username = `O usuário tem no mínimo ${USUARIO_MIN} caracteres. Ex.: maria.silva`
  else if (!USUARIO_VALIDO.test(usuario)) avisos.username = 'Use apenas letras, números, ponto, hífen ou sublinhado, sem espaços. Ex.: maria.silva'

  if (!password) avisos.password = 'Informe a senha.'
  else if (password.length < SENHA_MIN) avisos.password = `A senha tem no mínimo ${SENHA_MIN} caracteres.`
  return avisos
}

export function LoginPage({ onLogin }: { onLogin: (usuario: Usuario) => void }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [avisos, setAvisos] = useState<Avisos>({})
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  function limpar(campo: Campo) {
    setError('')
    setAvisos((atual) => ({ ...atual, [campo]: undefined }))
  }

  async function submit(event: FormEvent) {
    event.preventDefault(); setError('')
    const encontrados = validar(username, password)
    setAvisos(encontrados)
    if (Object.keys(encontrados).length) return 

    setLoading(true)
    try {
      const usuario = await api<Usuario>('/api/auth/login', { method: 'POST', body: JSON.stringify({ username, password }) })
      onLogin(usuario)
    } catch (reason) {
      if (reason instanceof ApiError && reason.status === 401) setError('Usuário ou senha incorretos. Confira os dados e tente de novo.')
      else setError(reason instanceof Error ? reason.message : 'Não foi possível entrar.')
    } finally { setLoading(false) }
  }

  return <main className="login-page">
    <section className="login-brand"><div className="login-mark">C+</div><span className="eyebrow">COZINHA MAIS · GESTÃO DE COZINHA</span><h1>Organize o trabalho de hoje.</h1><p>Estoque, fichas técnicas e produção em um só lugar para toda a equipe.</p><div className="login-feature"><span>01</span><div><strong>Planejamento claro</strong><small>Cada pessoa vê exatamente o que precisa fazer.</small></div></div><div className="login-feature"><span>02</span><div><strong>Receitas padronizadas</strong><small>Etapas e quantidades sempre disponíveis.</small></div></div></section>
    <section className="login-panel"><form className="login-card" onSubmit={submit} noValidate><span className="eyebrow">ACESSO AO SISTEMA</span><h2>Bem-vindo</h2><p>Entre com o usuário fornecido pela proprietária.</p>
      {error && <p className="form-error" role="alert">{error}</p>}
      <label>Usuário
        <input autoComplete="username" autoFocus value={username} aria-invalid={!!avisos.username} aria-describedby={avisos.username ? 'aviso-username' : undefined}
          className={avisos.username ? 'invalid' : undefined}
          onChange={(event) => { setUsername(event.target.value); limpar('username') }} placeholder="Ex.: maria.silva" />
        {avisos.username && <span className="field-warning" id="aviso-username" role="alert">{avisos.username}</span>}
      </label>
      <label>Senha
        <input autoComplete="current-password" type="password" value={password} aria-invalid={!!avisos.password} aria-describedby={avisos.password ? 'aviso-password' : undefined}
          className={avisos.password ? 'invalid' : undefined}
          onChange={(event) => { setPassword(event.target.value); limpar('password') }} placeholder={`Mínimo de ${SENHA_MIN} caracteres`} />
        {avisos.password && <span className="field-warning" id="aviso-password" role="alert">{avisos.password}</span>}
      </label>
      <button className="primary login-submit" disabled={loading}>{loading ? 'Entrando…' : 'Entrar'}</button><small className="login-help">Em caso de dificuldade, fale com a proprietária ou o gestor.</small></form></section>
  </main>
}