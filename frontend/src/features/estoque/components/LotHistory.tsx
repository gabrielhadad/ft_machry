import { useEffect, useState } from 'react'
import { EmptyState } from '../../../components/ui'
import type { Lote, Movimento } from '../../../types'
import { formatarDataHora } from '../../../utils/datas'
import { mensagemDeErro } from '../../../utils/erros'
import { numero } from '../../../utils/formatacao'
import { listarMovimentacoes } from '../api/estoqueApi'
import { movimentoLabels } from '../rotulos'

const maisRecentePrimeiro = (a: Movimento, b: Movimento) => b.criado_em.localeCompare(a.criado_em) || b.id - a.id

export function LotHistory({ lote }: { lote: Lote }) {
  const [movimentos, setMovimentos] = useState<Movimento[] | null>(null)
  const [erro, setErro] = useState('')

  useEffect(() => {
    let vigente = true
    listarMovimentacoes(lote.id)
      .then((dados) => { if (vigente) setMovimentos([...dados].sort(maisRecentePrimeiro)) })
      .catch((reason) => { if (vigente) setErro(mensagemDeErro(reason)) })
    return () => { vigente = false }
  }, [lote.id, lote.quantidade])

  if (erro) return <p className="form-error">{erro}</p>
  if (!movimentos) return <p className="helper">Carregando histórico…</p>
  if (!movimentos.length) return <EmptyState title="Sem movimentações" text="Nenhuma movimentação registrada para este lote." />

  return <ol className="timeline">
    {movimentos.map((item) => {
      const notas = [item.motivo, item.observacao].filter(Boolean)
      return <li key={item.id}>
        <div>
          <strong>{movimentoLabels[item.tipo] ?? item.tipo}</strong>
          <span>
            {numero.format(item.quantidade)}
            {item.quantidade_destino ? ` → ${numero.format(item.quantidade_destino)}` : ''}
            {item.lote_destino_id ? ` · para o lote #${item.lote_destino_id}` : ''}
          </span>
        </div>
        <small>{formatarDataHora(item.criado_em)} · usuário #{item.usuario_id}{notas.length ? ` · ${notas.join(' · ')}` : ''}</small>
      </li>
    })}
  </ol>
}
