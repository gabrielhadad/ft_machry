import { useCallback, useEffect, useState } from 'react'
import type { GrupoAcesso } from '../../../types'
import { mensagemDeErro } from '../../../utils/erros'
import { listarGruposDeAcesso } from '../api/acessosApi'

export function useGruposDeAcesso(rodadaDeAtualizacao: number, ativo = true) {
  const [grupos, setGrupos] = useState<GrupoAcesso[]>([])
  const [erro, setErro] = useState('')

  const atualizar = useCallback(async () => {
    if (!ativo) return
    try {
      setGrupos(await listarGruposDeAcesso())
      setErro('')
    } catch (reason) {
      setErro(mensagemDeErro(reason, 'Não foi possível carregar os grupos de acesso.'))
    }
  }, [ativo])

  useEffect(() => {
    void atualizar()
  }, [atualizar, rodadaDeAtualizacao])

  return { grupos, erro, atualizar }
}
