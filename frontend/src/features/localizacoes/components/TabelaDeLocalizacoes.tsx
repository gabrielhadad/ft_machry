import type { Localizacao } from '../../../types'

interface TabelaDeLocalizacoesProps {
  localizacoes: Localizacao[]
  erro: string
  onEditar: (localizacao: Localizacao) => void
  onExcluir: (localizacao: Localizacao) => void
}

export function TabelaDeLocalizacoes({ localizacoes, erro, onEditar, onExcluir }: TabelaDeLocalizacoesProps) {
  const nomeDaSuperior = (localizacao: Localizacao) =>
    localizacoes.find((item) => item.id === localizacao.parent_id)?.nome || '—'

  return <section className="panel">
    {erro && <p className="form-error">{erro}</p>}
    <div className="table-wrap">
      <table>
        <thead>
          <tr><th>Nome</th><th>Tipo</th><th>Dentro de</th><th>Ações</th></tr>
        </thead>
        <tbody>
          {localizacoes.map((localizacao) => <tr key={localizacao.id}>
            <td><strong>{localizacao.nome}</strong></td>
            <td>{localizacao.tipo}</td>
            <td>{nomeDaSuperior(localizacao)}</td>
            <td>
              <button className="text-button" onClick={() => onEditar(localizacao)}>Editar</button>
              {' · '}
              <button className="danger-link" onClick={() => onExcluir(localizacao)}>Excluir</button>
            </td>
          </tr>)}
        </tbody>
      </table>
    </div>
  </section>
}
