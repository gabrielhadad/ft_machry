import { useState, type FormEvent } from 'react'
import { SearchSelect } from '../../../components/ui'
import type { PapelUsuario, Usuario } from '../../../types'
import { mensagemDeErro } from '../../../utils/erros'
import { atualizarUsuario, criarUsuario } from '../api/usuariosApi'

const opcoesDePerfil: { value: PapelUsuario; label: string }[] = [
  { value: 'OWNER', label: 'Proprietário' },
  { value: 'ADMIN', label: 'Gestor' },
  { value: 'USER', label: 'Cozinha' },
]

const opcoesDeAtivo = [
  { value: '1', label: 'Sim' },
  { value: '0', label: 'Não' },
]

interface FormularioDeUsuarioProps {
  usuario: Usuario | null
  usuarioLogado: Usuario
  onSalvo: () => Promise<void>
  onCancelar: () => void
}

export function FormularioDeUsuario({ usuario, usuarioLogado, onSalvo, onCancelar }: FormularioDeUsuarioProps) {
  const [nome, setNome] = useState(usuario?.nome ?? '')
  const [username, setUsername] = useState(usuario?.username ?? '')
  const [password, setPassword] = useState('')
  const [papel, setPapel] = useState<PapelUsuario>(usuario?.papel ?? 'USER')
  const [ativo, setAtivo] = useState(usuario?.ativo !== 0)
  const [erro, setErro] = useState('')
  const [salvando, setSalvando] = useState(false)

  async function salvar(event: FormEvent) {
    event.preventDefault()
    setSalvando(true)
    setErro('')
    try {
      if (usuario) {
        const novaSenha = password ? { password } : {}
        await atualizarUsuario(usuario.id, { nome: nome.trim(), papel, ativo: ativo ? 1 : 0, ...novaSenha })
      } else {
        await criarUsuario({ nome: nome.trim(), username: username.trim(), password, papel })
      }
      await onSalvo()
    } catch (reason) {
      setErro(mensagemDeErro(reason, 'Falha ao salvar.'))
    } finally {
      setSalvando(false)
    }
  }

  return <section className="panel">
    <h2>{usuario ? 'Editar usuário' : 'Novo usuário'}</h2>
    <form className="inline-form" onSubmit={salvar}>
      <label>
        Nome
        <input required minLength={2} value={nome} onChange={(event) => setNome(event.target.value)} />
      </label>
      <label>
        Login
        <input required={!usuario} disabled={!!usuario} minLength={3} value={username} onChange={(event) => setUsername(event.target.value)} />
      </label>
      <label>
        {usuario ? 'Nova senha (opcional)' : 'Senha'}
        <input type="password" required={!usuario} minLength={8} value={password} onChange={(event) => setPassword(event.target.value)} />
      </label>
      <label>
        Perfil
        <SearchSelect ariaLabel="Perfil" value={papel} onChange={setPapel} options={opcoesDePerfil} />
      </label>
      {usuario && <label>
        Ativo
        <SearchSelect ariaLabel="Ativo" value={ativo ? '1' : '0'} disabled={usuario.id === usuarioLogado.id} onChange={(valor) => setAtivo(valor === '1')} options={opcoesDeAtivo} />
      </label>}
      <button className="primary" disabled={salvando}>{usuario ? 'Salvar usuário' : 'Cadastrar'}</button>
      {usuario && <button type="button" className="secondary" onClick={onCancelar}>Cancelar</button>}
    </form>
    {erro && <p className="form-error">{erro}</p>}
  </section>
}
