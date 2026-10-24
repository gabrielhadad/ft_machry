# Painel Machry — versão ampliada

Esta versão mantém os scripts e o cadastro de produtos e adiciona telas em `/painel` para estoque, localizações, movimentações e transformações. Não foi enviada ao GitHub.

## Executar

No PowerShell, na pasta do projeto: ` .\run.bat --seed ` (somente banco novo) ou ` .\run.bat ` (uso normal). Acesse http://127.0.0.1:5000/painel. Linux: `chmod +x run.sh && ./run.sh --seed`.

**IMPORTANTE:** copie a pasta do projeto para outro diretório antes de testar, se quiser manter sua base atual. Um ZIP extraído em nova pasta cria um banco novo; para preservar a base antiga, mantenha o diretório `data/` do seu projeto anterior. Nunca execute `init-db` manualmente no banco em uso.

## Testar

1. Em Produtos, confirme o cadastro e crie um item.
2. Em Estoque, crie um lote de produto e localização compatíveis. O saldo começa em zero.
3. Em Movimentações, registre `ENTRADA`, selecione lote e usuário e informe quantidade. Verifique o saldo na aba Estoque.
4. Registre `SAIDA` informando motivo. Teste uma quantidade maior que o saldo: deve ser rejeitada.
5. Para transformar, garanta que os dois produtos estejam cadastrados, que existam dois lotes e que haja saldo na origem. Na aba Transformações, cadastre a relação origem-destino (se ainda não existir); clique em Transformar produto, escolha ambos os lotes, as quantidades de origem e resultado. Consulte o inventário.
6. As quantidades estão na unidade do produto, e a conversão entre unidades diferentes não é automática.

## Limitações

Painel de demonstração, sem autenticação. Usuário responsável é selecionado no formulário, não verificado por login. Não usar em produção sem segurança. Receitas e consumo de múltiplos ingredientes continuam sem integração. Não há edição de lotes/localizações no painel (a API possui algumas rotas). Movimentações não são editáveis nem apagáveis.
