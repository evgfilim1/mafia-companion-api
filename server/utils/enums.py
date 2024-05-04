from enum import Enum


class Team(Enum):
    MAFIA = "mafia"
    CITIZEN = "citizen"


class Role(Enum):
    MAFIA = "mafia"
    DON = "don"
    SHERIFF = "sheriff"
    CITIZEN = "citizen"

    @property
    def team(self) -> Team:
        match self:
            case Role.MAFIA | Role.DON:
                return Team.MAFIA
            case Role.SHERIFF | Role.CITIZEN:
                return Team.CITIZEN
            case _:
                raise ValueError(f"Unexpected role: {self}")
