import { useCallback, useEffect, useState } from 'react'
import type { ItemLote } from '../../../types'
import { mensagemDeErro } from '../../../utils/erros'
import { listarItensDoLote } from '../api/estoqueApi'

export function useItensDoLote(loteId: number | null, ativo: boolean) {
  const [itens, setItens] = useState<ItemLote[] | null>(null)
  const [erro, setErro] = useState('')
  const [versao, setVersao] = useState(0)
  const recarregar = useCallback(() => setVersao((valor) => valor + 1), [])

  useEffect(() => {
    if (!loteId || !ativo) {
      setItens([])
      return
    }
    let vigente = true
    setErro('')
    listarItensDoLote(loteId)
      .then((dados) => { if (vigente) setItens(dados) })
      .catch((reason) => { if (vigente) setErro(mensagemDeErro(reason)) })
    return () => { vigente = false }
  }, [loteId, ativo, versao])

  return { itens, erro, recarregar }
}
