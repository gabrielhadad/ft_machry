"""adiciona perdas auditáveis ao estoque e produção final integrada

Revision ID: d6a1b2c3d4e5
Revises: c4e8f1a2b730
Create Date: 2026-11-01 06:10:00

"""
from typing import Sequence, Union

from alembic import op


revision: str = "d6a1b2c3d4e5"
down_revision: Union[str, Sequence[str], None] = "c4e8f1a2b730"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_VIEW_COMPONENTE_COM_PERDAS = """
    CREATE VIEW vw_sp_componente AS
    SELECT c.id AS sp_componente_id, c.solicitacao_producao_id,
           c.produto_id, p.nome AS componente, p.unidade_medida,
           sf.ordem AS fase_ordem, sf.fase_nome_snapshot AS fase,
           c.quantidade_prevista,
           COALESCE(SUM(CASE WHEN m.tipo IN ('CONSUMO_PRODUCAO', 'PERDA')
                             THEN m.quantidade ELSE 0 END), 0) AS quantidade_realizada,
           SUM(CASE WHEN m.tipo IN ('CONSUMO_PRODUCAO', 'PERDA')
                    THEN m.quantidade * l.custo_unitario ELSE 0 END) AS custo_realizado
      FROM sp_componente c
      JOIN produto p ON p.id = c.produto_id
      LEFT JOIN sp_fase sf ON sf.id = c.sp_fase_id
      LEFT JOIN movimentacao_estoque m
             ON m.sp_componente_id = c.id
            AND m.tipo IN ('CONSUMO_PRODUCAO', 'PERDA')
      LEFT JOIN lote l ON l.id = m.lote_id
     GROUP BY c.id, c.solicitacao_producao_id, c.produto_id, p.nome,
              p.unidade_medida, sf.ordem, sf.fase_nome_snapshot,
              c.quantidade_prevista
"""

_VIEW_COMPONENTE_SEM_PERDAS = """
    CREATE VIEW vw_sp_componente AS
    SELECT c.id AS sp_componente_id, c.solicitacao_producao_id,
           c.produto_id, p.nome AS componente, p.unidade_medida,
           sf.ordem AS fase_ordem, sf.fase_nome_snapshot AS fase,
           c.quantidade_prevista,
           COALESCE(SUM(m.quantidade), 0) AS quantidade_realizada,
           SUM(m.quantidade * l.custo_unitario) AS custo_realizado
      FROM sp_componente c
      JOIN produto p ON p.id = c.produto_id
      LEFT JOIN sp_fase sf ON sf.id = c.sp_fase_id
      LEFT JOIN movimentacao_estoque m
             ON m.sp_componente_id = c.id AND m.tipo = 'CONSUMO_PRODUCAO'
      LEFT JOIN lote l ON l.id = m.lote_id
     GROUP BY c.id, c.solicitacao_producao_id, c.produto_id, p.nome,
              p.unidade_medida, sf.ordem, sf.fase_nome_snapshot,
              c.quantidade_prevista
"""


def upgrade() -> None:
    # SQLite recria a tabela no batch mode; views dependentes precisam sair antes.
    op.execute("DROP VIEW IF EXISTS vw_sp_componente")
    op.execute("DROP VIEW IF EXISTS vw_sp_producao")

    with op.batch_alter_table("movimentacao_estoque") as batch_op:
        batch_op.drop_constraint("ck_movimentacao_tipo", type_="check")
        batch_op.create_check_constraint(
            "ck_movimentacao_tipo",
            "tipo IN ('ENTRADA', 'PRODUCAO', 'SAIDA', 'CONSUMO_PRODUCAO', "
            "'TRANSFERENCIA', 'TRANSFORMACAO', 'AJUSTE_ENTRADA', 'AJUSTE_SAIDA', 'PERDA')",
        )

    op.execute(_VIEW_COMPONENTE_COM_PERDAS)
    op.execute(
        "CREATE VIEW vw_sp_producao AS "
        "SELECT m.solicitacao_producao_id, m.lote_id, m.quantidade, m.criado_em "
        "FROM movimentacao_estoque m WHERE m.tipo = 'PRODUCAO'"
    )


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS vw_sp_componente")
    op.execute("DROP VIEW IF EXISTS vw_sp_producao")

    # A revisão antiga não conhece PERDA; downgrade só é seguro sem esses registros.
    op.execute("DELETE FROM movimentacao_estoque WHERE tipo = 'PERDA'")

    with op.batch_alter_table("movimentacao_estoque") as batch_op:
        batch_op.drop_constraint("ck_movimentacao_tipo", type_="check")
        batch_op.create_check_constraint(
            "ck_movimentacao_tipo",
            "tipo IN ('ENTRADA', 'PRODUCAO', 'SAIDA', 'CONSUMO_PRODUCAO', "
            "'TRANSFERENCIA', 'TRANSFORMACAO', 'AJUSTE_ENTRADA', 'AJUSTE_SAIDA')",
        )

    op.execute(_VIEW_COMPONENTE_SEM_PERDAS)
    op.execute(
        "CREATE VIEW vw_sp_producao AS "
        "SELECT m.solicitacao_producao_id, m.lote_id, m.quantidade, m.criado_em "
        "FROM movimentacao_estoque m WHERE m.tipo = 'PRODUCAO'"
    )
