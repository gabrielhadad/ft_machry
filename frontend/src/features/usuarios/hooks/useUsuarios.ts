import { useCallback, useEffect, useState } from 'react'
import type { Usuario } from '../../../types'
import { mensagemDeErro } from '../../../utils/erros'
import { listarUsuarios } from '../api/usuariosApi'

export function useUsuarios(rodadaDeAtualizacao: number) {
  const [usuarios, setUsuarios] = useState<Usuario[]>([])
  const [erro, setErro] = useState('')

  const atualizar = useCallback(async () => {
    try {
      setUsuarios(await listarUsuarios())
      setErro('')
    } catch (reason) {
      setErro(mensagemDeErro(reason, 'Não foi possível carregar os usuários.'))
    }
  }, [])

  useEffect(() => {
    void atualizar()
  }, [atualizar, rodadaDeAtualizacao])

  return { usuarios, erro, atualizar }
}
