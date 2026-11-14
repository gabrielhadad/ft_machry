import { useState } from 'react'
import { Modal } from '../../../components/ui'
import { baixarCsv } from '../../../utils/csv'
import { mensagemDeErro } from '../../../utils/erros'
import { importarProdutos } from '../api/produtosApi'
import { converterProdutosCsv, csvColunas, csvModelo, type LinhaCsv } from '../utils/csvProdutos'

interface ProductImportModalProps {
  onClose: () => void
  onSaved: (total: number, ignorados: string[]) => void
}

export function ProductImportModal({ onClose, onSaved }: ProductImportModalProps) {
  const [arquivo, setArquivo] = useState('')
  const [linhas, setLinhas] = useState<LinhaCsv[]>([])
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  const comErro = linhas.filter((item) => item.erros.length)

  async function selecionar(file: File | undefined) {
    setError('')
    setLinhas([])
    setArquivo(file?.name ?? '')
    if (!file) return
    const resultado = converterProdutosCsv(await file.text())
    setLinhas(resultado.linhas)
    if (resultado.erro) setError(resultado.erro)
  }

  async function importar() {
    setSaving(true)
    setError('')
    try {
      const resposta = await importarProdutos(linhas.map((item) => item.dados))
      onSaved(resposta.total, resposta.ignorados)
    } catch (reason) {
      const mensagem = mensagemDeErro(reason, 'Não foi possível importar os produtos.')
      setError(mensagem.replace(/^produto (\d+):/, (_, n: string) => `Linha ${linhas[Number(n) - 1]?.linha ?? n}:`))
    } finally {
      setSaving(false)
    }
  }

  const footer = <>
    <button className="secondary" onClick={onClose} type="button">Cancelar</button>
    <button className="primary" type="button" onClick={() => void importar()} disabled={saving || !linhas.length || comErro.length > 0}>
      {saving ? 'Importando…' : `Importar ${linhas.length || ''} produto(s)`}
    </button>
  </>

  return <Modal eyebrow="CATÁLOGO" title="Importar produtos (CSV)" wide onClose={onClose} footer={footer}>
    <div className="dialog-body">
      {error && <p className="form-error">{error}</p>}
      <p>
        Colunas: <code>{csvColunas.join(';')}</code>.
        Obrigatórias: nome, tipo (INSUMO, INTERMEDIARIO ou FINAL) e unidade_medida.
        Conservação padrão: SECO.
        Produtos com o mesmo nome e conservação de um já cadastrado são ignorados.
        A importação é feita por completo ou não é feita.
      </p>
      <button className="text-button" type="button" onClick={() => baixarCsv('modelo-produtos.csv', csvModelo)}>Baixar modelo CSV →</button>
      <label>
        Arquivo CSV
        <input type="file" accept=".csv,text/csv" onChange={(event) => void selecionar(event.target.files?.[0])} />
      </label>
      {arquivo && linhas.length > 0 && <>
        <p>{linhas.length} produto(s) em {arquivo}{comErro.length ? ` · ${comErro.length} linha(s) com erro` : ''}.</p>
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>Linha</th><th>Nome</th><th>Tipo</th><th>Unidade</th><th>Subdivisão</th><th>Conservação</th><th>Validade</th><th>Status</th></tr>
            </thead>
            <tbody>
              {linhas.map(({ linha, dados, erros }) => <tr key={linha}>
                <td>{linha}</td>
                <td><strong>{String(dados.nome || '—')}</strong></td>
                <td>{String(dados.tipo ?? '—')}</td>
                <td>{String(dados.unidade_medida || '—')}</td>
                <td>{String(dados.subdivisao ?? '—')}</td>
                <td>{String(dados.conservacao ?? '—')}</td>
                <td>{dados.validade_padrao_dias == null ? '—' : `${dados.validade_padrao_dias} dias`}{dados.validade_obrigatoria ? ' (obrigatória)' : ''}</td>
                <td>{erros.length ? <span className="form-error">{erros.join('; ')}</span> : 'OK'}</td>
              </tr>)}
            </tbody>
          </table>
        </div>
      </>}
    </div>
  </Modal>
}
