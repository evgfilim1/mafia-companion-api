from typing import Literal

from pydantic import BaseModel

from .user import User


class LoginModel(BaseModel):
    username: str
    password: str


class RegisterModel(BaseModel):
    username: str
    nickname: str
    real_name: str
    password: str
    invite_code: str


class TokensModel(BaseModel):
    access_token: str
    refresh_token: str


class AuthData(TokensModel):
    user: User
    token_type: Literal["Bearer"] = "Bearer"
