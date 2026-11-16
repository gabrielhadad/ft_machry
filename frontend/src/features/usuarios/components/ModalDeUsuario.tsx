import { useState, type FormEvent } from 'react'
import { Modal, SearchSelect, type SearchSelectOption } from '../../../components/ui'
import type { GrupoResumo, Usuario } from '../../../types'
import { mensagemDeErro } from '../../../utils/erros'
import { atualizarUsuario, criarUsuario } from '../api/usuariosApi'

const opcoesDeAtivo = [
  { value: '1', label: 'Sim' },
  { value: '0', label: 'Não' },
]

interface ModalDeUsuarioProps {
  usuario: Usuario | null
  usuarioLogado: Usuario
  grupos: GrupoResumo[] | null
  onClose: () => void
  onSalvo: () => Promise<void>
}

export function ModalDeUsuario({
  usuario,
  usuarioLogado,
  grupos,
  onClose,
  onSalvo,
}: ModalDeUsuarioProps) {
  const [nome, setNome] = useState(usuario?.nome ?? '')
  const [username, setUsername] = useState(usuario?.username ?? '')
  const [password, setPassword] = useState('')
  const [gruposEscolhidos, setGruposEscolhidos] = useState<number[]>(
    usuario?.grupos.map((grupo) => grupo.id) ?? [],
  )
  const [ativo, setAtivo] = useState(usuario?.ativo !== 0)
  const [erro, setErro] = useState('')
  const [salvando, setSalvando] = useState(false)

  const podeEscolherGrupos = grupos !== null
  const escolhidos = gruposEscolhidos
    .map((id) => grupos?.find((grupo) => grupo.id === id))
    .filter((grupo) => grupo !== undefined)
  const disponiveis = (grupos ?? []).filter((grupo) => !gruposEscolhidos.includes(grupo.id))
  const opcoesDeGrupo: SearchSelectOption<number | ''>[] = disponiveis.map((grupo) => ({
    value: grupo.id,
    label: grupo.nome,
  }))

  let placeholderDoGrupo = 'Buscar grupo para adicionar'
  if (grupos?.length === 0) placeholderDoGrupo = 'Nenhum grupo de acesso cadastrado'
  else if (disponiveis.length === 0) placeholderDoGrupo = 'Todos os grupos já foram adicionados'

  const adicionarGrupo = (id: number | '') => {
    if (id === '') return
    setGruposEscolhidos((atuais) => [...atuais, id])
  }

  const removerGrupo = (id: number) => {
    setGruposEscolhidos((atuais) => atuais.filter((item) => item !== id))
  }

  async function salvar(event: FormEvent) {
    event.preventDefault()
    setSalvando(true)
    setErro('')
    try {
      if (usuario) {
        const novaSenha = password ? { password } : {}
        const novosGrupos = podeEscolherGrupos ? { grupos: gruposEscolhidos } : {}
        await atualizarUsuario(usuario.id, {
          nome: nome.trim(),
          ativo: ativo ? 1 : 0,
          ...novosGrupos,
          ...novaSenha,
        })
      } else {
        await criarUsuario({
          nome: nome.trim(),
          username: username.trim(),
          password,
          grupos: gruposEscolhidos,
        })
      }
      await onSalvo()
    } catch (reason) {
      setErro(mensagemDeErro(reason, 'Não foi possível salvar o usuário.'))
      setSalvando(false)
    }
  }

  let textoDoBotao = usuario ? 'Salvar usuário' : 'Cadastrar usuário'
  if (salvando) textoDoBotao = 'Salvando…'

  const footer = <>
    <button className="secondary" onClick={onClose} type="button" disabled={salvando}>
      Cancelar
    </button>
    <button className="primary" form="user-form" disabled={salvando}>{textoDoBotao}</button>
  </>

  return <Modal
    eyebrow="ADMINISTRAÇÃO"
    title={usuario ? 'Editar usuário' : 'Novo usuário'}
    onClose={onClose}
    footer={footer}
  >
    <form className="dialog-body" id="user-form" onSubmit={salvar}>
      {erro && <p className="form-error">{erro}</p>}
      <div className="form-grid">
        <label>
          Nome
          <input
            required
            minLength={2}
            maxLength={120}
            value={nome}
            onChange={(event) => setNome(event.target.value)}
          />
        </label>
        <label>
          Login
          <input
            required={!usuario}
            disabled={!!usuario}
            minLength={3}
            maxLength={80}
            value={username}
            onChange={(event) => setUsername(event.target.value)}
          />
        </label>
      </div>
      <div className="form-grid">
        <label>
          {usuario ? 'Nova senha (opcional)' : 'Senha'}
          <input
            type="password"
            required={!usuario}
            minLength={8}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </label>
        {usuario && <label>
          Ativo
          <SearchSelect
            ariaLabel="Ativo"
            value={ativo ? '1' : '0'}
            disabled={usuario.id === usuarioLogado.id}
            onChange={(valor) => setAtivo(valor === '1')}
            options={opcoesDeAtivo}
          />
        </label>}
      </div>
      {podeEscolherGrupos
        ? <div className="lista-de-grupos">
          <label>
            Grupos de acesso
            <SearchSelect<number | ''>
              ariaLabel="Adicionar grupo de acesso"
              placeholder={placeholderDoGrupo}
              disabled={disponiveis.length === 0}
              value=""
              onChange={adicionarGrupo}
              options={opcoesDeGrupo}
            />
          </label>
          {escolhidos.length
            ? <div className="grupos-escolhidos">
              {escolhidos.map((grupo) => <button
                type="button"
                className="chip-button"
                key={grupo.id}
                aria-label={`Remover ${grupo.nome}`}
                onClick={() => removerGrupo(grupo.id)}
              >
                {grupo.nome}
                <span aria-hidden="true">×</span>
              </button>)}
            </div>
            : <small>Nenhum grupo escolhido: o usuário entra no sistema sem permissões.</small>}
        </div>
        : <p className="notice">
          Você não tem permissão para ver os grupos de acesso, então os grupos deste usuário
          serão mantidos como estão.
        </p>}
    </form>
  </Modal>
}
