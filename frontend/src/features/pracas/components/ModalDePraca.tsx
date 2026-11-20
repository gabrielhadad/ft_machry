import { useState, type FormEvent } from 'react'
import { Modal, SearchSelect } from '../../../components/ui'
import type { CozinheiroResumo, Praca } from '../../../types'
import { mensagemDeErro } from '../../../utils/erros'
import { atualizarPraca, criarPraca, type AlteracaoDePraca } from '../api/pracasApi'

interface ModalDePracaProps {
  praca: Praca | null
  cozinheiros: CozinheiroResumo[]
  onClose: () => void
  onSalva: (mensagem: string) => Promise<void>
}

function mesmosIds(ids: number[], outros: number[]) {
  return ids.length === outros.length && ids.every((id) => outros.includes(id))
}

export function ModalDePraca({ praca, cozinheiros, onClose, onSalva }: ModalDePracaProps) {
  const [nome, setNome] = useState(praca?.nome ?? '')
  const [descricao, setDescricao] = useState(praca?.descricao ?? '')
  const [ativo, setAtivo] = useState(praca?.ativo ?? 1)
  const [selecionados, setSelecionados] = useState<number[]>(
    praca?.cozinheiros.map((cozinheiro) => cozinheiro.id) ?? [],
  )
  const [erro, setErro] = useState('')
  const [salvando, setSalvando] = useState(false)
  const candidatos = cozinheiros.filter((cozinheiro) => !selecionados.includes(cozinheiro.id))
  const selecionadosDetalhes = selecionados.map((id) => (
    cozinheiros.find((usuario) => usuario.id === id) ?? praca?.cozinheiros.find((usuario) => usuario.id === id)
  )).filter((usuario): usuario is CozinheiroResumo => usuario !== undefined)
  const alterouEquipe = !praca || !mesmosIds(selecionados, praca.cozinheiros.map((cozinheiro) => cozinheiro.id))
  const alterou = !praca || nome.trim() !== praca.nome || (descricao.trim() || null) !== praca.descricao ||
    ativo !== praca.ativo || alterouEquipe

  async function salvar(event: FormEvent) {
    event.preventDefault()
    if (selecionados.length === 0 || !alterou) return
    setSalvando(true)
    setErro('')
    try {
      const descricaoTratada = descricao.trim() || null
      if (praca) {
        const dados: AlteracaoDePraca = {}
        if (nome.trim() !== praca.nome) dados.nome = nome.trim()
        if (descricaoTratada !== praca.descricao) dados.descricao = descricaoTratada
        if (ativo !== praca.ativo) dados.ativo = ativo
        // Só atualiza a equipe quando ela mudou; preserva vínculos históricos inalterados.
        if (alterouEquipe) dados.cozinheiros = selecionados
        await atualizarPraca(praca.id, dados)
      } else {
        await criarPraca({ nome: nome.trim(), descricao: descricaoTratada, cozinheiros: selecionados })
      }
      await onSalva(praca ? 'Praça atualizada com sucesso.' : 'Praça cadastrada com sucesso.')
    } catch (reason) {
      setErro(mensagemDeErro(reason, 'Não foi possível salvar a praça.'))
    } finally {
      setSalvando(false)
    }
  }

  return <Modal
    eyebrow="EQUIPE DA COZINHA"
    title={praca ? 'Editar praça' : 'Nova praça'}
    onClose={onClose}
    footer={<>
      <button type="button" className="secondary" disabled={salvando} onClick={onClose}>Cancelar</button>
      <button type="submit" className="primary" form="praca-form"
        disabled={salvando || selecionados.length === 0 || !alterou}>
        {salvando ? 'Salvando…' : praca ? 'Salvar alterações' : 'Criar praça'}
      </button>
    </>}
  >
    <form id="praca-form" className="dialog-body" onSubmit={salvar}>
      {erro && <p className="form-error" role="alert">{erro}</p>}
      <label>
        Nome da praça
        <input autoFocus required minLength={2} maxLength={120} value={nome}
          placeholder="Ex.: Grelha, Saladas, Sobremesas"
          onChange={(event) => setNome(event.target.value)} />
      </label>
      <label>
        Descrição (opcional)
        <textarea rows={3} value={descricao} onChange={(event) => setDescricao(event.target.value)} />
      </label>
      {praca && <label>
        Situação
        <SearchSelect ariaLabel="Situação da praça" value={ativo} onChange={setAtivo}
          options={[{ value: 1, label: 'Ativa' }, { value: 0, label: 'Inativa' }]} />
      </label>}
      <div className="praca-selecao">
        <label>
          Cozinheiros (mínimo de 1)
          <SearchSelect<number | ''>
            ariaLabel="Adicionar cozinheiro à praça"
            value=""
            disabled={salvando || candidatos.length === 0}
            placeholder={candidatos.length ? 'Buscar cozinheiro' : 'Nenhum outro cozinheiro disponível'}
            options={candidatos.map((cozinheiro) => ({
              value: cozinheiro.id,
              label: `${cozinheiro.nome} (${cozinheiro.username})`,
            }))}
            onChange={(id) => {
              if (id !== '') setSelecionados((ids) => ids.includes(id) ? ids : [...ids, id])
            }}
          />
        </label>
        {selecionadosDetalhes.length > 0 ? <div className="praca-chips" aria-label="Cozinheiros selecionados">
          {selecionadosDetalhes.map((cozinheiro) => <button
            key={cozinheiro.id}
            type="button"
            className="praca-chip"
            disabled={salvando}
            aria-label={`Remover ${cozinheiro.nome} da praça`}
            title={`Remover ${cozinheiro.nome}`}
            onClick={() => setSelecionados((ids) => ids.filter((id) => id !== cozinheiro.id))}
          >{cozinheiro.nome} ×</button>)}
        </div> : <small>Selecione ao menos um cozinheiro para cadastrar ou atualizar a praça.</small>}
      </div>
    </form>
  </Modal>
}
