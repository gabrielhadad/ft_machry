import type { Permissao, PermissaoCatalogo, RecursoPermissao } from '../../../types'
import { ordemDasAcoes, rotuloDaAcao, rotuloDoRecurso } from '../utils/rotulos'

interface MatrizDePermissoesProps {
  catalogo: PermissaoCatalogo[]
  selecionadas: Permissao[]
  desabilitada: boolean
  onChange: (selecionadas: Permissao[]) => void
}

function recursosDoCatalogo(catalogo: PermissaoCatalogo[]): RecursoPermissao[] {
  const recursos: RecursoPermissao[] = []
  for (const permissao of catalogo) {
    if (!recursos.includes(permissao.recurso)) recursos.push(permissao.recurso)
  }
  return recursos
}

export function MatrizDePermissoes({
  catalogo,
  selecionadas,
  desabilitada,
  onChange,
}: MatrizDePermissoesProps) {
  const recursos = recursosDoCatalogo(catalogo)
  const codigosDoRecurso = (recurso: RecursoPermissao) => catalogo
    .filter((permissao) => permissao.recurso === recurso)
    .map((permissao) => permissao.codigo)

  const alternar = (codigo: Permissao) => {
    if (selecionadas.includes(codigo)) onChange(selecionadas.filter((item) => item !== codigo))
    else onChange([...selecionadas, codigo])
  }

  const alternarRecurso = (recurso: RecursoPermissao) => {
    const codigos = codigosDoRecurso(recurso)
    const todosMarcados = codigos.every((codigo) => selecionadas.includes(codigo))
    const semOsDoRecurso = selecionadas.filter((codigo) => !codigos.includes(codigo))
    onChange(todosMarcados ? semOsDoRecurso : [...semOsDoRecurso, ...codigos])
  }

  return <div className="table-wrap matriz-permissoes">
    <table>
      <thead>
        <tr>
          <th>Área do sistema</th>
          {ordemDasAcoes.map((acao) => <th key={acao}>{rotuloDaAcao[acao]}</th>)}
          {!desabilitada && <th>Linha inteira</th>}
        </tr>
      </thead>
      <tbody>
        {recursos.map((recurso) => {
          const codigos = codigosDoRecurso(recurso)
          const todosMarcados = codigos.every((codigo) => selecionadas.includes(codigo))
          return <tr key={recurso}>
            <td><strong>{rotuloDoRecurso[recurso]}</strong></td>
            {ordemDasAcoes.map((acao) => {
              const codigo: Permissao = `${recurso}:${acao}`
              const existe = codigos.includes(codigo)
              return <td key={acao}>
                {existe
                  ? <input
                    type="checkbox"
                    aria-label={`${rotuloDaAcao[acao]} ${rotuloDoRecurso[recurso]}`}
                    checked={selecionadas.includes(codigo)}
                    disabled={desabilitada}
                    onChange={() => alternar(codigo)}
                  />
                  : <span className="ausente" title="Ação não disponível para esta área">
                    —
                  </span>}
              </td>
            })}
            {!desabilitada && <td>
              <button
                className="text-button"
                type="button"
                onClick={() => alternarRecurso(recurso)}
              >
                {todosMarcados ? 'Desmarcar todas' : 'Marcar todas'}
              </button>
            </td>}
          </tr>
        })}
      </tbody>
    </table>
  </div>
}
