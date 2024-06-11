from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Header

from ..dependencies.auth import get_current_user_id, login_form_data
from ..dependencies.repo import get_auth_repo, get_users_repo
from ..dependencies.settings import get_app_settings
from ..models.auth import AuthData, LoginModel, RegisterModel, TokensModel
from ..models.user import User
from ..repo.cache import AuthRepo
from ..repo.db import UsersRepo
from ..utils.exceptions.repo import (
    InvalidPasswordError,
    PlayerAlreadyExistsError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from ..utils.settings import Settings

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@router.post("/login")
async def login(
    *,
    login_form: Annotated[LoginModel, Depends(login_form_data)],
    users_repo: Annotated[UsersRepo, Depends(get_users_repo)],
    auth_repo: Annotated[AuthRepo, Depends(get_auth_repo)],
) -> AuthData:
    try:
        user_id, user = await users_repo.try_login(login_form.username, login_form.password)
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username",
        ) from None
    except InvalidPasswordError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password",
        ) from None
    auth, refresh = await auth_repo.save_user_auth(user_id)
    return AuthData(
        user=user,
        access_token=auth,
        refresh_token=refresh,
    )


@router.post("/refresh")
async def refresh_auth(
    *,
    refresh_token: Annotated[str, Header(alias="X-Refresh-Token")],
    auth_repo: Annotated[AuthRepo, Depends(get_auth_repo)],
) -> TokensModel:
    tokens = await auth_repo.update_tokens_by_refresh(refresh_token)
    if tokens is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    return TokensModel(
        access_token=tokens[0],
        refresh_token=tokens[1],
    )


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all(
    *,
    user_id: Annotated[str, Depends(get_current_user_id)],
    auth_repo: Annotated[AuthRepo, Depends(get_auth_repo)],
) -> None:
    await auth_repo.revoke_all_tokens(user_id)


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    *,
    register_model: RegisterModel,
    users_repo: Annotated[UsersRepo, Depends(get_users_repo)],
    app_settings: Annotated[Settings, Depends(get_app_settings)],
) -> User:
    if app_settings.invite_code is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Registration is disabled",
        )
    if register_model.invite_code != app_settings.invite_code:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid invite code",
        )
    try:
        user = await users_repo.create(
            register_model.username,
            register_model.password,
            nickname=register_model.nickname,
            real_name=register_model.real_name,
        )
    except UserAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username is already taken",
        )
    except PlayerAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Nickname is already taken",
        )
    return user
