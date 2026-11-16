import { useState } from 'react'
import { PageHeading } from '../../components/ui'
import {
  excluirLocalizacao,
  FormularioDeLocalizacao,
  TabelaDeLocalizacoes,
} from '../../features/localizacoes'
import type { Mutacao } from '../../stores/dados'
import type { Localizacao } from '../../types'
import { mensagemDeErro } from '../../utils/erros'

const descricaoDaPagina =
  'Cadastre e organize depósitos, câmaras frias, geladeiras e áreas de armazenamento.'

interface LocalizacoesPageProps {
  localizacoes: Localizacao[]
  podeCriar: boolean
  podeAtualizar: boolean
  podeExcluir: boolean
  atualizar: (mutacao: Mutacao) => Promise<boolean>
}

export function LocalizacoesPage({
  localizacoes,
  podeCriar,
  podeAtualizar,
  podeExcluir,
  atualizar,
}: LocalizacoesPageProps) {
  const [editando, setEditando] = useState<Localizacao | null>(null)
  const [versaoDoFormulario, setVersaoDoFormulario] = useState(0)
  const [erroAoExcluir, setErroAoExcluir] = useState('')

  const reiniciarFormulario = () => {
    setEditando(null)
    setVersaoDoFormulario((versao) => versao + 1)
  }

  const editar = (localizacao: Localizacao) => {
    setEditando(localizacao)
    setErroAoExcluir('')
  }

  const aposSalvar = async () => {
    await atualizar('localizacao')
    reiniciarFormulario()
  }

  const excluir = async (localizacao: Localizacao) => {
    if (!window.confirm(`Excluir a localização ${localizacao.nome}?`)) return
    setErroAoExcluir('')
    try {
      await excluirLocalizacao(localizacao.id)
      await atualizar('localizacao')
      reiniciarFormulario()
    } catch (reason) {
      setErroAoExcluir(mensagemDeErro(reason, 'Falha ao excluir.'))
    }
  }

  const mostrarFormulario = editando ? podeAtualizar : podeCriar

  return <>
    <PageHeading
      eyebrow="ORGANIZAÇÃO"
      title="Localizações"
      description={descricaoDaPagina}
    />
    {mostrarFormulario && <FormularioDeLocalizacao
      key={`${editando?.id ?? 'nova'}-${versaoDoFormulario}`}
      localizacao={editando}
      localizacoes={localizacoes}
      onSalva={aposSalvar}
      onCancelar={reiniciarFormulario}
    />}
    <TabelaDeLocalizacoes
      localizacoes={localizacoes}
      erro={erroAoExcluir}
      onEditar={podeAtualizar ? editar : undefined}
      onExcluir={podeExcluir ? (localizacao) => void excluir(localizacao) : undefined}
    />
  </>
}
