import { useState, type FormEvent } from 'react'
import { SearchSelect } from '../../../components/ui'
import type { Conservacao, Localizacao } from '../../../types'
import { mensagemDeErro } from '../../../utils/erros'
import { opcoesDeConservacao } from '../../produtos'
import { atualizarLocalizacao, criarLocalizacao } from '../api/localizacoesApi'

interface FormularioDeLocalizacaoProps {
  localizacao: Localizacao | null
  localizacoes: Localizacao[]
  onSalva: () => Promise<void>
  onCancelar: () => void
}

export function FormularioDeLocalizacao({ localizacao, localizacoes, onSalva, onCancelar }: FormularioDeLocalizacaoProps) {
  const [nome, setNome] = useState(localizacao?.nome ?? '')
  const [tipo, setTipo] = useState<Conservacao>(localizacao?.tipo ?? 'SECO')
  const [superior, setSuperior] = useState(localizacao?.parent_id?.toString() ?? '')
  const [erro, setErro] = useState('')
  const [salvando, setSalvando] = useState(false)

  const opcoesDeSuperior = [
    { value: '', label: 'Nenhuma' },
    ...localizacoes.filter((item) => item.id !== localizacao?.id).map((item) => ({ value: String(item.id), label: item.nome })),
  ]

  async function salvar(event: FormEvent) {
    event.preventDefault()
    setSalvando(true)
    setErro('')
    const dados = { nome: nome.trim(), tipo, parent_id: superior ? Number(superior) : null }
    try {
      if (localizacao) await atualizarLocalizacao(localizacao.id, dados)
      else await criarLocalizacao(dados)
      await onSalva()
    } catch (reason) {
      setErro(mensagemDeErro(reason, 'Falha ao salvar.'))
    } finally {
      setSalvando(false)
    }
  }

  return <section className="panel">
    <h2>{localizacao ? `Editar ${localizacao.nome}` : 'Nova localização'}</h2>
    <form onSubmit={salvar} className="inline-form">
      <label>
        Nome
        <input required value={nome} onChange={(event) => setNome(event.target.value)} />
      </label>
      <label>
        Conservação
        <SearchSelect ariaLabel="Tipo" value={tipo} onChange={setTipo} options={opcoesDeConservacao} />
      </label>
      <label>
        Localização superior
        <SearchSelect ariaLabel="Localização superior" value={superior} onChange={setSuperior} options={opcoesDeSuperior} />
      </label>
      <button className="primary" disabled={salvando || !nome.trim()}>{localizacao ? 'Salvar alterações' : 'Criar localização'}</button>
      {localizacao && <button type="button" className="secondary" onClick={onCancelar}>Cancelar</button>}
    </form>
    {erro && <p className="form-error">{erro}</p>}
  </section>
}
