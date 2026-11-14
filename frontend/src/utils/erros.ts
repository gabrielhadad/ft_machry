export function mensagemDeErro(reason: unknown, padrao = 'Não foi possível concluir a operação.') {
  return reason instanceof Error ? reason.message : padrao
}
