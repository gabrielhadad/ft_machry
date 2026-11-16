import type { GrupoAcesso } from '../../../types'

interface TabelaDeGruposProps {
  grupos: GrupoAcesso[]
  erro: string
  podeAtualizar: boolean
  onAbrir: (grupo: GrupoAcesso) => void
  onExcluir?: (grupo: GrupoAcesso) => void
}

export function TabelaDeGrupos({
  grupos,
  erro,
  podeAtualizar,
  onAbrir,
  onExcluir,
}: TabelaDeGruposProps) {
  return <section className="panel">
    {erro && <p className="form-error">{erro}</p>}
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Grupo</th>
            <th>Descrição</th>
            <th>Permissões</th>
            <th>Usuários</th>
            <th>Ações</th>
          </tr>
        </thead>
        <tbody>
          {grupos.map((grupo) => <tr key={grupo.id}>
            <td>
              <strong>{grupo.nome}</strong>
              {grupo.protegido === 1 && <span className="badge protegido">Protegido</span>}
            </td>
            <td className="grupo-descricao">{grupo.descricao || '—'}</td>
            <td>{grupo.permissoes.length}</td>
            <td>{grupo.total_usuarios}</td>
            <td>
              <button className="text-button" onClick={() => onAbrir(grupo)}>
                {grupo.protegido === 1 || !podeAtualizar ? 'Ver' : 'Editar'}
              </button>
              {onExcluir && grupo.protegido === 0 && <>
                {' · '}
                <button className="danger-link" onClick={() => onExcluir(grupo)}>Excluir</button>
              </>}
            </td>
          </tr>)}
        </tbody>
      </table>
    </div>
  </section>
}
