# Hotfix — exclusão de localizações

A exclusão de uma localização agora é bloqueada com HTTP 409 quando:

- a localização possui sub-localizações;
- a localização possui lotes vinculados.

Isso evita que uma restrição de chave estrangeira chegue ao banco como erro interno.

Exemplo: o seed cria `Cozinha` como pai de `Geladeira da Cozinha`, portanto `Cozinha` não pode ser removida antes de mover/remover a localização filha.
