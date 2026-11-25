import { useState } from 'react'
import { SearchSelect } from '../../../components/ui'
import type { Usuario } from '../../../types'
import { definirResponsavelGlobal, removerResponsavelGlobal, useResponsavelGlobal } from './timersStore'

interface PhaseAssigneeProps {
  timerId: string
  usuarios: Usuario[]
}

export function PhaseAssignee({ timerId, usuarios }: PhaseAssigneeProps) {
  const responsavel = useResponsavelGlobal(timerId)
  const [selecionando, setSelecionando] = useState(false)

  const opcoesUsuarios = usuarios
    .filter((u) => u.ativo !== 0)
    .map((u) => ({
      value: u.nome,
      label: `${u.nome} (${u.username})`,
    }))

  function selecionar(nome: string) {
    definirResponsavelGlobal(timerId, nome)
    setSelecionando(false)
  }

  if (selecionando) {
    return (
      <div className="phase-assignee-select">
        <SearchSelect
          ariaLabel="Selecionar responsável"
          placeholder="Buscar cozinheiro..."
          value={responsavel}
          options={opcoesUsuarios}
          onChange={selecionar}
        />
        <button
          type="button"
          className="phase-assignee-remove"
          title="Cancelar"
          onClick={() => setSelecionando(false)}
        >
          ×
        </button>
      </div>
    )
  }

  if (responsavel) {
    return (
      <span className="phase-assignee-chip">
        <button
          type="button"
          className="phase-assignee-name"
          title="Clique para trocar o responsável"
          onClick={() => setSelecionando(true)}
        >
          👤 {responsavel}
        </button>
        <button
          type="button"
          className="phase-assignee-remove"
          title="Remover responsável"
          aria-label="Remover responsável"
          onClick={() => removerResponsavelGlobal(timerId)}
        >
          ×
        </button>
      </span>
    )
  }

  return (
    <button
      type="button"
      className="phase-assignee-add"
      onClick={() => setSelecionando(true)}
    >
      + Responsável
    </button>
  )
}