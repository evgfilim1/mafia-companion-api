"""Fix constraints

Revision ID: 51dfe1d15cfd
Revises: 7f8b5994a887
Create Date: 2024-06-11 11:44:03.787791+00:00

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "51dfe1d15cfd"
down_revision: Union[str, None] = "7f8b5994a887"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_primary_key(None, "game_logs", ["game_id"])
    op.create_primary_key(None, "game_player_extra_scores", ["game_id", "player_id"])
    op.create_primary_key(None, "game_player_results", ["game_id", "player_id"])
    op.create_primary_key(None, "game_players", ["game_id", "player_id"])
    op.create_unique_constraint(None, "game_players", ["game_id", "seat"])
    op.create_primary_key(None, "game_results", ["game_id"])
    op.create_unique_constraint(None, "games", ["table_id", "number"])
    op.create_primary_key(None, "tournament_players", ["player_id", "tournament_id"])
    op.create_unique_constraint(None, "tables", ["tournament_id", "number"])


def downgrade() -> None:
    op.drop_constraint("tables_tournament_id_number_key", "tables", type_="unique")
    op.drop_constraint("tournament_players_pkey", "tournament_players", type_="primary")
    op.drop_constraint("games_table_id_number_key", "games", type_="unique")
    op.drop_constraint("game_results_pkey", "game_results", type_="primary")
    op.drop_constraint("game_players_game_id_seat_key", "game_players", type_="unique")
    op.drop_constraint("game_players_pkey", "game_players", type_="primary")
    op.drop_constraint("game_player_results_pkey", "game_player_results", type_="primary")
    op.drop_constraint("game_player_extra_scores_pkey", "game_player_extra_scores", type_="primary")
    op.drop_constraint("game_logs_pkey", "game_logs", type_="primary")
