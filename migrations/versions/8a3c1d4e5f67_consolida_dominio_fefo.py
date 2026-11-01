"""consolida domínio e corrige nomenclatura FEFO

Revision ID: 8a3c1d4e5f67
Revises: fee791234a46
Create Date: 2026-11-01 04:15:00

"""
from typing import Sequence, Union

from alembic import op

revision: str = "8a3c1d4e5f67"
down_revision: Union[str, Sequence[str], None] = "fee791234a46"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_FEFO_VIEW = """
    CREATE VIEW vw_fefo AS
    SELECT l.* FROM lote l WHERE l.quantidade > 0
     ORDER BY l.produto_id,
              CASE WHEN l.data_validade IS NULL THEN 1 ELSE 0 END,
              l.data_validade ASC,
              l.criado_em ASC,
              l.id ASC
"""

_FIFO_VIEW = """
    CREATE VIEW vw_fifo AS
    SELECT l.* FROM lote l WHERE l.quantidade > 0
     ORDER BY l.produto_id, l.data_validade ASC, l.criado_em ASC
"""


def upgrade() -> None:
    # O domínio sempre selecionou por validade; o nome FIFO era legado.
    op.execute("DROP VIEW IF EXISTS vw_fifo")
    op.execute("DROP VIEW IF EXISTS vw_fefo")

    with op.batch_alter_table("lote") as batch_op:
        batch_op.drop_index("idx_lote_fifo")
        batch_op.create_index(
            "idx_lote_fefo",
            ["produto_id", "data_validade", "localizacao_id"],
            unique=False,
        )

    op.execute(_FEFO_VIEW)


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS vw_fefo")
    op.execute("DROP VIEW IF EXISTS vw_fifo")

    with op.batch_alter_table("lote") as batch_op:
        batch_op.drop_index("idx_lote_fefo")
        batch_op.create_index(
            "idx_lote_fifo",
            ["produto_id", "data_validade", "localizacao_id"],
            unique=False,
        )

    op.execute(_FIFO_VIEW)
