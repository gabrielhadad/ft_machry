import os

import click
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import URL, event, inspect, text
from werkzeug.security import generate_password_hash


db = SQLAlchemy()


def _montar_database_uri(config: dict):
    if config.get("DATABASE_URL"):
        return config["DATABASE_URL"]

    conexao = str(config.get("DB_CONNECTION", "sqlite")).lower()
    if conexao in {"postgres", "postgresql"}:
        return URL.create(
            "postgresql+psycopg2",
            username=config["DB_USERNAME"],
            password=config["DB_PASSWORD"],
            host=config["DB_HOST"],
            port=int(config["DB_PORT"]),
            database=config["DB_DATABASE"],
        )
    if conexao != "sqlite":
        raise ValueError("DB_CONNECTION deve ser sqlite, postgres ou postgresql")

    caminho = os.path.abspath(config["DATABASE_PATH"]).replace("\\", "/")
    os.makedirs(os.path.dirname(caminho) or ".", exist_ok=True)
    return f"sqlite:///{caminho}"


def _configurar_sqlite(engine) -> None:
    @event.listens_for(engine, "connect")
    def _configurar_conexao(conexao_dbapi, _):
        conexao_dbapi.execute("PRAGMA foreign_keys = ON")
        conexao_dbapi.isolation_level = None

    @event.listens_for(engine, "begin")
    def _begin_immediate(conexao):
        conexao.exec_driver_sql("BEGIN IMMEDIATE")


def _tabelas_existem(engine) -> bool:
    return inspect(engine).has_table("usuario")


def _migrar_autenticacao() -> None:
    colunas = {coluna["name"] for coluna in inspect(db.engine).get_columns("usuario")}
    if "username" not in colunas:
        db.session.execute(text("ALTER TABLE usuario ADD COLUMN username VARCHAR(80)"))
    if "senha_hash" not in colunas:
        db.session.execute(text("ALTER TABLE usuario ADD COLUMN senha_hash VARCHAR(255)"))
    db.session.commit()



def _migrar_produto() -> None:
    colunas = {coluna["name"] for coluna in inspect(db.engine).get_columns("produto")}
    if "subdivisao" not in colunas:
        db.session.execute(text("ALTER TABLE produto ADD COLUMN subdivisao TEXT"))
    db.session.commit()


def _migrar_lote() -> None:
    colunas = {coluna["name"] for coluna in inspect(db.engine).get_columns("lote")}
    for coluna in ("fornecedor", "nota_fiscal"):
        if coluna not in colunas:
            db.session.execute(text(f"ALTER TABLE lote ADD COLUMN {coluna} TEXT"))
    db.session.commit()


def _migrar_producao() -> None:
    colunas = {
        coluna["name"]
        for coluna in inspect(db.engine).get_columns("solicitacao_producao")
    }
    if "quantidade_planejada" not in colunas:
        db.session.execute(text(
            "ALTER TABLE solicitacao_producao "
            "ADD COLUMN quantidade_planejada NUMERIC NOT NULL DEFAULT 1"
        ))
        db.session.execute(text(
            "UPDATE solicitacao_producao SET quantidade_planejada = "
            "COALESCE((SELECT rendimento FROM ficha_tecnica "
            "WHERE ficha_tecnica.id = solicitacao_producao.ficha_tecnica_id), 1)"
        ))
    if "localizacao_destino_id" not in colunas:
        db.session.execute(text(
            "ALTER TABLE solicitacao_producao "
            "ADD COLUMN localizacao_destino_id INTEGER REFERENCES localizacao(id)"
        ))
    db.session.commit()


def _migrar_pracas() -> None:
    """Adiciona o vínculo opcional em bases já existentes, sem alterar as produções."""
    colunas = {
        coluna["name"]
        for coluna in inspect(db.engine).get_columns("solicitacao_producao")
    }
    if "praca_id" not in colunas:
        db.session.execute(text(
            "ALTER TABLE solicitacao_producao "
            "ADD COLUMN praca_id INTEGER REFERENCES praca(id)"
        ))
    # CREATE ALL não cria índices novos em tabelas que já existiam.
    db.session.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_solicitacao_producao_praca_id "
        "ON solicitacao_producao (praca_id)"
    ))
    db.session.execute(text(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_praca_nome_normalizado "
        "ON praca (lower(nome))"
    ))
    db.session.commit()


def _sincronizar_permissoes() -> None:
    from app.features.acessos.models import Permissao
    from app.utils.permissoes import catalogo_de_permissoes

    existentes = {
        permissao.codigo: permissao
        for permissao in db.session.execute(db.select(Permissao)).scalars()
    }
    codigos_do_catalogo = set()
    for item in catalogo_de_permissoes():
        codigos_do_catalogo.add(item["codigo"])
        permissao = existentes.get(item["codigo"])
        if permissao is None:
            db.session.add(Permissao(**item))
        else:
            permissao.recurso = item["recurso"]
            permissao.acao = item["acao"]
            permissao.descricao = item["descricao"]
    for codigo, permissao in existentes.items():
        if codigo not in codigos_do_catalogo:
            db.session.delete(permissao)
    db.session.commit()


def _grupos_por_nome() -> dict:
    from app.features.acessos.models import GrupoAcesso

    grupos = db.session.execute(db.select(GrupoAcesso)).scalars()
    return {grupo.nome: grupo for grupo in grupos}


def _criar_grupos_padrao() -> None:
    from app.features.acessos.models import GrupoAcesso, Permissao
    from app.utils.enums import GrupoPadrao
    from app.utils.permissoes import permissoes_do_grupo_padrao

    permissoes = {
        permissao.codigo: permissao
        for permissao in db.session.execute(db.select(Permissao)).scalars()
    }
    grupos = _grupos_por_nome()
    for padrao in GrupoPadrao:
        grupo = grupos.get(padrao.value)
        if grupo is None:
            grupo = GrupoAcesso(
                nome=padrao.value,
                descricao=padrao.descricao,
                protegido=int(padrao.protegido),
            )
            grupo.permissoes = [permissoes[codigo] for codigo in permissoes_do_grupo_padrao(padrao)]
            db.session.add(grupo)
        elif grupo.protegido:
            grupo.permissoes = list(permissoes.values())
    db.session.commit()


def _migrar_papeis_para_grupos() -> None:
    from app.features.acessos.models import UsuarioGrupoAcesso
    from app.features.usuarios.models import Usuario
    from app.utils.enums import PapelAntigo

    colunas = {coluna["name"] for coluna in inspect(db.engine).get_columns("usuario")}
    if "papel" not in colunas:
        return
    vinculos = db.session.execute(
        db.select(db.func.count()).select_from(UsuarioGrupoAcesso)
    ).scalar_one()
    if vinculos > 0:
        return

    grupos = _grupos_por_nome()
    for usuario_id, papel in db.session.execute(text("SELECT id, papel FROM usuario")).all():
        if papel not in PapelAntigo.valores():
            continue
        grupo = grupos.get(PapelAntigo(papel).grupo.value)
        if grupo is not None:
            usuario = db.session.get(Usuario, usuario_id)
            usuario.grupos.append(grupo)
    db.session.commit()

    if db.engine.dialect.name == "postgresql":
        db.session.execute(text("ALTER TABLE usuario DROP COLUMN papel"))
        db.session.commit()


def _provisionar_usuarios_iniciais() -> None:
    from flask import current_app

    from app.features.usuarios.models import Usuario
    from app.features.usuarios.repository import UsuarioRepository
    from app.utils.enums import GrupoPadrao

    config = current_app.config
    contas = [
        (
            "Proprietária",
            config["OWNER_USERNAME"],
            config["OWNER_INITIAL_PASSWORD"],
            GrupoPadrao.ADMINISTRADOR,
        ),
        (
            "Gestor",
            config["MANAGER_USERNAME"],
            config["MANAGER_INITIAL_PASSWORD"],
            GrupoPadrao.GESTOR,
        ),
        (
            "Cozinha",
            config["COOK_USERNAME"],
            config["COOK_INITIAL_PASSWORD"],
            GrupoPadrao.COZINHA,
        ),
    ]
    repositorio = UsuarioRepository()
    grupos = _grupos_por_nome()
    for nome, username, password, grupo in contas:
        username = username.strip().lower()
        if repositorio.obter_por_username(username) is None:
            usuario = Usuario(
                nome=nome, username=username, senha_hash=generate_password_hash(password)
            )
            usuario.grupos.append(grupos[grupo.value])
            db.session.add(usuario)
    db.session.commit()

    _garantir_administrador_ativo(config["OWNER_USERNAME"].strip().lower())

    db.session.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_usuario_username ON usuario (username)"))
    db.session.commit()


def _garantir_administrador_ativo(username_da_proprietaria: str) -> None:
    from app.features.usuarios.repository import UsuarioRepository
    from app.utils.enums import GrupoPadrao

    grupo = _grupos_por_nome()[GrupoPadrao.ADMINISTRADOR.value]
    if any(usuario.ativo for usuario in grupo.usuarios):
        return
    proprietaria = UsuarioRepository().obter_por_username(username_da_proprietaria)
    proprietaria.ativo = 1
    if grupo not in proprietaria.grupos:
        proprietaria.grupos.append(grupo)
    db.session.commit()


def _sincronizar_acessos() -> None:
    _sincronizar_permissoes()
    _criar_grupos_padrao()
    _migrar_papeis_para_grupos()
    _provisionar_usuarios_iniciais()


VIEWS = {
    "vw_inventario": """
        SELECT p.id AS produto_id, p.nome AS produto, p.tipo AS tipo_produto,
               p.unidade_medida, l.id AS lote_id, l.quantidade,
               l.data_validade, loc.nome AS localizacao
          FROM lote l
          JOIN produto p ON p.id = l.produto_id
          JOIN localizacao loc ON loc.id = l.localizacao_id
         WHERE l.quantidade > 0
    """,
    "vw_fifo": """
        SELECT l.* FROM lote l WHERE l.quantidade > 0
         ORDER BY l.produto_id, l.data_validade ASC, l.criado_em ASC
    """,
    "vw_sp_componente": """
        SELECT c.id AS sp_componente_id, c.solicitacao_producao_id,
               c.produto_id, p.nome AS componente, p.unidade_medida,
               sf.ordem AS fase_ordem, fp.nome AS fase,
               c.quantidade_prevista,
               COALESCE(SUM(m.quantidade), 0) AS quantidade_realizada,
               SUM(m.quantidade * l.custo_unitario) AS custo_realizado
          FROM sp_componente c
          JOIN produto p ON p.id = c.produto_id
          LEFT JOIN sp_fase sf ON sf.id = c.sp_fase_id
          LEFT JOIN fase_producao fp ON fp.id = sf.fase_id
          LEFT JOIN movimentacao_estoque m
                 ON m.sp_componente_id = c.id AND m.tipo = 'CONSUMO_PRODUCAO'
          LEFT JOIN lote l ON l.id = m.lote_id
         GROUP BY c.id, c.solicitacao_producao_id, c.produto_id, p.nome,
                  p.unidade_medida, sf.ordem, fp.nome, c.quantidade_prevista
    """,
    "vw_sp_producao": """
        SELECT m.solicitacao_producao_id, m.lote_id, m.quantidade, m.criado_em
          FROM movimentacao_estoque m WHERE m.tipo = 'PRODUCAO'
    """,
}


def _criar_views() -> None:
    for nome, consulta in VIEWS.items():
        db.session.execute(text(f"CREATE VIEW {nome} AS {consulta}"))
    db.session.commit()


@click.command("init-db")
@click.option("--seed", is_flag=True, help="Também carrega os dados de exemplo.")
def init_db_command(seed: bool):
    if _tabelas_existem(db.engine):
        db.create_all()
        _migrar_autenticacao()
        _migrar_produto()
        _migrar_lote()
        _migrar_producao()
        _migrar_pracas()
        _sincronizar_acessos()
        click.echo("Banco já criado e atualizado")
        return

    db.create_all()
    _criar_views()
    if seed:
        from db.seed import carregar_seeds

        carregar_seeds()
    _sincronizar_acessos()
    click.echo("Banco inicializado." + (" (com seeds)" if seed else ""))


def _tabelas_do_catalogo() -> list:
    """Tabela `produto` e todas as que dependem dela (fichas, estoque, produção), na ordem de exclusão."""
    alvo = {"produto"}
    mudou = True
    while mudou:
        mudou = False
        for tabela in db.metadata.tables.values():
            if tabela.name not in alvo and any(fk.column.table.name in alvo for fk in tabela.foreign_keys):
                alvo.add(tabela.name)
                mudou = True
    return [t for t in reversed(db.metadata.sorted_tables) if t.name in alvo]


@click.command("limpar-catalogo")
@click.option("--sim", is_flag=True, help="Não pede confirmação.")
def limpar_catalogo_command(sim: bool):
    """Apaga produtos e fichas técnicas (e lotes, estoque e produção ligados a eles).

    Usuários, fases de produção, grupos e localizações são mantidos.
    """
    tabelas = _tabelas_do_catalogo()
    nomes = ", ".join(t.name for t in tabelas)
    if not sim:
        click.confirm(f"Apagar todos os registros de: {nomes}?", abort=True)
    for tabela in tabelas:
        db.session.execute(tabela.delete())
    db.session.commit()
    click.echo(f"Catálogo limpo: {nomes}.")


def init_app(app: Flask):
    if "SQLALCHEMY_DATABASE_URI" not in app.config:
        app.config["SQLALCHEMY_DATABASE_URI"] = _montar_database_uri(app.config)
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)

    db.init_app(app)
    with app.app_context():
        if db.engine.dialect.name == "sqlite":
            _configurar_sqlite(db.engine)

    app.cli.add_command(init_db_command)
    app.cli.add_command(limpar_catalogo_command)
