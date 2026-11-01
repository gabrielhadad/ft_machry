"""adiciona planejamento de produção

Revision ID: b7d9e2f4a610
Revises: 8a3c1d4e5f67
Create Date: 2026-11-01 04:45:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7d9e2f4a610"
down_revision: Union[str, Sequence[str], None] = "8a3c1d4e5f67"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Primeiro adicionamos a quantidade como nullable para conseguir preencher
    # solicitações já existentes a partir do rendimento de sua ficha técnica.
    with op.batch_alter_table("solicitacao_producao") as batch_op:
        batch_op.add_column(sa.Column("responsavel_id", sa.Integer(), nullable=True))
        batch_op.add_column(
            sa.Column("quantidade_planejada", sa.Numeric(18, 3), nullable=True)
        )
        batch_op.add_column(
            sa.Column(
                "prioridade",
                sa.Text(),
                server_default="NORMAL",
                nullable=False,
            )
        )
        batch_op.add_column(sa.Column("previsto_para", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("observacao", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("iniciado_em", sa.String(), nullable=True))
        batch_op.create_foreign_key(
            "fk_solicitacao_responsavel",
            "usuario",
            ["responsavel_id"],
            ["id"],
        )

    op.execute(
        """
        UPDATE solicitacao_producao
           SET quantidade_planejada = (
               SELECT ficha_tecnica.rendimento
                 FROM ficha_tecnica
                WHERE ficha_tecnica.id = solicitacao_producao.ficha_tecnica_id
           )
         WHERE quantidade_planejada IS NULL
        """
    )

    with op.batch_alter_table("solicitacao_producao") as batch_op:
        batch_op.alter_column(
            "quantidade_planejada",
            existing_type=sa.Numeric(18, 3),
            nullable=False,
        )
        batch_op.create_check_constraint(
            "ck_solicitacao_quantidade_planejada",
            "quantidade_planejada > 0",
        )
        batch_op.create_check_constraint(
            "ck_solicitacao_prioridade",
            "prioridade IN ('BAIXA', 'NORMAL', 'ALTA', 'URGENTE')",
        )
        batch_op.create_index(
            "idx_solicitacao_planejamento",
            ["status", "previsto_para", "prioridade"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("solicitacao_producao") as batch_op:
        batch_op.drop_index("idx_solicitacao_planejamento")
        batch_op.drop_constraint("ck_solicitacao_prioridade", type_="check")
        batch_op.drop_constraint("ck_solicitacao_quantidade_planejada", type_="check")
        batch_op.drop_constraint("fk_solicitacao_responsavel", type_="foreignkey")
        batch_op.drop_column("iniciado_em")
        batch_op.drop_column("observacao")
        batch_op.drop_column("previsto_para")
        batch_op.drop_column("prioridade")
        batch_op.drop_column("quantidade_planejada")
        batch_op.drop_column("responsavel_id")
