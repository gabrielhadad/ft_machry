import { useEffect, useState } from 'react'
import type { PermissaoCatalogo } from '../../../types'
import { mensagemDeErro } from '../../../utils/erros'
import { listarPermissoes } from '../api/acessosApi'

export function usePermissoes() {
  const [catalogo, setCatalogo] = useState<PermissaoCatalogo[]>([])
  const [erro, setErro] = useState('')

  useEffect(() => {
    listarPermissoes()
      .then(setCatalogo)
      .catch((reason) => {
        setErro(mensagemDeErro(reason, 'Não foi possível carregar o catálogo de permissões.'))
      })
  }, [])

  return { catalogo, erro }
}
