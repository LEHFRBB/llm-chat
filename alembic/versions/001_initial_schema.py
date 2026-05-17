"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-04-25 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("login", sa.String(255), nullable=False),
        sa.Column("password", sa.String(255), nullable=True),
        sa.Column("github_id", sa.String(100), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("login"),
        sa.UniqueConstraint("github_id"),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_login", "users", ["login"])

    op.create_table(
        "chats",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_chats_id", "chats", ["id"])

    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("chat_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["chat_id"], ["chats.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_messages_id", "messages", ["id"])


def downgrade() -> None:
    op.drop_index("ix_messages_id", table_name="messages")
    op.drop_table("messages")
    op.drop_index("ix_chats_id", table_name="chats")
    op.drop_table("chats")
    op.drop_index("ix_users_login", table_name="users")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_table("users")
