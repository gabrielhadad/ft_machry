import { useState } from 'react'
import { PageHeading } from '../../components/ui'
import { excluirLocalizacao, FormularioDeLocalizacao, TabelaDeLocalizacoes } from '../../features/localizacoes'
import type { Mutacao } from '../../stores/dados'
import type { Localizacao } from '../../types'
import { mensagemDeErro } from '../../utils/erros'

interface LocalizacoesPageProps {
  localizacoes: Localizacao[]
  atualizar: (mutacao: Mutacao) => Promise<boolean>
}

export function LocalizacoesPage({ localizacoes, atualizar }: LocalizacoesPageProps) {
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

  return <>
    <PageHeading eyebrow="ORGANIZAÇÃO" title="Localizações" description="Cadastre e organize depósitos, câmaras frias, geladeiras e áreas de armazenamento." />
    <FormularioDeLocalizacao
      key={`${editando?.id ?? 'nova'}-${versaoDoFormulario}`}
      localizacao={editando}
      localizacoes={localizacoes}
      onSalva={aposSalvar}
      onCancelar={reiniciarFormulario}
    />
    <TabelaDeLocalizacoes localizacoes={localizacoes} erro={erroAoExcluir} onEditar={editar} onExcluir={(localizacao) => void excluir(localizacao)} />
  </>
}
