import type { AcaoPermissao, RecursoPermissao } from '../../../types'

export const rotuloDoRecurso: Record<RecursoPermissao, string> = {
  produtos: 'Produtos',
  fichas_tecnicas: 'Fichas técnicas',
  estoque: 'Estoque',
  localizacoes: 'Localizações',
  producao: 'Produção',
  pracas: 'Praças',
  usuarios: 'Usuários',
  grupos_acesso: 'Grupos de acesso',
}

export const rotuloDaAcao: Record<AcaoPermissao, string> = {
  ler: 'Visualizar',
  criar: 'Criar',
  atualizar: 'Atualizar',
  excluir: 'Excluir',
}

export const ordemDasAcoes: AcaoPermissao[] = ['ler', 'criar', 'atualizar', 'excluir']
