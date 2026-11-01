export type TipoProduto = 'INSUMO' | 'INTERMEDIARIO' | 'FINAL'
export type Conservacao = 'SECO' | 'RESFRIADO' | 'CONGELADO'
export type PapelUsuario = 'OWNER' | 'ADMIN' | 'USER'

export interface Usuario {
  id: number
  nome: string
  username: string
  papel: PapelUsuario
  ativo: number
  deve_trocar_senha: number
}

export interface Produto {
  id: number
  nome: string
  tipo: TipoProduto
  unidade_medida: string
  grupo_id: number | null
  conservacao: Conservacao
  validade_obrigatoria: number
  validade_padrao_dias: number | null
  foto_url: string | null
  ativo: number
  criado_em: string
}

export interface FaseCatalogo {
  id: number
  nome: string
}

export interface FichaFase {
  id: number
  fase_id: number
  fase: string
  ordem: number
  tempo_previsto_min: number
}

export interface FichaComponente {
  id: number
  produto_id: number
  produto: string
  unidade_medida: string
  quantidade: number
  ficha_tecnica_fase_id: number | null
  fase_ordem: number | null
}

export interface FichaTecnica {
  id: number
  produto_id: number
  produto: string
  unidade_rendimento: string
  rendimento: number
  observacao: string | null
  fases: FichaFase[]
  componentes: FichaComponente[]
}

export interface ItemInventario {
  produto_id: number
  produto: string
  tipo_produto: TipoProduto
  unidade_medida: string
  lote_id: number
  quantidade: number
  data_validade: string | null
  localizacao: string
}

export interface Localizacao {
  id: number
  nome: string
  tipo: Conservacao
  parent_id: number | null
  foto_url: string | null
}

export interface Lote {
  id: number
  produto_id: number
  produto: string
  localizacao_id: number
  localizacao: string
  quantidade: number
  data_producao: string | null
  data_validade: string | null
  custo_unitario: number | null
  criado_em: string
}

export interface TransformacaoDisponivel {
  produto_origem_id: number
  produto_destino_id: number
  produto_destino: string
  unidade_medida: string
  conservacao: Conservacao
}

export interface SolicitacaoProducao {
  id: number
  ficha_tecnica_id: number
  usuario_id: number
  responsavel_id: number | null
  quantidade_planejada: number
  quantidade_produzida: number | null
  prioridade: 'BAIXA' | 'NORMAL' | 'ALTA' | 'URGENTE'
  previsto_para: string | null
  observacao: string | null
  observacao_execucao: string | null
  status: string
  criado_em: string
  iniciado_em: string | null
  concluido_em: string | null
  perda_rendimento: number | null
}

export interface ComponenteSolicitacao {
  sp_componente_id: number
  solicitacao_producao_id: number
  produto_id: number
  componente: string
  unidade_medida: string
  fase_ordem: number | null
  fase: string | null
  quantidade_prevista: number
  quantidade_realizada: number
  custo_realizado: number | null
}

export interface FaseSolicitacao {
  sp_fase_id: number
  fase_id: number
  ordem: number
  fase: string
  tempo_previsto_min: number
  tempo_realizado_min: number | null
  observacao: string | null
  iniciado_em: string | null
  finalizado_em: string | null
}

export interface LoteProduzido {
  solicitacao_producao_id: number
  lote_id: number
  quantidade: number
  criado_em: string
}

export interface SolicitacaoDetalhe {
  solicitacao: SolicitacaoProducao
  componentes: ComponenteSolicitacao[]
  fases: FaseSolicitacao[]
  lotes_produzidos: LoteProduzido[]
}

export interface PlanejamentoProducaoInput {
  ficha_tecnica_id: number
  quantidade_planejada?: number
  prioridade: SolicitacaoProducao['prioridade']
  previsto_para?: string | null
  responsavel_id?: number | null
  observacao?: string | null
}

export type View =
  | 'inicio'
  | 'produtos'
  | 'fichas'
  | 'estoque'
  | 'producao'
  | 'historico'
  | 'locais'
  | 'usuarios'
