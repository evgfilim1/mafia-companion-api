from typing import Annotated

from fastapi import APIRouter, Depends

from server.dependencies.auth import get_current_user_id
from server.dependencies.repo import get_users_repo
from server.models.user import User
from server.repo.db import UsersRepo

router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@router.get("/me")
async def get_me(
    *,
    user_id: Annotated[str, Depends(get_current_user_id)],
    users_repo: Annotated[UsersRepo, Depends(get_users_repo)],
) -> User:
    return await users_repo.get_by_id(user_id)
