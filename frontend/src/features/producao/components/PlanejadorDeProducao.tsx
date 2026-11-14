import { useEffect, useState } from 'react'
import { SearchSelect } from '../../../components/ui'
import type { FichaTecnica, Localizacao, Produto } from '../../../types'
import { numero } from '../../../utils/formatacao'

const fichaLabel = (ficha: FichaTecnica) => `${ficha.produto} · ${numero.format(ficha.rendimento)} ${ficha.unidade_rendimento}`

interface PlanejadorDeProducaoProps {
  fichas: FichaTecnica[]
  produtos: Produto[]
  localizacoes: Localizacao[]
  ocupado: boolean
  onCriar: (fichaId: number, quantidade: number, localizacaoId: number) => Promise<void>
}

export function PlanejadorDeProducao({ fichas, produtos, localizacoes, ocupado, onCriar }: PlanejadorDeProducaoProps) {
  const [selectedSheet, setSelectedSheet] = useState(fichas[0]?.id ?? 0)
  const [quantidade, setQuantidade] = useState(String(fichas[0]?.rendimento ?? ''))
  const [localizacaoId, setLocalizacaoId] = useState(0)
  const selectedFicha = fichas.find((ficha) => ficha.id === selectedSheet)
  const selectedProduct = produtos.find((produto) => produto.id === selectedFicha?.produto_id)
  const compatibleLocations = localizacoes.filter((local) => local.tipo === selectedProduct?.conservacao)
  const quantidadeNumero = Number(quantidade.replace(',', '.'))
  const podeCriar = Boolean(selectedSheet) && quantidadeNumero > 0 && Boolean(localizacaoId)

  useEffect(() => {
    if (!compatibleLocations.some((local) => local.id === localizacaoId)) {
      setLocalizacaoId(compatibleLocations[0]?.id ?? 0)
    }
  }, [compatibleLocations, localizacaoId])

  const chooseSheet = (fichaId: number) => {
    setSelectedSheet(fichaId)
    const ficha = fichas.find((item) => item.id === fichaId)
    setQuantidade(String(ficha?.rendimento ?? ''))
  }

  const create = () => {
    if (!podeCriar) return
    void onCriar(selectedSheet, quantidadeNumero, localizacaoId)
  }

  return <section className="panel production-planner">
    <div>
      <span className="eyebrow">SOLICITAÇÕES DE PRODUÇÃO</span>
      <h2>Adicionar preparo</h2>
    </div>
    <label>
      Ficha técnica
      <SearchSelect
        ariaLabel="Ficha técnica"
        placeholder="Buscar ficha técnica"
        value={selectedSheet}
        onChange={chooseSheet}
        options={fichas.map((ficha) => ({ value: ficha.id, label: fichaLabel(ficha) }))}
      />
    </label>
    <label>
      Quantidade a produzir ({selectedFicha?.unidade_rendimento ?? 'unidade'})
      <input type="number" min="0.001" step="0.001" value={quantidade} onChange={(event) => setQuantidade(event.target.value)} />
    </label>
    <label>
      Local do produto final
      <SearchSelect
        ariaLabel="Local do produto final"
        placeholder="Buscar localização"
        value={localizacaoId}
        onChange={setLocalizacaoId}
        options={compatibleLocations.map((local) => ({ value: local.id, label: local.nome }))}
      />
    </label>
    <button className="primary" disabled={!podeCriar || ocupado} onClick={create}>Adicionar à fila</button>
  </section>
}
