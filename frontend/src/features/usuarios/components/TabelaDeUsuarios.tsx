import { useState } from 'react'
import { Pagination } from '../../../components/ui'
import type { Usuario } from '../../../types'

const POR_PAGINA = 20

interface TabelaDeUsuariosProps {
  usuarios: Usuario[]
  erro: string
  onEditar: (usuario: Usuario) => void
}

export function TabelaDeUsuarios({ usuarios, erro, onEditar }: TabelaDeUsuariosProps) {
  const [pagina, setPagina] = useState(1)
  const paginaAtual = Math.min(pagina, Math.max(1, Math.ceil(usuarios.length / POR_PAGINA)))
  const visiveis = usuarios.slice((paginaAtual - 1) * POR_PAGINA, paginaAtual * POR_PAGINA)

  return <section className="panel">
    {erro && <p className="form-error">{erro}</p>}
    <div className="table-wrap">
      <table>
        <thead>
          <tr><th>Nome</th><th>Login</th><th>Perfil</th><th>Status</th><th></th></tr>
        </thead>
        <tbody>
          {visiveis.map((usuario) => <tr key={usuario.id}>
            <td><strong>{usuario.nome}</strong></td>
            <td>{usuario.username}</td>
            <td>{usuario.papel}</td>
            <td>{usuario.ativo ? 'Ativo' : 'Inativo'}</td>
            <td><button className="text-button" onClick={() => onEditar(usuario)}>Editar</button></td>
          </tr>)}
        </tbody>
      </table>
    </div>
    <Pagination page={paginaAtual} perPage={POR_PAGINA} total={usuarios.length} label="Paginação de usuários" onChange={setPagina} />
  </section>
}
