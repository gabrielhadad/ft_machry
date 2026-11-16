import { useState } from 'react'
import { PageHeading } from '../../components/ui'
import {
  excluirGrupo,
  ModalDeGrupo,
  TabelaDeGrupos,
  useGruposDeAcesso,
  usePermissoes,
} from '../../features/acessos'
import type { GrupoAcesso, UsuarioLogado } from '../../types'
import { mensagemDeErro } from '../../utils/erros'
import { temPermissao } from '../../utils/permissoes'

const descricaoDaPagina =
  'Cada grupo reúne permissões por área do sistema. ' +
  'Um usuário pode estar em vários grupos e acumula as permissões de todos eles.'

interface GruposDeAcessoPageProps {
  usuarioLogado: UsuarioLogado
  rodadaDeAtualizacao: number
}

export function GruposDeAcessoPage({
  usuarioLogado,
  rodadaDeAtualizacao,
}: GruposDeAcessoPageProps) {
  const podeCriar = temPermissao(usuarioLogado, 'grupos_acesso:criar')
  const podeAtualizar = temPermissao(usuarioLogado, 'grupos_acesso:atualizar')
  const podeExcluir = temPermissao(usuarioLogado, 'grupos_acesso:excluir')
  const { grupos, erro, atualizar } = useGruposDeAcesso(rodadaDeAtualizacao)
  const { catalogo, erro: erroDoCatalogo } = usePermissoes()
  const [aberto, setAberto] = useState<GrupoAcesso | 'novo' | null>(null)
  const [erroAoExcluir, setErroAoExcluir] = useState('')

  const abrir = (grupo: GrupoAcesso | 'novo') => {
    setAberto(grupo)
    setErroAoExcluir('')
  }

  const aposSalvar = async () => {
    setAberto(null)
    await atualizar()
  }

  const excluir = async (grupo: GrupoAcesso) => {
    const aviso = grupo.total_usuarios
      ? ` ${grupo.total_usuarios} usuário(s) perderão as permissões deste grupo.`
      : ''
    if (!window.confirm(`Excluir o grupo ${grupo.nome}?${aviso}`)) return
    setErroAoExcluir('')
    try {
      await excluirGrupo(grupo.id)
      await atualizar()
    } catch (reason) {
      setErroAoExcluir(mensagemDeErro(reason, 'Falha ao excluir.'))
    }
  }

  const grupoAberto = aberto === 'novo' ? null : aberto
  const somenteLeitura = grupoAberto ? grupoAberto.protegido === 1 || !podeAtualizar : false

  const acoes = podeCriar
    ? <button className="primary" onClick={() => abrir('novo')}>Novo grupo</button>
    : undefined

  return <>
    <PageHeading
      eyebrow="ADMINISTRAÇÃO"
      title="Grupos de acesso"
      description={descricaoDaPagina}
      action={acoes}
    />
    {erroDoCatalogo && <p className="form-error">{erroDoCatalogo}</p>}
    <TabelaDeGrupos
      grupos={grupos}
      erro={erro || erroAoExcluir}
      podeAtualizar={podeAtualizar}
      onAbrir={abrir}
      onExcluir={podeExcluir ? (grupo) => void excluir(grupo) : undefined}
    />

    {aberto && <ModalDeGrupo
      grupo={grupoAberto}
      catalogo={catalogo}
      somenteLeitura={somenteLeitura}
      onClose={() => setAberto(null)}
      onSalvo={aposSalvar}
    />}
  </>
}
