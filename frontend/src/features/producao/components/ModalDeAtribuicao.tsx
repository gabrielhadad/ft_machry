import { useState, type FormEvent } from 'react'
import { Modal, SearchSelect } from '../../../components/ui'
import type { Praca, SolicitacaoProducao } from '../../../types'
import { mensagemDeErro } from '../../../utils/erros'

interface ModalDeAtribuicaoProps {
  solicitacao: SolicitacaoProducao
  pracas: Praca[]
  onSalvar: (id: number, pracaId: number | null) => Promise<void>
  onClose: () => void
}

export function ModalDeAtribuicao({ solicitacao, pracas, onSalvar, onClose }: ModalDeAtribuicaoProps) {
  const [pracaId, setPracaId] = useState(solicitacao.praca_id ?? 0)
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState('')
  const atual = solicitacao.praca
  const opcoes = [
    { value: 0, label: 'Sem praça' },
    ...pracas.filter((praca) => praca.ativo === 1).map((praca) => ({ value: praca.id, label: praca.nome })),
  ]
  // Exibe o vínculo antigo mesmo quando a praça foi desativada depois do planejamento.
  if (atual && !opcoes.some((opcao) => opcao.value === atual.id)) {
    opcoes.push({ value: atual.id, label: `${atual.nome} (inativa)` })
  }

  async function salvar(event: FormEvent) {
    event.preventDefault()
    setSalvando(true)
    setErro('')
    try {
      await onSalvar(solicitacao.id, pracaId || null)
      onClose()
    } catch (reason) {
      setErro(mensagemDeErro(reason, 'Não foi possível atribuir a praça.'))
    } finally {
      setSalvando(false)
    }
  }

  return <Modal
    title={`Praça da solicitação #${solicitacao.id}`}
    eyebrow="PLANEJAMENTO"
    onClose={onClose}
    footer={<>
      <button type="button" className="secondary" disabled={salvando} onClick={onClose}>Cancelar</button>
      <button type="submit" form="atribuicao-praca-form" className="primary"
        disabled={salvando || pracaId === (solicitacao.praca_id ?? 0) || (pracaId !== 0 && !pracas.some((praca) => praca.id === pracaId && praca.ativo))}>
        {salvando ? 'Salvando…' : 'Salvar atribuição'}
      </button>
    </>}
  >
    <form id="atribuicao-praca-form" className="dialog-body" onSubmit={salvar}>
      {erro && <p className="form-error" role="alert">{erro}</p>}
      <label>
        Praça responsável
        <SearchSelect ariaLabel="Praça responsável" value={pracaId} onChange={setPracaId} options={opcoes} />
      </label>
      <small>Esta atribuição só pode ser alterada antes do início da produção.</small>
    </form>
  </Modal>
}
