import { useState, type FormEvent } from 'react'
import { Modal } from '../../../components/ui'
import type { GrupoAcesso, Permissao, PermissaoCatalogo } from '../../../types'
import { mensagemDeErro } from '../../../utils/erros'
import { atualizarGrupo, criarGrupo } from '../api/acessosApi'
import { MatrizDePermissoes } from './MatrizDePermissoes'

interface ModalDeGrupoProps {
  grupo: GrupoAcesso | null
  catalogo: PermissaoCatalogo[]
  somenteLeitura: boolean
  onClose: () => void
  onSalvo: () => Promise<void>
}

export function ModalDeGrupo({
  grupo,
  catalogo,
  somenteLeitura,
  onClose,
  onSalvo,
}: ModalDeGrupoProps) {
  const [nome, setNome] = useState(grupo?.nome ?? '')
  const [descricao, setDescricao] = useState(grupo?.descricao ?? '')
  const [permissoes, setPermissoes] = useState<Permissao[]>(
    grupo?.permissoes.map((permissao) => permissao.codigo) ?? [],
  )
  const [erro, setErro] = useState('')
  const [salvando, setSalvando] = useState(false)

  async function salvar(event: FormEvent) {
    event.preventDefault()
    setSalvando(true)
    setErro('')
    const dados = { nome: nome.trim(), descricao: descricao.trim() || null, permissoes }
    try {
      if (grupo) await atualizarGrupo(grupo.id, dados)
      else await criarGrupo(dados)
      await onSalvo()
    } catch (reason) {
      setErro(mensagemDeErro(reason, 'Não foi possível salvar o grupo.'))
      setSalvando(false)
    }
  }

  let titulo = 'Novo grupo de acesso'
  if (grupo) titulo = somenteLeitura ? grupo.nome : `Editar ${grupo.nome}`

  let textoDoBotao = grupo ? 'Salvar grupo' : 'Criar grupo'
  if (salvando) textoDoBotao = 'Salvando…'

  const footer = <>
    <button className="secondary" onClick={onClose} type="button" disabled={salvando}>
      {somenteLeitura ? 'Fechar' : 'Cancelar'}
    </button>
    {!somenteLeitura && <button
      className="primary"
      form="group-form"
      disabled={salvando || !nome.trim()}
    >
      {textoDoBotao}
    </button>}
  </>

  return <Modal eyebrow="ADMINISTRAÇÃO" title={titulo} wide onClose={onClose} footer={footer}>
    <form className="dialog-body" id="group-form" onSubmit={salvar}>
      {erro && <p className="form-error">{erro}</p>}
      {grupo?.protegido === 1 && <p className="notice">
        O grupo {grupo.nome} é protegido: tem todas as permissões e não pode ser alterado
        nem excluído.
      </p>}
      <div className="form-grid">
        <label>
          Nome
          <input
            required
            minLength={2}
            maxLength={80}
            disabled={somenteLeitura}
            value={nome}
            onChange={(event) => setNome(event.target.value)}
          />
        </label>
        <label>
          Descrição
          <input
            maxLength={300}
            disabled={somenteLeitura}
            value={descricao}
            onChange={(event) => setDescricao(event.target.value)}
          />
        </label>
      </div>
      <div className="lista-de-grupos">
        <span className="field-title">Permissões</span>
        <small>
          Marque o que o grupo pode fazer em cada área do sistema. Um traço indica que a ação
          não existe para aquela área.
        </small>
        <MatrizDePermissoes
          catalogo={catalogo}
          selecionadas={permissoes}
          desabilitada={somenteLeitura}
          onChange={setPermissoes}
        />
      </div>
    </form>
  </Modal>
}
