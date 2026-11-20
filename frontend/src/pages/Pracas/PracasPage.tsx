import { useEffect, useState } from 'react'
import { PageHeading } from '../../components/ui'
import { atualizarPraca, desativarPraca, listarCozinheiros, ModalDePraca, TabelaDePracas } from '../../features/pracas'
import type { Mutacao } from '../../stores/dados'
import type { CozinheiroResumo, Praca } from '../../types'
import { mensagemDeErro } from '../../utils/erros'

interface PracasPageProps {
  pracas: Praca[]
  podeCriar: boolean
  podeAtualizar: boolean
  podeExcluir: boolean
  aoAlterar: (mutacao: Mutacao, mensagem: string) => Promise<void>
  rodadaDeAtualizacao: number
}

export function PracasPage({ pracas, podeCriar, podeAtualizar, podeExcluir, aoAlterar, rodadaDeAtualizacao }: PracasPageProps) {
  const [cozinheiros, setCozinheiros] = useState<CozinheiroResumo[]>([])
  const [erroCozinheiros, setErroCozinheiros] = useState('')
  const [erro, setErro] = useState('')
  const [carregando, setCarregando] = useState(true)
  const [ocupado, setOcupado] = useState(false)
  const [editando, setEditando] = useState<Praca | 'nova' | null>(null)

  useEffect(() => {
    // A lista de cozinheiros é independente da permissão administrativa de ler usuários.
    let ativo = true
    void listarCozinheiros().then((lista) => {
      if (ativo) { setCozinheiros(lista); setErroCozinheiros('') }
    }).catch((reason) => {
      if (ativo) setErroCozinheiros(mensagemDeErro(reason, 'Não foi possível consultar os cozinheiros.'))
    }).finally(() => {
      if (ativo) setCarregando(false)
    })
    return () => { ativo = false }
  }, [rodadaDeAtualizacao])

  const aposSalvar = async (mensagem: string) => {
    await aoAlterar('praca', mensagem)
    setEditando(null)
  }

  async function mudarSituacao(praca: Praca, ativar: boolean) {
    if (!ativar && !window.confirm(`Desativar a praça ${praca.nome}? As produções antigas serão preservadas.`)) return
    setOcupado(true)
    setErro('')
    try {
      if (ativar) await atualizarPraca(praca.id, { ativo: 1 })
      else await desativarPraca(praca.id)
      await aoAlterar('praca', ativar ? 'Praça reativada.' : 'Praça desativada.')
    } catch (reason) {
      setErro(mensagemDeErro(reason, ativar ? 'Não foi possível reativar.' : 'Não foi possível desativar.'))
    } finally {
      setOcupado(false)
    }
  }

  const acoes = podeCriar ? <button type="button" className="primary"
    disabled={ocupado || carregando || !!erroCozinheiros || cozinheiros.length === 0}
    onClick={() => setEditando('nova')}>Nova praça</button> : undefined

  return <>
    <PageHeading eyebrow="OPERAÇÃO" title="Praças"
      description="Organize as estações de trabalho e os cozinheiros responsáveis por cada praça."
      action={acoes} />
    {erroCozinheiros && <p className="form-error" role="alert">{erroCozinheiros}</p>}
    {!carregando && !erroCozinheiros && cozinheiros.length === 0 && podeCriar &&
      <p className="notice">Nenhum cozinheiro ativo encontrado. Cadastre um usuário no grupo Cozinha antes de criar a praça.</p>}
    {erro && <p className="form-error" role="alert">{erro}</p>}
    <TabelaDePracas pracas={pracas} ocupado={ocupado}
      onEditar={podeAtualizar ? setEditando : undefined}
      onDesativar={podeExcluir ? (praca) => { void mudarSituacao(praca, false) } : undefined}
      onReativar={podeAtualizar ? (praca) => { void mudarSituacao(praca, true) } : undefined} />
    {editando && <ModalDePraca key={editando === 'nova' ? 'nova' : editando.id}
      praca={editando === 'nova' ? null : editando}
      cozinheiros={cozinheiros}
      onClose={() => setEditando(null)}
      onSalva={aposSalvar} />}
  </>
}
