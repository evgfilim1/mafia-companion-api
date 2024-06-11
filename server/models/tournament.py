import datetime
from uuid import UUID

from pydantic import BaseModel


class NewTournament(BaseModel):
    name: str
    date_from: datetime.datetime
    date_to: datetime.datetime


class Tournament(NewTournament):
    id: UUID


class NewTable(BaseModel):
    judge_username: str


class Table(BaseModel):
    id: UUID
    number: int
    judge_nickname: str
