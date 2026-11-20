import { useState } from 'react'
import { EmptyState, Pagination } from '../../../components/ui'
import type { Praca } from '../../../types'
import { normalizeSearch } from '../../../utils/texto'

const POR_PAGINA = 20

interface TabelaDePracasProps {
  pracas: Praca[]
  ocupado: boolean
  onEditar?: (praca: Praca) => void
  onDesativar?: (praca: Praca) => void
  onReativar?: (praca: Praca) => void
}

export function TabelaDePracas({ pracas, ocupado, onEditar, onDesativar, onReativar }: TabelaDePracasProps) {
  const [busca, setBusca] = useState('')
  const [pagina, setPagina] = useState(1)
  const termo = normalizeSearch(busca)
  const filtradas = pracas.filter((praca) => normalizeSearch([
    praca.nome,
    praca.descricao ?? '',
    ...praca.cozinheiros.map((cozinheiro) => cozinheiro.nome),
  ].join(' ')).includes(termo))
  const paginaAtual = Math.min(pagina, Math.max(1, Math.ceil(filtradas.length / POR_PAGINA)))
  const visiveis = filtradas.slice((paginaAtual - 1) * POR_PAGINA, paginaAtual * POR_PAGINA)

  return <section className="panel">
    <div className="toolbar">
      <input type="search" aria-label="Buscar praças" placeholder="Buscar praça ou cozinheiro"
        value={busca} onChange={(event) => { setBusca(event.target.value); setPagina(1) }} />
      <span>{filtradas.length} praça(s)</span>
    </div>
    {visiveis.length > 0 ? <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Praça</th><th>Cozinheiros</th><th>Situação</th>
            {(onEditar || onDesativar || onReativar) && <th>Ações</th>}
          </tr>
        </thead>
        <tbody>
          {visiveis.map((praca) => <tr key={praca.id}>
            <td><strong>{praca.nome}</strong>{praca.descricao && <div className="praca-descricao">{praca.descricao}</div>}</td>
            <td>{praca.cozinheiros.map((cozinheiro) => cozinheiro.nome).join(', ') || '—'}</td>
            <td><span className={praca.ativo ? '' : 'praca-status-inativo'}>{praca.ativo ? 'Ativa' : 'Inativa'}</span></td>
            {(onEditar || onDesativar || onReativar) && <td>
              <div className="praca-actions">
                {onEditar && <button type="button" className="text-button" disabled={ocupado}
                  onClick={() => onEditar(praca)}>Editar</button>}
                {praca.ativo === 1 && onDesativar && <button type="button" className="danger-link"
                  disabled={ocupado} onClick={() => onDesativar(praca)}>Desativar</button>}
                {praca.ativo === 0 && onReativar && <button type="button" className="text-button"
                  disabled={ocupado} onClick={() => onReativar(praca)}>Reativar</button>}
              </div>
            </td>}
          </tr>)}
        </tbody>
      </table>
    </div> : <EmptyState
      title={termo ? 'Nenhuma praça encontrada' : 'Nenhuma praça cadastrada'}
      text={termo ? 'Tente outro termo para buscar.' : 'Crie uma praça e vincule os cozinheiros que trabalham nela.'}
    />}
    <Pagination page={paginaAtual} perPage={POR_PAGINA} total={filtradas.length}
      label="Paginação de praças" onChange={setPagina} />
  </section>
}
