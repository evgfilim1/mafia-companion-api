import datetime

from pydantic import BaseModel


class NewTournament(BaseModel):
    name: str
    date_from: datetime.datetime
    date_to: datetime.datetime


class Tournament(NewTournament):
    id: int


class NewTable(BaseModel):
    judge_username: str


class Table(BaseModel):
    id: int
    number: int
    judge_nickname: str
