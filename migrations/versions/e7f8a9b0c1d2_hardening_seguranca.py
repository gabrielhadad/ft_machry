"""hardening seguranca

Revision ID: e7f8a9b0c1d2
Revises: d6a1b2c3d4e5
Create Date: 2026-11-01
"""
from alembic import op
import sqlalchemy as sa

revision = "e7f8a9b0c1d2"
down_revision = "d6a1b2c3d4e5"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("usuario") as batch:
        batch.add_column(sa.Column("deve_trocar_senha", sa.Integer(), nullable=False, server_default="0"))
        batch.add_column(sa.Column("login_falhas", sa.Integer(), nullable=False, server_default="0"))
        batch.add_column(sa.Column("bloqueado_ate", sa.Text(), nullable=True))
        batch.add_column(sa.Column("ultimo_login_em", sa.Text(), nullable=True))
        batch.add_column(sa.Column("senha_alterada_em", sa.Text(), nullable=True))

    op.create_table(
        "auditoria",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("evento", sa.String(length=80), nullable=False),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuario.id"), nullable=True),
        sa.Column("username", sa.String(length=80), nullable=True),
        sa.Column("ip", sa.String(length=64), nullable=True),
        sa.Column("metodo", sa.String(length=12), nullable=True),
        sa.Column("caminho", sa.String(length=255), nullable=True),
        sa.Column("detalhes", sa.Text(), nullable=True),
        sa.Column("criado_em", sa.Text(), nullable=False, server_default=sa.text("(CAST(CURRENT_TIMESTAMP AS TEXT))")),
    )
    op.create_index("ix_auditoria_evento", "auditoria", ["evento"])
    op.create_index("ix_auditoria_criado_em", "auditoria", ["criado_em"])


def downgrade():
    op.drop_index("ix_auditoria_criado_em", table_name="auditoria")
    op.drop_index("ix_auditoria_evento", table_name="auditoria")
    op.drop_table("auditoria")
    with op.batch_alter_table("usuario") as batch:
        batch.drop_column("senha_alterada_em")
        batch.drop_column("ultimo_login_em")
        batch.drop_column("bloqueado_ate")
        batch.drop_column("login_falhas")
        batch.drop_column("deve_trocar_senha")
