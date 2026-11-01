import { useState, type FormEvent } from 'react'
import { api } from './api'
import { Modal } from './components'
import type { Usuario } from './types'

function PasswordForm({ usuario, onChanged, compact = false }: { usuario: Usuario; onChanged: (usuario: Usuario) => void; compact?: boolean }) {
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(event: FormEvent) {
    event.preventDefault(); setError('')
    if (newPassword !== confirmPassword) { setError('As novas senhas não conferem.'); return }
    setBusy(true)
    try {
      const updated = await api<Usuario>('/api/auth/change-password', {
        method: 'POST',
        body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
      })
      onChanged(updated)
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Não foi possível alterar a senha.') }
    finally { setBusy(false) }
  }

  return <form className={compact ? 'dialog-body' : 'login-card'} onSubmit={submit}>
    {!compact && <><span className="eyebrow">SEGURANÇA DA CONTA</span><h2>Crie sua nova senha</h2><p>Olá, {usuario.nome}. Troque a senha inicial antes de continuar.</p></>}
    {error && <p className="form-error">{error}</p>}
    <label>Senha atual<input required type="password" autoComplete="current-password" value={currentPassword} onChange={e => setCurrentPassword(e.target.value)} /></label>
    <label>Nova senha<input required minLength={8} type="password" autoComplete="new-password" value={newPassword} onChange={e => setNewPassword(e.target.value)} /></label>
    <small className="helper">Use maiúscula, minúscula, número e caractere especial.</small>
    <label>Confirmar nova senha<input required minLength={8} type="password" autoComplete="new-password" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} /></label>
    <button className="primary" disabled={busy}>{busy ? 'Alterando…' : 'Alterar senha'}</button>
  </form>
}

export function FirstLoginPasswordPage({ usuario, onChanged }: { usuario: Usuario; onChanged: (usuario: Usuario) => void }) {
  return <main className="login-page"><section className="login-brand"><div className="login-mark">C+</div><span className="eyebrow">PRIMEIRO ACESSO</span><h1>Proteja sua conta.</h1><p>A senha inicial é temporária e precisa ser substituída antes de acessar a operação.</p></section><section className="login-panel"><PasswordForm usuario={usuario} onChanged={onChanged} /></section></main>
}

export function PasswordChangeModal({ usuario, onClose, onChanged }: { usuario: Usuario; onClose: () => void; onChanged: (usuario: Usuario) => void }) {
  return <Modal eyebrow="SEGURANÇA" title="Alterar minha senha" onClose={onClose} footer={<button type="button" className="secondary" onClick={onClose}>Cancelar</button>}>
    <PasswordForm usuario={usuario} compact onChanged={onChanged} />
  </Modal>
}
