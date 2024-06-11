from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from ..models.auth import LoginModel
from ..repo.cache import AuthRepo
from .repo import get_auth_repo

auth = OAuth2PasswordBearer(tokenUrl="auth/login")


def login_form_data(
    login_form: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> LoginModel:
    if login_form.username == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username must be non-empty",
        )
    if login_form.password == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be non-empty",
        )
    return LoginModel(
        username=login_form.username,
        password=login_form.password,
    )


async def get_current_user_id(
    *,
    token: Annotated[str, Depends(auth)],
    auth_repo: Annotated[AuthRepo, Depends(get_auth_repo)],
) -> str:
    user_id = await auth_repo.get_user_id_by_auth(token)
    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id
