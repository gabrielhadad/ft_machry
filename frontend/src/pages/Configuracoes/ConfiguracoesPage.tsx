import { useEffect, useState, type FormEvent } from 'react'
import { PageHeading } from '../../components/ui'
import {
  buscarConfiguracoes,
  salvarConfiguracoes,
  type MetodoCustoMedio,
} from '../../features/configuracoes'
import { mensagemDeErro } from '../../utils/erros'

const metodos: { valor: MetodoCustoMedio; titulo: string; descricao: string }[] = [
  {
    valor: 'PONDERADO_MOVEL',
    titulo: 'Custo médio ponderado móvel',
    descricao: 'A cada entrada com custo, a média é recalculada com o saldo anterior. '
      + 'Saídas reduzem o saldo, mas não mudam a média. É o método contábil usual.',
  },
  {
    valor: 'PONDERADO_SALDO',
    titulo: 'Média ponderada pelo saldo atual',
    descricao: 'Média do custo dos lotes que ainda têm saldo, ponderada pela quantidade de cada um. '
      + 'Quando um lote sai do estoque, ele deixa de contar na média.',
  },
]

interface ConfiguracoesPageProps {
  podeAtualizar: boolean
  aoSalvar: (mensagem: string) => void
}

export function ConfiguracoesPage({ podeAtualizar, aoSalvar }: ConfiguracoesPageProps) {
  const [salvo, setSalvo] = useState<MetodoCustoMedio | null>(null)
  const [metodo, setMetodo] = useState<MetodoCustoMedio | null>(null)
  const [erro, setErro] = useState('')
  const [salvando, setSalvando] = useState(false)

  useEffect(() => {
    buscarConfiguracoes()
      .then((dados) => {
        setSalvo(dados.metodo_custo_medio)
        setMetodo(dados.metodo_custo_medio)
      })
      .catch((reason) => setErro(mensagemDeErro(reason, 'Não foi possível carregar as configurações.')))
  }, [])

  async function salvar(event: FormEvent) {
    event.preventDefault()
    if (!metodo) return
    setSalvando(true)
    setErro('')
    try {
      const dados = await salvarConfiguracoes({ metodo_custo_medio: metodo })
      setSalvo(dados.metodo_custo_medio)
      setMetodo(dados.metodo_custo_medio)
      aoSalvar('Configurações salvas.')
    } catch (reason) {
      setErro(mensagemDeErro(reason, 'Não foi possível salvar as configurações.'))
    } finally {
      setSalvando(false)
    }
  }

  return <>
    <PageHeading
      eyebrow="SISTEMA"
      title="Configurações"
      description="Ajustes gerais que valem para todos os usuários."
    />
    <section className="panel">
      <h2>Custo dos produtos</h2>
      <p className="settings-help">
        Define como o custo unitário de cada produto é calculado a partir do estoque.
        É usado no custo dos componentes e no custo total das fichas técnicas.
      </p>
      <form onSubmit={salvar} className="settings-form">
        {metodo === null && !erro && <p>Carregando…</p>}
        {metodo !== null && <fieldset className="settings-options" disabled={!podeAtualizar || salvando}>
          <legend>Método de custo médio</legend>
          {metodos.map((opcao) => <label key={opcao.valor} className="settings-option">
            <input
              type="radio"
              name="metodo_custo_medio"
              value={opcao.valor}
              checked={metodo === opcao.valor}
              onChange={() => setMetodo(opcao.valor)}
            />
            <span>
              <strong>{opcao.titulo}</strong>
              <small>{opcao.descricao}</small>
            </span>
          </label>)}
        </fieldset>}
        {erro && <p className="form-error">{erro}</p>}
        {podeAtualizar && metodo !== null && <button className="primary" disabled={salvando || metodo === salvo}>
          {salvando ? 'Salvando…' : 'Salvar'}
        </button>}
      </form>
    </section>
  </>
}
