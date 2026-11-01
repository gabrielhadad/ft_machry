import os
import sqlite3
import subprocess
import sys
from pathlib import Path


def test_baseline_alembic_cria_schema_e_views(tmp_path):
    root = Path(__file__).resolve().parents[1]
    database = tmp_path / "migration.db"
    env = os.environ.copy()
    env.update(
        {
            "DB_CONNECTION": "sqlite",
            "DATABASE_PATH": str(database),
            "SECRET_KEY": "migration-test-secret",
        }
    )

    resultado = subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "-c",
            "migrations/alembic.ini",
            "upgrade",
            "head",
        ],
        cwd=root,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr

    with sqlite3.connect(database) as conexao:
        objetos = {
            (tipo, nome)
            for tipo, nome in conexao.execute(
                "SELECT type, name FROM sqlite_master WHERE type IN ('table', 'view')"
            )
        }
        revisao = conexao.execute("SELECT version_num FROM alembic_version").fetchone()
        colunas_solicitacao = {
            linha[1] for linha in conexao.execute("PRAGMA table_info(solicitacao_producao)")
        }
        colunas_usuario = {
            linha[1] for linha in conexao.execute("PRAGMA table_info(usuario)")
        }
        indices_solicitacao = {
            linha[1] for linha in conexao.execute("PRAGMA index_list(solicitacao_producao)")
        }
        sql_movimentacao = conexao.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'movimentacao_estoque'"
        ).fetchone()[0]
        sql_view_componente = conexao.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'view' AND name = 'vw_sp_componente'"
        ).fetchone()[0]

    assert revisao == ("e7f8a9b0c1d2",)
    assert "PERDA" in sql_movimentacao
    assert "PERDA" in sql_view_componente
    assert ("table", "produto") in objetos
    assert ("table", "solicitacao_producao") in objetos
    assert ("table", "movimentacao_estoque") in objetos
    assert ("table", "auditoria") in objetos
    assert ("view", "vw_inventario") in objetos
    assert ("view", "vw_fefo") in objetos
    assert ("view", "vw_fifo") not in objetos
    assert ("view", "vw_sp_componente") in objetos
    assert ("view", "vw_sp_producao") in objetos
    assert {
        "responsavel_id",
        "quantidade_planejada",
        "quantidade_produzida",
        "prioridade",
        "previsto_para",
        "observacao",
        "observacao_execucao",
        "iniciado_em",
    }.issubset(colunas_solicitacao)
    assert "idx_solicitacao_planejamento" in indices_solicitacao
    assert {"deve_trocar_senha", "login_falhas", "bloqueado_ate", "ultimo_login_em", "senha_alterada_em"}.issubset(colunas_usuario)


def test_migration_planejamento_preserva_solicitacoes_existentes(tmp_path):
    root = Path(__file__).resolve().parents[1]
    database = tmp_path / "migration-existing.db"
    env = os.environ.copy()
    env.update(
        {
            "DB_CONNECTION": "sqlite",
            "DATABASE_PATH": str(database),
            "SECRET_KEY": "migration-existing-secret",
        }
    )

    anterior = subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "-c",
            "migrations/alembic.ini",
            "upgrade",
            "8a3c1d4e5f67",
        ],
        cwd=root,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert anterior.returncode == 0, anterior.stdout + anterior.stderr

    with sqlite3.connect(database) as conexao:
        conexao.execute(
            "INSERT INTO usuario (id, nome, username, senha_hash, papel, ativo) "
            "VALUES (1, 'Gestor', 'gestor', 'hash', 'ADMIN', 1)"
        )
        conexao.execute(
            "INSERT INTO produto (id, nome, tipo, unidade_medida, conservacao, validade_obrigatoria, ativo) "
            "VALUES (1, 'Produto final', 'FINAL', 'un', 'SECO', 0, 1)"
        )
        conexao.execute(
            "INSERT INTO ficha_tecnica (id, produto_id, rendimento) VALUES (1, 1, 10)"
        )
        conexao.execute(
            "INSERT INTO solicitacao_producao (id, ficha_tecnica_id, usuario_id, status) "
            "VALUES (1, 1, 1, 'ABERTA')"
        )
        conexao.commit()

    atual = subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "-c",
            "migrations/alembic.ini",
            "upgrade",
            "head",
        ],
        cwd=root,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert atual.returncode == 0, atual.stdout + atual.stderr

    with sqlite3.connect(database) as conexao:
        linha = conexao.execute(
            "SELECT quantidade_planejada, prioridade, responsavel_id "
            "FROM solicitacao_producao WHERE id = 1"
        ).fetchone()
        revisao = conexao.execute("SELECT version_num FROM alembic_version").fetchone()

    assert linha == (10, "NORMAL", None)
    assert revisao == ("e7f8a9b0c1d2",)


def test_migration_execucao_faz_backfill_do_snapshot_de_fase(tmp_path):
    root = Path(__file__).resolve().parents[1]
    database = tmp_path / "migration-execucao.db"
    env = os.environ.copy()
    env.update(
        {
            "DB_CONNECTION": "sqlite",
            "DATABASE_PATH": str(database),
            "SECRET_KEY": "migration-execucao-secret",
        }
    )

    anterior = subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "-c",
            "migrations/alembic.ini",
            "upgrade",
            "b7d9e2f4a610",
        ],
        cwd=root,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert anterior.returncode == 0, anterior.stdout + anterior.stderr

    with sqlite3.connect(database) as conexao:
        conexao.execute(
            "INSERT INTO usuario (id, nome, username, senha_hash, papel, ativo) "
            "VALUES (1, 'Gestor', 'gestor', 'hash', 'ADMIN', 1)"
        )
        conexao.execute(
            "INSERT INTO fase_producao (id, nome) VALUES (1, 'Cozir')"
        )
        conexao.execute(
            "INSERT INTO produto (id, nome, tipo, unidade_medida, conservacao, validade_obrigatoria, ativo) "
            "VALUES (1, 'Produto final', 'FINAL', 'un', 'SECO', 0, 1)"
        )
        conexao.execute(
            "INSERT INTO ficha_tecnica (id, produto_id, rendimento) VALUES (1, 1, 10)"
        )
        conexao.execute(
            "INSERT INTO solicitacao_producao "
            "(id, ficha_tecnica_id, usuario_id, quantidade_planejada, prioridade, status) "
            "VALUES (1, 1, 1, 10, 'NORMAL', 'EM_PRODUCAO')"
        )
        conexao.execute(
            "INSERT INTO sp_fase "
            "(id, solicitacao_producao_id, fase_id, ordem, tempo_previsto_min) "
            "VALUES (1, 1, 1, 1, 30)"
        )
        conexao.commit()

    atual = subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "-c",
            "migrations/alembic.ini",
            "upgrade",
            "head",
        ],
        cwd=root,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert atual.returncode == 0, atual.stdout + atual.stderr

    with sqlite3.connect(database) as conexao:
        fase = conexao.execute(
            "SELECT fase_nome_snapshot, observacao, iniciado_em, finalizado_em "
            "FROM sp_fase WHERE id = 1"
        ).fetchone()
        solicitacao = conexao.execute(
            "SELECT quantidade_produzida, observacao_execucao "
            "FROM solicitacao_producao WHERE id = 1"
        ).fetchone()
        revisao = conexao.execute("SELECT version_num FROM alembic_version").fetchone()

    assert fase == ("Cozir", None, None, None)
    assert solicitacao == (None, None)
    assert revisao == ("e7f8a9b0c1d2",)
