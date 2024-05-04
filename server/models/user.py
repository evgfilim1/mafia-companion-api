from pydantic import BaseModel


class User(BaseModel):
    username: str
    nickname: str
    real_name: str
