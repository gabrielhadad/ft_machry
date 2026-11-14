import { useState } from 'react'
import { PageHeading } from '../../components/ui'
import { FormularioDeUsuario, TabelaDeUsuarios, useUsuarios } from '../../features/usuarios'
import type { Usuario } from '../../types'

export function UsuariosPage({ usuarioLogado }: { usuarioLogado: Usuario }) {
  const { usuarios, erro, atualizar } = useUsuarios()
  const [editando, setEditando] = useState<Usuario | null>(null)
  const [versaoDoFormulario, setVersaoDoFormulario] = useState(0)

  const reiniciarFormulario = () => {
    setEditando(null)
    setVersaoDoFormulario((versao) => versao + 1)
  }

  const aposSalvar = async () => {
    await atualizar()
    reiniciarFormulario()
  }

  return <>
    <PageHeading eyebrow="ADMINISTRAÇÃO" title="Usuários" description="Somente a conta proprietária pode cadastrar, alterar permissões e desativar acessos." />
    <FormularioDeUsuario
      key={`${editando?.id ?? 'novo'}-${versaoDoFormulario}`}
      usuario={editando}
      usuarioLogado={usuarioLogado}
      onSalvo={aposSalvar}
      onCancelar={reiniciarFormulario}
    />
    <TabelaDeUsuarios usuarios={usuarios} erro={erro} onEditar={setEditando} />
  </>
}
