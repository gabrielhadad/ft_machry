export const unidadesMedida = [
  { valor: 'kg', nome: 'Quilograma (kg)' },
  { valor: 'g', nome: 'Grama (g)' },
  { valor: 'mg', nome: 'Miligrama (mg)' },
  { valor: 'L', nome: 'Litro (L)' },
  { valor: 'ml', nome: 'Mililitro (ml)' },
  { valor: 'un', nome: 'Unidade (un)' },
  { valor: 'pct', nome: 'Pacote (pct)' },
  { valor: 'cx', nome: 'Caixa (cx)' },
  { valor: 'dz', nome: 'Dúzia (dz)' },
  { valor: 'pç', nome: 'Peça (pç)' },
] as const

export const unidadesPermitidas = new Set<string>(unidadesMedida.map((item) => item.valor))
