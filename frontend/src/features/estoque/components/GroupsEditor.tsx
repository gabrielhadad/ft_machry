import { RotuloDoCampo } from '../../../components/ui'
import type { Grupo } from '../types'
import { grupoVazio, sugerirValidade } from '../utils/grupos'

interface GroupsEditorProps {
  grupos: Grupo[]
  unidade: string
  pedirValidade: boolean
  validadeObrigatoria: boolean
  validadePadraoDias?: number | null
  onChange: (grupos: Grupo[]) => void
}

export function GroupsEditor({ grupos, unidade, pedirValidade, validadeObrigatoria, validadePadraoDias, onChange }: GroupsEditorProps) {
  const atualizar = (chave: number, campos: Partial<Grupo>) =>
    onChange(grupos.map((grupo) => grupo.chave === chave ? { ...grupo, ...campos } : grupo))

  const trocarFabricacao = (grupo: Grupo, fabricacao: string) => {
    const manterValidade = grupo.validadeManual || !pedirValidade
    if (manterValidade) atualizar(grupo.chave, { fabricacao })
    else atualizar(grupo.chave, { fabricacao, validade: sugerirValidade(fabricacao, validadePadraoDias) })
  }

  const remover = (chave: number) => onChange(grupos.filter((grupo) => grupo.chave !== chave))

  return <div className="groups">
    <div className="groups-head">
      <span>Grupos de unidades <small>· use mais de um quando a marca, a validade ou o tamanho mudar</small></span>
      <button type="button" className="chip-button" onClick={() => onChange([...grupos, grupoVazio()])}>+ Grupo</button>
    </div>
    {grupos.map((grupo, indice) => <fieldset className={pedirValidade ? 'group-row' : 'group-row sem-validade'} key={grupo.chave}>
      <legend>Grupo {indice + 1}</legend>
      <label>
        Unidades
        <input type="number" min="1" max="500" step="1" required value={grupo.unidades} onChange={(event) => atualizar(grupo.chave, { unidades: event.target.value })} />
      </label>
      <label>
        Conteúdo por unidade ({unidade || 'un'})
        <input type="number" min="0.001" step="any" required value={grupo.conteudo} onChange={(event) => atualizar(grupo.chave, { conteudo: event.target.value })} placeholder="Ex.: 1000" />
      </label>
      <label>
        <RotuloDoCampo texto="Fabricante / marca" opcional />
        <input maxLength={100} value={grupo.fabricante} onChange={(event) => atualizar(grupo.chave, { fabricante: event.target.value })} placeholder="Ex.: Tio João" />
      </label>
      <label>
        <RotuloDoCampo texto="Fabricação" opcional />
        <input type="date" value={grupo.fabricacao} onChange={(event) => trocarFabricacao(grupo, event.target.value)} />
      </label>
      {pedirValidade && <label>
        <RotuloDoCampo texto="Validade" opcional={!validadeObrigatoria} />
        <input type="date" required={validadeObrigatoria} value={grupo.validade} onChange={(event) => atualizar(grupo.chave, { validade: event.target.value, validadeManual: true })} />
      </label>}
      {grupos.length > 1 && <button type="button" className="remove-row" aria-label={`Remover grupo ${indice + 1}`} onClick={() => remover(grupo.chave)}>×</button>}
    </fieldset>)}
  </div>
}
