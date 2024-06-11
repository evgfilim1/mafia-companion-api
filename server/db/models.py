import datetime
from typing import Annotated

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    PrimaryKeyConstraint,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from ..utils.enums import Role, Team
from ..utils.types import JsonT

_uuid = Annotated[
    str,
    mapped_column(
        Uuid(as_uuid=False),
        server_default=text("uuid_generate_v7()"),
    ),
]
_json_dict = dict[str, JsonT]


def _fk(column: Mapped[str] | str, *, pk: bool = False) -> Mapped[str]:
    return mapped_column(ForeignKey(column, ondelete="CASCADE", onupdate="CASCADE"), primary_key=pk)


def _pk() -> Mapped[str]:
    return mapped_column(primary_key=True)


class BaseDBModel(AsyncAttrs, DeclarativeBase):
    type_annotation_map = {
        _json_dict: JSON,
        datetime.datetime: DateTime(timezone=True),
    }


class Player(BaseDBModel):
    __tablename__ = "players"

    id: Mapped[_uuid] = _pk()
    nickname: Mapped[str] = mapped_column(unique=True)
    real_name: Mapped[str]


# class UserConnection(BaseDBModel):
#     __tablename__ = "user_connections"
#
#     user_id: Mapped[_uuid] = _fk(User.id, pk=True)
#     email: Mapped[str | None]
#     telegram_id: Mapped[int | None]


class User(BaseDBModel):
    __tablename__ = "users"

    id: Mapped[_uuid] = _pk()
    username: Mapped[str] = mapped_column(unique=True)
    player_id: Mapped[_uuid] = _fk(Player.id)
    password_hash: Mapped[str]


class Tournament(BaseDBModel):
    __tablename__ = "tournaments"

    id: Mapped[_uuid] = _pk()
    name: Mapped[str]
    date_from: Mapped[datetime.datetime]
    date_to: Mapped[datetime.datetime]
    created_by_user_id: Mapped[_uuid] = _fk(User.id)


class TournamentPlayer(BaseDBModel):
    __tablename__ = "tournament_players"

    player_id: Mapped[_uuid] = _fk(Player.id)
    tournament_id: Mapped[_uuid] = _fk(Tournament.id)

    __table_args__ = (PrimaryKeyConstraint(player_id, tournament_id),)


class Table(BaseDBModel):
    __tablename__ = "tables"

    id: Mapped[_uuid] = _pk()
    tournament_id: Mapped[_uuid] = _fk(Tournament.id)
    number: Mapped[int] = mapped_column()
    judge_id: Mapped[_uuid] = _fk(Player.id)

    __table_args__ = (UniqueConstraint(tournament_id, number),)


class Game(BaseDBModel):
    __tablename__ = "games"

    id: Mapped[_uuid] = _pk()
    table_id: Mapped[_uuid] = _fk(Table.id)
    number: Mapped[int] = mapped_column()

    __table_args__ = (UniqueConstraint(table_id, number),)


class GamePlayer(BaseDBModel):
    __tablename__ = "game_players"

    game_id: Mapped[_uuid] = _fk(Game.id)
    player_id: Mapped[_uuid] = _fk(Player.id)
    role: Mapped[Role]
    seat: Mapped[int] = mapped_column()

    __table_args__ = (
        PrimaryKeyConstraint(game_id, player_id),
        CheckConstraint((1 <= seat) & (seat <= 10)),
        UniqueConstraint(game_id, seat),
    )


class GameResult(BaseDBModel):
    __tablename__ = "game_results"

    game_id: Mapped[_uuid] = _fk(Game.id, pk=True)
    winner: Mapped[Team | None]
    finished_at: Mapped[datetime.datetime]


class GameLog(BaseDBModel):
    __tablename__ = "game_logs"

    game_id: Mapped[_uuid] = _fk(Game.id, pk=True)
    raw_game_log: Mapped[_json_dict]


class GamePlayerResult(BaseDBModel):
    __tablename__ = "game_player_results"

    game_id: Mapped[_uuid] = _fk(Game.id)
    player_id: Mapped[_uuid] = _fk(Player.id)
    warn_count: Mapped[int] = mapped_column()
    was_kicked: Mapped[bool]
    caused_other_team_won: Mapped[bool]
    found_mafia_count: Mapped[int] = mapped_column()
    has_found_sheriff: Mapped[bool]
    was_killed_first_night: Mapped[bool] = mapped_column()
    guessed_mafia_count: Mapped[int] = mapped_column()

    __table_args__ = (
        PrimaryKeyConstraint(game_id, player_id),
        CheckConstraint((0 <= warn_count) & (warn_count <= 4)),
        CheckConstraint((0 <= found_mafia_count) & (found_mafia_count <= 3)),
        CheckConstraint((0 <= guessed_mafia_count) & (guessed_mafia_count <= 3)),
        CheckConstraint(
            (was_killed_first_night & (found_mafia_count >= 0)) | ~was_killed_first_night
        ),
        # other checks are kinda complex and should be done in the application
    )


class GamePlayerExtraScore(BaseDBModel):
    __tablename__ = "game_player_extra_scores"

    game_id: Mapped[_uuid] = _fk(Game.id)
    player_id: Mapped[_uuid] = _fk(Player.id)
    score: Mapped[float]
    reason: Mapped[str] = mapped_column()

    __table_args__ = (
        PrimaryKeyConstraint(game_id, player_id),
        CheckConstraint(reason.like("_%")),
    )


# TODO: add permissions
