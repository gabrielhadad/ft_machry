import { useState } from 'react'
import { PageHeading } from '../../components/ui'
import { useGruposDeAcesso } from '../../features/acessos'
import { ModalDeUsuario, TabelaDeUsuarios, useUsuarios } from '../../features/usuarios'
import type { Usuario, UsuarioLogado } from '../../types'
import { temPermissao } from '../../utils/permissoes'

const descricaoDaPagina =
  'Cadastre usuários e vincule cada um aos grupos de acesso que definem o que ele pode fazer.'

interface UsuariosPageProps {
  usuarioLogado: UsuarioLogado
  rodadaDeAtualizacao: number
}

export function UsuariosPage({ usuarioLogado, rodadaDeAtualizacao }: UsuariosPageProps) {
  const podeCriar = temPermissao(usuarioLogado, 'usuarios:criar')
  const podeAtualizar = temPermissao(usuarioLogado, 'usuarios:atualizar')
  const podeVerGrupos = temPermissao(usuarioLogado, 'grupos_acesso:ler')
  const podeExcluir = temPermissao(usuarioLogado, 'usuarios:excluir')
  const { usuarios, erro, atualizar } = useUsuarios(rodadaDeAtualizacao)
  const { grupos, erro: erroDosGrupos } = useGruposDeAcesso(rodadaDeAtualizacao, podeVerGrupos)
  const [aberto, setAberto] = useState<Usuario | 'novo' | null>(null)

  const aposSalvar = async () => {
    setAberto(null)
    await atualizar()
  }

  const acoes = podeCriar
    ? <button className="primary" onClick={() => setAberto('novo')}>Novo usuário</button>
    : undefined

  return <>
    <PageHeading
      eyebrow="ADMINISTRAÇÃO"
      title="Usuários"
      description={descricaoDaPagina}
      action={acoes}
    />
    {erroDosGrupos && <p className="form-error">{erroDosGrupos}</p>}
    <TabelaDeUsuarios
      usuarios={usuarios}
      erro={erro}
      onEditar={podeAtualizar ? setAberto : undefined}
    />

    {aberto && <ModalDeUsuario
      usuario={aberto === 'novo' ? null : aberto}
      usuarioLogado={usuarioLogado}
      grupos={podeVerGrupos ? grupos : null}
      podeExcluir={podeExcluir}
      onClose={() => setAberto(null)}
      onSalvo={aposSalvar}
    />}
  </>
}
