import { useState } from 'react'
import { Modal } from '../../../components/ui'
import { baixarCsv } from '../../../utils/csv'
import { mensagemDeErro } from '../../../utils/erros'
import { importarFichas } from '../api/fichasApi'
import { converterFichasCsv, fasesEmOrdem, fichaColunas, fichaModelo, numeroCsv, type FichaCsv } from '../utils/csvFichas'

interface SheetImportModalProps {
  onClose: () => void
  onSaved: (total: number, fasesCriadas: string[], ignoradas: string[]) => void
}

export function SheetImportModal({ onClose, onSaved }: SheetImportModalProps) {
  const [arquivo, setArquivo] = useState('')
  const [fichas, setFichas] = useState<FichaCsv[]>([])
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  const comErro = fichas.filter((item) => item.erros.length)

  async function selecionar(file: File | undefined) {
    setError('')
    setFichas([])
    setArquivo(file?.name ?? '')
    if (!file) return
    const resultado = converterFichasCsv(await file.text())
    setFichas(resultado.fichas)
    if (resultado.erro) setError(resultado.erro)
  }

  async function importar() {
    setSaving(true)
    setError('')
    try {
      const corpo = fichas.map((ficha) => ({
        produto: ficha.nome,
        rendimento: String(numeroCsv(ficha.rendimento)),
        observacao: ficha.observacoes.join('\n') || null,
        fases: fasesEmOrdem(ficha),
        componentes: ficha.componentes,
      }))
      const resposta = await importarFichas(corpo)
      onSaved(resposta.total, resposta.fases_criadas, resposta.ignoradas)
    } catch (reason) {
      const mensagem = mensagemDeErro(reason, 'Não foi possível importar as fichas.')
      setError(mensagem.replace(/^ficha (\d+) \(/, (_, n: string) => `Linha ${fichas[Number(n) - 1]?.linhas[0] ?? n} (`))
    } finally {
      setSaving(false)
    }
  }

  const footer = <>
    <button className="secondary" onClick={onClose} type="button">Cancelar</button>
    <button className="primary" type="button" onClick={() => void importar()} disabled={saving || !fichas.length || comErro.length > 0}>
      {saving ? 'Importando…' : `Importar ${fichas.length || ''} ficha(s)`}
    </button>
  </>

  return <Modal eyebrow="PADRONIZAÇÃO" title="Importar fichas técnicas (CSV)" wide onClose={onClose} footer={footer}>
    <div className="dialog-body">
      {error && <p className="form-error">{error}</p>}
      <p>Uma linha por componente; as linhas com o mesmo nome em <code>ficha</code> formam uma receita. Colunas: <code>{fichaColunas.join(';')}</code>.</p>
      <p>
        Produtos e fases são buscados pelo nome (sem diferenciar maiúsculas e acentos).
        A ficha precisa ser de um produto intermediário ou final já cadastrado;
        fases que não existem são criadas e produtos que já têm ficha são ignorados.
        Em <code>unidade</code>, g/mg/kg e ml/L são convertidos para a unidade do produto.
        Quantidade <code>q.b.</code> vira “a gosto” na observação.
        A importação é feita por completo ou não é feita.
      </p>
      <button className="text-button" type="button" onClick={() => baixarCsv('modelo-fichas-tecnicas.csv', fichaModelo)}>Baixar modelo CSV →</button>
      <label>
        Arquivo CSV
        <input type="file" accept=".csv,text/csv" onChange={(event) => void selecionar(event.target.files?.[0])} />
      </label>
      {arquivo && fichas.length > 0 && <>
        <p>{fichas.length} ficha(s) em {arquivo}{comErro.length ? ` · ${comErro.length} com erro` : ''}.</p>
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>Linhas</th><th>Ficha</th><th>Rendimento</th><th>Fases</th><th>Componentes</th><th>A gosto</th><th>Status</th></tr>
            </thead>
            <tbody>
              {fichas.map((ficha) => <tr key={ficha.linhas[0]}>
                <td>{ficha.linhas[0]}–{ficha.linhas[ficha.linhas.length - 1]}</td>
                <td><strong>{ficha.nome}</strong></td>
                <td>{ficha.rendimento || '—'}</td>
                <td>{fasesEmOrdem(ficha).map((fase) => `${fase.ordem}. ${fase.fase}`).join(', ') || '—'}</td>
                <td>{ficha.componentes.filter((item) => item.quantidade).length}</td>
                <td>{ficha.componentes.filter((item) => !item.quantidade).map((item) => item.produto).join(', ') || '—'}</td>
                <td>{ficha.erros.length ? <span className="form-error">{ficha.erros.join('; ')}</span> : 'OK'}</td>
              </tr>)}
            </tbody>
          </table>
        </div>
      </>}
    </div>
  </Modal>
}
