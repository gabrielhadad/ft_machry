"""Testes focados na modelagem de praças (Fase 1)."""

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

from app.features.pracas.models import Praca
from app.features.producao.models import SolicitacaoProducao
from app.features.usuarios.models import Usuario
from db.database_config import db


def test_estrutura_criada_com_chaves_e_indices(app, client):
    with app.app_context():
        inspetor = inspect(db.engine)
        assert {"praca", "praca_usuario"}.issubset(inspetor.get_table_names())
        assert "praca_id" in {
            coluna["name"] for coluna in inspetor.get_columns("solicitacao_producao")
        }
        vinculos = {
            (fk["constrained_columns"][0], fk["referred_table"])
            for fk in inspetor.get_foreign_keys("praca_usuario")
        }
        assert vinculos == {("praca_id", "praca"), ("usuario_id", "usuario")}
        assert any(
            fk["constrained_columns"] == ["praca_id"]
            and fk["referred_table"] == "praca"
            for fk in inspetor.get_foreign_keys("solicitacao_producao")
        )
        assert any(
            idx["name"] == "ix_solicitacao_producao_praca_id"
            for idx in inspetor.get_indexes("solicitacao_producao")
        )


def test_praca_associa_multiplos_cozinheiros_e_producao(app, seeded_client):
    with app.app_context():
        usuarios = list(db.session.execute(db.select(Usuario)).scalars())
        cozinheiro = next(
            usuario for usuario in usuarios
            if any(grupo.nome == "Cozinha" for grupo in usuario.grupos)
        )
        auxiliar = Usuario(
            nome="Auxiliar", username="auxiliar", senha_hash="hash-teste",
            grupos=list(cozinheiro.grupos),
        )
        # Persistir antes de consultas que disparam o autoflush do SQLAlchemy.
        db.session.add(auxiliar)
        ficha_id = db.session.execute(text("SELECT id FROM ficha_tecnica LIMIT 1")).scalar_one()
        praca = Praca(nome="Grelha", descricao="Estação de grelhados")
        praca.cozinheiros = [cozinheiro, auxiliar]
        outra_praca = Praca(nome="Finalização", cozinheiros=[cozinheiro])
        solicitacao = SolicitacaoProducao(ficha_tecnica_id=ficha_id, usuario_id=cozinheiro.id)
        praca.solicitacoes.append(solicitacao)
        db.session.add_all([praca, outra_praca])
        db.session.commit()
        assert praca.ativo == 1
        assert praca.criado_em is not None
        assert {usuario.id for usuario in praca.cozinheiros} == {cozinheiro.id, auxiliar.id}
        assert {p.id for p in cozinheiro.pracas} == {praca.id, outra_praca.id}
        assert solicitacao.praca_id == praca.id
        assert solicitacao.praca is praca


def test_praca_impede_nome_repetido_e_ativo_invalido(app, client):
    with app.app_context():
        db.session.add(Praca(nome="Massas"))
        db.session.commit()
        with pytest.raises(IntegrityError):
            db.session.add(Praca(nome="Massas"))
            db.session.commit()
        db.session.rollback()

        with pytest.raises(IntegrityError):
            db.session.add(Praca(nome="Doces", ativo=2))
            db.session.commit()
        db.session.rollback()


def test_associacao_nao_aceita_usuario_inexistente(app, client):
    with app.app_context():
        praca = Praca(nome="Saladas")
        db.session.add(praca)
        db.session.commit()
        with pytest.raises(IntegrityError):
            db.session.execute(
                text("INSERT INTO praca_usuario (praca_id, usuario_id) VALUES (:p, 99999)"),
                {"p": praca.id},
            )
            db.session.commit()
        db.session.rollback()


def test_migracao_preserva_solicitacao_existente(app, seeded_client):
    """Migra tabela legada no banco temporário, preservando a solicitação."""
    with app.app_context():
        usuario_id = db.session.execute(text("SELECT id FROM usuario LIMIT 1")).scalar_one()
        ficha_id = db.session.execute(text("SELECT id FROM ficha_tecnica LIMIT 1")).scalar_one()

        # O SQLite não permite remover uma coluna referenciada por uma FK.
        # Reconstruímos a tabela vazia com seu esquema anterior à Fase 1,
        # somente no banco isolado criado pelo fixture de teste.
        db.session.execute(text("DROP TABLE solicitacao_producao"))
        db.session.execute(text("""
            CREATE TABLE solicitacao_producao (
                id INTEGER PRIMARY KEY,
                ficha_tecnica_id INTEGER NOT NULL REFERENCES ficha_tecnica(id),
                usuario_id INTEGER NOT NULL REFERENCES usuario(id),
                quantidade_planejada NUMERIC NOT NULL DEFAULT 1,
                localizacao_destino_id INTEGER REFERENCES localizacao(id),
                status TEXT NOT NULL DEFAULT 'ABERTA',
                criado_em VARCHAR NOT NULL DEFAULT (CAST(CURRENT_TIMESTAMP AS TEXT)),
                concluido_em VARCHAR,
                CONSTRAINT ck_solicitacao_status CHECK (
                    status IN ('ABERTA', 'EM_SEPARACAO', 'EM_PRODUCAO', 'CONCLUIDA', 'CANCELADA')
                )
            )
        """))
        db.session.execute(
            text("INSERT INTO solicitacao_producao (ficha_tecnica_id, usuario_id) "
                 "VALUES (:f, :u)"),
            {"f": ficha_id, "u": usuario_id},
        )
        db.session.commit()
        sp_id = db.session.execute(text("SELECT MAX(id) FROM solicitacao_producao")).scalar_one()
        # Inspeciona pela conexão já aberta para não competir por bloqueios no SQLite.
        assert "praca_id" not in {
            coluna["name"] for coluna in inspect(db.session.connection()).get_columns("solicitacao_producao")
        }
        db.session.remove()

        resultado = app.test_cli_runner().invoke(args=["init-db"])
        assert resultado.exit_code == 0, resultado.output
        registro = db.session.execute(
            text("SELECT id, praca_id FROM solicitacao_producao WHERE id = :id"),
            {"id": sp_id},
        ).one()
        assert registro == (sp_id, None)
        indice = [
            i["name"]
            for i in inspect(db.session.connection()).get_indexes("solicitacao_producao")
        ]
        assert "ix_solicitacao_producao_praca_id" in indice
        db.session.remove()

        # Rodar novamente não deve falhar nem duplicar informações.
        resultado = app.test_cli_runner().invoke(args=["init-db"])
        assert resultado.exit_code == 0, resultado.output
        assert db.session.execute(text("SELECT COUNT(*) FROM solicitacao_producao")).scalar_one() == 1
