const BOM = '﻿'

export function lerCsv(conteudo: string): string[][] {
  const texto = conteudo.startsWith(BOM) ? conteudo.slice(1) : conteudo
  const primeira = texto.split(/\r?\n/, 1)[0] ?? ''
  const sep = (primeira.match(/;/g)?.length ?? 0) >= (primeira.match(/,/g)?.length ?? 0) ? ';' : ','
  const linhas: string[][] = []
  let linha: string[] = []
  let campo = ''
  let aspas = false
  for (let i = 0; i < texto.length; i += 1) {
    const c = texto[i]
    if (aspas) {
      if (c === '"' && texto[i + 1] === '"') { campo += '"'; i += 1 }
      else if (c === '"') aspas = false
      else campo += c
    } else if (c === '"') aspas = true
    else if (c === sep) { linha.push(campo); campo = '' }
    else if (c === '\n' || c === '\r') {
      if (c === '\r' && texto[i + 1] === '\n') i += 1
      linha.push(campo); linhas.push(linha); linha = []; campo = ''
    } else campo += c
  }
  if (campo || linha.length) { linha.push(campo); linhas.push(linha) }
  return linhas
}

export function baixarCsv(nomeDoArquivo: string, conteudo: string) {
  const url = URL.createObjectURL(new Blob([BOM + conteudo], { type: 'text/csv;charset=utf-8' }))
  const link = Object.assign(document.createElement('a'), { href: url, download: nomeDoArquivo })
  link.click()
  URL.revokeObjectURL(url)
}
