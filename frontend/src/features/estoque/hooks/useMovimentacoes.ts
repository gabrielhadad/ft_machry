import { useCallback, useEffect, useState } from 'react'
import type { Movimento } from '../../../types'
import { mensagemDeErro } from '../../../utils/erros'
import { listarMovimentacoes } from '../api/estoqueApi'

export function useMovimentacoes(rodadaDeAtualizacao: number) {
  const [movimentos, setMovimentos] = useState<Movimento[]>([])
  const [erro, setErro] = useState('')
  const [carregando, setCarregando] = useState(false)

  const atualizar = useCallback(async () => {
    setCarregando(true)
    setErro('')
    try {
      setMovimentos(await listarMovimentacoes())
    } catch (reason) {
      setErro(mensagemDeErro(reason, 'Não foi possível carregar as movimentações.'))
    } finally {
      setCarregando(false)
    }
  }, [])

  useEffect(() => {
    void atualizar()
  }, [atualizar, rodadaDeAtualizacao])

  return { movimentos, erro, carregando, atualizar }
}
