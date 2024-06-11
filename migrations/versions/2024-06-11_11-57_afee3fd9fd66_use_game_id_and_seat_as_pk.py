"""Use game_id and seat as a primary key for game_players

Revision ID: afee3fd9fd66
Revises: 51dfe1d15cfd
Create Date: 2024-06-11 11:57:20.432761+00:00

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "afee3fd9fd66"
down_revision: Union[str, None] = "51dfe1d15cfd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("game_players_pkey", "game_players", type_="primary")
    op.drop_constraint("game_players_game_id_seat_key", "game_players", type_="unique")
    op.create_primary_key(None, "game_players", ["game_id", "seat"])

    op.add_column("game_player_extra_scores", sa.Column("seat", sa.Integer(), nullable=True))
    op.execute(
        "UPDATE game_player_extra_scores"
        " SET seat = (SELECT seat FROM game_players"
        " WHERE game_players.player_id = game_player_extra_scores.player_id"
        " AND game_players.game_id = game_player_extra_scores.game_id)"
    )
    op.alter_column("game_player_extra_scores", "seat", existing_type=sa.Integer(), nullable=False)

    op.drop_constraint(
        "game_player_extra_scores_player_id_fkey", "game_player_extra_scores", type_="foreignkey"
    )
    op.drop_constraint("game_player_extra_scores_pkey", "game_player_extra_scores", type_="primary")
    op.drop_column("game_player_extra_scores", "player_id")

    op.drop_constraint(
        "game_player_extra_scores_game_id_fkey", "game_player_extra_scores", type_="foreignkey"
    )
    op.create_foreign_key(
        None, "game_player_extra_scores", "game_players", ["game_id", "seat"], ["game_id", "seat"]
    )

    op.create_primary_key(None, "game_player_extra_scores", ["game_id", "seat"])

    op.add_column("game_player_results", sa.Column("seat", sa.Integer(), nullable=True))
    op.execute(
        "UPDATE game_player_results"
        " SET seat = (SELECT seat FROM game_players"
        " WHERE game_players.player_id = game_player_results.player_id"
        " AND game_players.game_id = game_player_results.game_id)"
    )
    op.alter_column("game_player_results", "seat", existing_type=sa.Integer(), nullable=False)

    op.drop_constraint(
        "game_player_results_player_id_fkey", "game_player_results", type_="foreignkey"
    )
    op.drop_constraint("game_player_results_pkey", "game_player_results", type_="primary")
    op.drop_column("game_player_results", "player_id")

    op.drop_constraint(
        "game_player_results_game_id_fkey", "game_player_results", type_="foreignkey"
    )

    op.create_foreign_key(
        None, "game_player_results", "game_players", ["game_id", "seat"], ["game_id", "seat"]
    )
    op.create_primary_key(None, "game_player_results", ["game_id", "seat"])


def downgrade() -> None:
    op.drop_constraint("game_player_results_pkey", "game_player_results", type_="primary")
    op.drop_constraint(
        "game_player_results_game_id_seat_fkey", "game_player_results", type_="foreignkey"
    )

    op.create_foreign_key(None, "game_player_results", "games", ["game_id"], ["id"])

    op.add_column(
        "game_player_results",
        sa.Column("player_id", sa.Uuid(as_uuid=False), nullable=True),
    )
    op.execute(
        "UPDATE game_player_results"
        " SET player_id = (SELECT player_id FROM game_players"
        " WHERE game_players.game_id = game_player_results.game_id"
        " AND game_players.seat = game_player_results.seat)"
    )
    op.alter_column(
        "game_player_results", "player_id", existing_type=sa.Uuid(as_uuid=False), nullable=False
    )
    op.create_foreign_key(None, "game_player_results", "players", ["player_id"], ["id"])
    op.create_primary_key(
        "game_player_results_pkey", "game_player_results", ["game_id", "player_id"]
    )

    op.drop_column("game_player_results", "seat")

    op.drop_constraint("game_player_extra_scores_pkey", "game_player_extra_scores", type_="primary")
    op.drop_constraint(
        "game_player_extra_scores_game_id_seat_fkey", "game_player_extra_scores", type_="foreignkey"
    )
    op.create_foreign_key(None, "game_player_extra_scores", "games", ["game_id"], ["id"])

    op.add_column(
        "game_player_extra_scores",
        sa.Column("player_id", sa.Uuid(as_uuid=False), nullable=True),
    )
    op.execute(
        "UPDATE game_player_extra_scores"
        " SET player_id = (SELECT player_id FROM game_players"
        " WHERE game_players.game_id = game_player_extra_scores.game_id"
        " AND game_players.seat = game_player_extra_scores.seat)"
    )
    op.alter_column(
        "game_player_extra_scores",
        "player_id",
        existing_type=sa.Uuid(as_uuid=False),
        nullable=False,
    )
    op.create_foreign_key(None, "game_player_extra_scores", "players", ["player_id"], ["id"])

    op.create_primary_key(None, "game_player_extra_scores", ["game_id", "player_id"])

    op.drop_column("game_player_extra_scores", "seat")

    op.drop_constraint("game_players_pkey", "game_players", type_="primary")
    op.create_unique_constraint(None, "game_players", ["game_id", "seat"])
    op.create_primary_key(None, "game_players", ["game_id", "player_id"])
