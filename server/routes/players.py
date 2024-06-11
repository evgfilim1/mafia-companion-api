from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from ..dependencies.auth import get_current_user_id
from ..dependencies.repo import get_players_repo, get_users_repo
from ..models.auth import LoginModel
from ..models.page import PaginatedResponse
from ..models.player import NewPlayer, Player
from ..repo.db import PlayersRepo, UsersRepo
from ..utils.exceptions.repo import PlayerAlreadyExistsError

router = APIRouter(
    prefix="/players",
    dependencies=[
        # protect all endpoints behind authorization
        Depends(get_current_user_id),
    ],
    tags=["players"],
)


@router.get("/{player_id}")
async def get_player(
    player_id: UUID,
    *,
    players_repo: Annotated[PlayersRepo, Depends(get_players_repo)],
) -> Player:
    player = await players_repo.get_by_id(str(player_id))
    if player is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found")
    return player


@router.put("/{player_id}")
async def put_player(
    player_id: UUID,
    *,
    new_player: NewPlayer,
    players_repo: Annotated[PlayersRepo, Depends(get_players_repo)],
) -> Player:
    try:
        await players_repo.edit_or_create(
            new_player.nickname,
            real_name=new_player.real_name,
            id_=str(player_id),
        )
    except PlayerAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Player with this nickname already exists",
        ) from e
    return Player.model_construct(
        id=player_id,
        nickname=new_player.nickname,
        real_name=new_player.real_name,
    )


@router.post("/{player_id}/invite", tags=["users"], status_code=status.HTTP_201_CREATED)
async def invite_as_judge(
    player_id: UUID,
    *,
    creds: LoginModel,
    players_repo: Annotated[PlayersRepo, Depends(get_players_repo)],
    users_repo: Annotated[UsersRepo, Depends(get_users_repo)],
) -> None:
    player = await players_repo.get_by_id(str(player_id))
    if player is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found")
    await users_repo.create_linked(
        username=creds.username,
        password=creds.password,
        player_id=str(player_id),
    )


# TODO: allow editing/removing only if the player is not participating in any game/tournament ^


@router.get("/")
async def get_all_players(
    *,
    players_repo: Annotated[PlayersRepo, Depends(get_players_repo)],
) -> PaginatedResponse[Player]:
    players = await players_repo.get_all()
    # TODO: implement pagination
    return PaginatedResponse(
        page=1,
        total_pages=1,
        result=players,
    )


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_player(
    new_player: NewPlayer,
    *,
    players_repo: Annotated[PlayersRepo, Depends(get_players_repo)],
) -> Player:
    try:
        player = await players_repo.edit_or_create(
            new_player.nickname,
            real_name=new_player.real_name,
            id_=None,
        )
    except PlayerAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Player with this nickname already exists",
        )
    return player
