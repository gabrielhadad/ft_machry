import { useMemo, useState } from 'react'
import { PageHeading } from '../../components/ui'
import { LotModal, MetricasDeEstoque, NewLotModal, TabelaDeLotes, type Aba, type Contexto } from '../../features/estoque'
import type { Localizacao, Lote, Produto } from '../../types'

interface EstoquePageProps {
  lotes: Lote[]
  produtos: Produto[]
  localizacoes: Localizacao[]
  usuarioId: number
  onChanged: (mensagem: string) => Promise<void>
}

export function EstoquePage({ lotes, produtos, localizacoes, usuarioId, onChanged }: EstoquePageProps) {
  const [aberto, setAberto] = useState<{ loteId: number | null; aba: Aba } | null>(null)
  const [novoLote, setNovoLote] = useState(false)

  const contexto: Contexto = useMemo(() => ({
    produtosPorId: new Map(produtos.map((item) => [item.id, item])),
    locaisPorId: new Map(localizacoes.map((item) => [item.id, item])),
  }), [produtos, localizacoes])

  const loteAberto = aberto?.loteId ? lotes.find((lote) => lote.id === aberto.loteId) ?? null : null

  const acoes = <div className="heading-actions">
    <button className="secondary outline" type="button" onClick={() => setAberto({ loteId: null, aba: 'TRANSFERIR' })}>Transferir ou transformar</button>
    <button className="primary" type="button" onClick={() => setNovoLote(true)}>+ Novo lote</button>
  </div>

  return <>
    <PageHeading
      eyebrow="CONTROLE GERAL"
      title="Estoque"
      description="Veja todos os lotes com entrada, validade e situação. Clique em um lote para ver os itens que ele contém."
      action={acoes}
    />
    <MetricasDeEstoque lotes={lotes} />
    <TabelaDeLotes lotes={lotes} contexto={contexto} onVerItens={(loteId) => setAberto({ loteId, aba: 'ITENS' })} />

    {aberto && <LotModal
      lote={loteAberto}
      abaInicial={aberto.aba}
      lotes={lotes}
      produtos={produtos}
      contexto={contexto}
      usuarioId={usuarioId}
      onClose={() => setAberto(null)}
      onChanged={onChanged}
      onFinishedWithoutLot={() => setAberto(null)}
    />}

    {novoLote && <NewLotModal
      produtos={produtos}
      localizacoes={localizacoes}
      usuarioId={usuarioId}
      onClose={() => setNovoLote(false)}
      onSaved={async (loteId) => {
        setNovoLote(false)
        await onChanged(`Lote #${loteId} criado.`)
      }}
    />}
  </>
}
