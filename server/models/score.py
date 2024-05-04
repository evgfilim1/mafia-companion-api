from typing import Annotated

from pydantic import BaseModel, Field, computed_field

from ..utils.enums import Role

type CountByRole = dict[Role, int]
_BY_ROLE_TEMPLATE: CountByRole = {r: 0 for r in Role}


class ScoreRow(BaseModel):
    nickname: str
    judge_extra_points: float = 0
    judge_penalty_points: float = 0
    best_turn_points: float = 0
    ci_points: float = 0
    wins_by_role: Annotated[CountByRole, Field(default_factory=_BY_ROLE_TEMPLATE.copy)]
    first_night_killed_times: int = 0
    games_by_role: Annotated[CountByRole, Field(default_factory=_BY_ROLE_TEMPLATE.copy)]
    warns: int = 0
    times_kicked: int = 0
    times_caused_other_team_won: int = 0
    found_mafia_count: int = 0
    times_found_sheriff: int = 0
    times_killed_first_night: int = 0
    guessed_mafia_count: int = 0

    @computed_field
    @property
    def win_count(self) -> int:
        return sum(self.wins_by_role.values())

    @computed_field
    @property
    def play_count(self) -> int:
        return sum(self.games_by_role.values())

    @computed_field
    @property
    def total_extra_points(self) -> float:
        return self.judge_extra_points + self.best_turn_points

    @computed_field
    @property
    def total_penalty_points(self) -> float:
        return (
            self.judge_penalty_points + self.times_kicked * 0.5 + self.times_caused_other_team_won
        )

    @computed_field
    @property
    def sum(self) -> float:
        return self.win_count + self.total_extra_points - self.total_penalty_points + self.ci_points

    @computed_field
    @property
    def win_rate(self) -> float | None:
        return (self.win_count / self.play_count) if self.play_count > 0 else None
