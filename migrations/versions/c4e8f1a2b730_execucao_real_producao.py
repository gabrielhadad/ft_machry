"""adiciona execução real e snapshot histórico da produção

Revision ID: c4e8f1a2b730
Revises: b7d9e2f4a610
Create Date: 2026-11-01 05:30:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c4e8f1a2b730"
down_revision: Union[str, Sequence[str], None] = "b7d9e2f4a610"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_VIEW_COMPONENTE_SNAPSHOT = """
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

_VIEW_COMPONENTE_ANTIGA = """
    CREATE VIEW vw_sp_componente AS
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
"""


def upgrade() -> None:
    # A view usa sp_fase e precisa ser recriada depois do snapshot.
    op.execute("DROP VIEW IF EXISTS vw_sp_componente")

    with op.batch_alter_table("solicitacao_producao") as batch_op:
        batch_op.add_column(
            sa.Column("quantidade_produzida", sa.Numeric(18, 3), nullable=True)
        )
        batch_op.add_column(sa.Column("observacao_execucao", sa.Text(), nullable=True))
        batch_op.create_check_constraint(
            "ck_solicitacao_quantidade_produzida",
            "quantidade_produzida IS NULL OR quantidade_produzida >= 0",
        )

    # Snapshot começa nullable para permitir backfill de produções existentes.
    with op.batch_alter_table("sp_fase") as batch_op:
        batch_op.add_column(sa.Column("fase_nome_snapshot", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("observacao", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("iniciado_em", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("finalizado_em", sa.String(), nullable=True))

    op.execute(
        """
        UPDATE sp_fase
           SET fase_nome_snapshot = (
               SELECT fase_producao.nome
                 FROM fase_producao
                WHERE fase_producao.id = sp_fase.fase_id
           )
         WHERE fase_nome_snapshot IS NULL
        """
    )

    with op.batch_alter_table("sp_fase") as batch_op:
        batch_op.alter_column(
            "fase_nome_snapshot",
            existing_type=sa.Text(),
            nullable=False,
        )
        batch_op.create_check_constraint(
            "ck_sp_fase_tempo_realizado",
            "tempo_realizado_min IS NULL OR tempo_realizado_min >= 0",
        )

    op.execute(_VIEW_COMPONENTE_SNAPSHOT)


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS vw_sp_componente")

    with op.batch_alter_table("sp_fase") as batch_op:
        batch_op.drop_constraint("ck_sp_fase_tempo_realizado", type_="check")
        batch_op.drop_column("finalizado_em")
        batch_op.drop_column("iniciado_em")
        batch_op.drop_column("observacao")
        batch_op.drop_column("fase_nome_snapshot")

    with op.batch_alter_table("solicitacao_producao") as batch_op:
        batch_op.drop_constraint("ck_solicitacao_quantidade_produzida", type_="check")
        batch_op.drop_column("observacao_execucao")
        batch_op.drop_column("quantidade_produzida")

    op.execute(_VIEW_COMPONENTE_ANTIGA)
