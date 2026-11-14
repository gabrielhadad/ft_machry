function semAcentos(valor: string) {
  return valor.normalize('NFD').replace(/[̀-ͯ]/g, '')
}

export function normalizeSearch(value: string) {
  return semAcentos(value).trim().toLocaleLowerCase('pt-BR')
}

export function normalizarChave(valor: string) {
  return semAcentos(valor).trim().toUpperCase()
}
