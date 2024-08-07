import datetime
from typing import Annotated, Any
from uuid import UUID

from pydantic import BaseModel, Field

from ..utils.enums import Role, Team


class GamePlayer(BaseModel):
    nickname: str | None
    role: Role


class NewGame(BaseModel):
    players: Annotated[list[GamePlayer], Field(min_items=10, max_items=10)]


class Game(NewGame):
    id: UUID
    number: int
    table_id: UUID


class PlayerExtraScore(BaseModel):
    points: float
    reason: str


class PlayerResult(BaseModel):
    warn_count: int
    was_kicked: bool
    caused_other_team_won: bool
    found_mafia_count: int
    has_found_sheriff: bool
    was_killed_first_night: bool
    guessed_mafia_count: int
    extra_scores: list[PlayerExtraScore]


class BaseGameResult(BaseModel):
    winner: Team | None
    results: Annotated[list[PlayerResult], Field(min_items=10, max_items=10)]


class NewGameResult(BaseGameResult):
    raw_game_log: dict[str, Any] | None = None
    finished_at: datetime.datetime | None = None


class GameResult(BaseGameResult):
    finished_at: datetime.datetime
