"""create repositories table

Revision ID: 20260528_0001
Revises:
Create Date: 2026-05-28 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260528_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "repositories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("external_id", sa.String(length=140), nullable=False),
        sa.Column("owner", sa.String(length=39), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("full_name", sa.String(length=140), nullable=False),
        sa.Column("html_url", sa.String(length=300), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("stars", sa.Integer(), nullable=False),
        sa.Column("forks", sa.Integer(), nullable=False),
        sa.Column("open_issues", sa.Integer(), nullable=False),
        sa.Column("default_branch", sa.String(length=100), nullable=False),
        sa.Column("language", sa.String(length=100), nullable=True),
        sa.Column("visibility", sa.String(length=20), nullable=False),
        sa.Column("raw_metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("external_id", name="uq_repositories_external_id"),
    )
    op.create_index(op.f("ix_repositories_external_id"), "repositories", ["external_id"], unique=False)
    op.create_index(op.f("ix_repositories_id"), "repositories", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_repositories_id"), table_name="repositories")
    op.drop_index(op.f("ix_repositories_external_id"), table_name="repositories")
    op.drop_table("repositories")
