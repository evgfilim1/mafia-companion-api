"""Convert int identity columns to UUIDv7

Revision ID: 7f8b5994a887
Revises: d31a63a82b44
Create Date: 2024-06-03 20:04:39.608695+00:00

"""

from typing import Sequence, Union, Any

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7f8b5994a887"
down_revision: Union[str, None] = "d31a63a82b44"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def drop_pk_cascade(
    target_table: str,
    target_col_name: str,
    tables: list[str | tuple[str, str]],
    default_col_name: str,
) -> None:
    for table_name in tables:
        if isinstance(table_name, tuple):
            table_name, col_name = table_name
        else:
            col_name = default_col_name
        op.drop_constraint(f"{table_name}_{col_name}_id_fkey", table_name, type_="foreignkey")
    op.drop_constraint(
        f"{target_table}_pkey",
        target_table,
        type_="primary",
    )
    op.create_primary_key(
        f"{target_table}_pkey",
        target_table,
        [target_col_name],
    )


def alter_fk_cascade(
    target_table: str,
    target_col_name: str,
    to_type: Any,
    tables: list[str | tuple[str, str]],
    default_col_name: str,
) -> None:
    for table_name in tables:
        if isinstance(table_name, tuple):
            table_name, col_name = table_name
        else:
            col_name = default_col_name
        target_ref_col_name = f"migrate_{col_name}_id_{revision}"
        op.add_column(
            table_name,
            sa.Column(target_ref_col_name, to_type, nullable=True),
        )
        op.execute(
            f'UPDATE "{table_name}" dst SET "{target_ref_col_name}" ='
            f' (SELECT "{target_col_name}" FROM "{target_table}" WHERE id = dst."{col_name}_id")'
        )
        op.drop_column(table_name, f"{col_name}_id")
        op.alter_column(
            table_name,
            target_ref_col_name,
            new_column_name=f"{col_name}_id",
            existing_type=to_type,
            nullable=False,
        )
        op.create_foreign_key(
            f"{table_name}_{col_name}_id_fkey",
            table_name,
            target_table,
            [f"{col_name}_id"],
            [target_col_name],
            onupdate="CASCADE",
            ondelete="CASCADE",
        )
    op.drop_column(target_table, "id")
    op.alter_column(
        target_table,
        target_col_name,
        new_column_name="id",
        existing_type=to_type,
        nullable=False,
    )


def upgrade_impl(
    target_table: str,
    dependent_tables: list[str | tuple[str, str]],
    default_col_name: str,
) -> None:
    target_col_name = f"migrate_id_{revision}"
    op.add_column(
        target_table,
        sa.Column(
            target_col_name,
            sa.Uuid(as_uuid=False),
            nullable=False,
            server_default=sa.text("uuid_generate_v7()"),
        ),
    )
    drop_pk_cascade(
        target_table,
        target_col_name,
        dependent_tables,
        default_col_name,
    )
    alter_fk_cascade(
        target_table,
        target_col_name,
        sa.Uuid(as_uuid=False),
        dependent_tables,
        default_col_name,
    )


def downgrade_impl(
    target_table: str,
    dependent_tables: list[str | tuple[str, str]],
    default_col_name: str,
) -> None:
    target_col_name = f"migrate_id_{revision}"
    op.add_column(
        target_table,
        sa.Column(
            target_col_name,
            sa.Integer(),
            nullable=False,
            server_default=sa.Identity(always=False),
        ),
    )
    drop_pk_cascade(
        target_table,
        target_col_name,
        dependent_tables,
        default_col_name,
    )
    alter_fk_cascade(
        target_table,
        target_col_name,
        sa.INTEGER(),
        dependent_tables,
        default_col_name,
    )


DATA = [
    (
        "players",
        [
            "game_player_extra_scores",
            "game_player_results",
            "game_players",
            ("tables", "judge"),
            "tournament_players",
            "users",
        ],
        "player",
    ),
    (
        "games",
        [
            "game_logs",
            "game_player_extra_scores",
            "game_player_results",
            "game_players",
            "game_results",
        ],
        "game",
    ),
    ("tournaments", ["tournament_players", "tables"], "tournament"),
    ("tables", ["games"], "table"),
    ("users", [("tournaments", "created_by_user")], "user"),
]


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_uuidv7")
    for target_table, dependent_tables, default_col_name in DATA:
        upgrade_impl(target_table, dependent_tables, default_col_name)


def downgrade() -> None:
    for target_table, dependent_tables, default_col_name in DATA:
        downgrade_impl(target_table, dependent_tables, default_col_name)
