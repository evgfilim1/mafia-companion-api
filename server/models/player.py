from pydantic import BaseModel


class NewPlayer(BaseModel):
    nickname: str
    real_name: str


class Player(NewPlayer):
    id: int
