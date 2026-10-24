# Execução e formulário de produtos — Machry

## Para que servem os scripts?
`run.bat` automatiza a execução no Windows e `run.sh` faz o mesmo no Linux/macOS. Criam `.venv` quando necessário, instalam as dependências, inicializam o SQLite **somente na primeira execução** e iniciam o Flask em `127.0.0.1:5000`. Não sobrescrevem o banco existente. Não executam Git nem alteram o repositório remoto.

## Windows
1. Instale Python 3.12+ (habilite **Add Python to PATH**).
2. Extraia o ZIP para uma pasta normal, por exemplo `C:\projetos\ft_machry`.
3. Execute `run.bat` com duplo clique. Para iniciar **um banco novo com dados de demonstração**, execute `run.bat --seed` no CMD da pasta. Se já existir `data/app.db`, `--seed` não altera esse banco.
4. Acesse http://127.0.0.1:5000/painel, Swagger http://127.0.0.1:5000/docs e API http://127.0.0.1:5000/api/produtos.
5. Mantenha o terminal aberto. Para parar, pressione Ctrl+C.

## Linux/macOS
`chmod +x run.sh && ./run.sh` (ou `./run.sh --seed` **na primeira execução**).

## Testar o formulário
1. Clique em **Novo produto**, preencha nome, tipo e unidade, salve.
2. Use a busca e o filtro de tipo.
3. Edite o produto, salve e atualize a página; confirme a persistência.
4. Desative o produto, atualize: ele não deve mais ser listado (exclusão lógica).
5. Feche o servidor e abra de novo: os dados devem permanecer.
6. Verifique erros: nome vazio e cadastro sem unidade devem ser rejeitados.

## Rodar testes automatizados
Ative `.venv` e instale `pytest`: `python -m pip install pytest`; então `python -m pytest -q`. No Windows, pode executar `.venv\Scripts\python.exe -m pytest -q`.

## Observações
- Este painel é um **frontend local de demonstração para CRUD de produtos**, não o frontend final da equipe externa.
- Sem autenticação; a execução está limitada ao localhost para segurança básica. Não exponha o servidor de desenvolvimento na rede ou internet.
- Se Python/pip não conseguem acessar a internet, a instalação automática das dependências pode falhar.
- A página HTML/CSS/JS é local; as fontes externas são opcionais e utilizam substitutas do sistema caso falhem.
- A especificação Swagger permanece como no repositório original (cobre produtos); estoque não foi modificado.
