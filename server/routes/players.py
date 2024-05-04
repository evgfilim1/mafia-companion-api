from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from ..dependencies.auth import get_current_user_id
from ..dependencies.repo import get_players_repo
from ..models.page import PaginatedResponse
from ..models.player import NewPlayer, Player
from ..repo.db import PlayersRepo
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
    player_id: int,
    *,
    players_repo: Annotated[PlayersRepo, Depends(get_players_repo)],
) -> Player:
    player = await players_repo.get_by_id(player_id)
    if player is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found")
    return player


@router.put("/{player_id}")
async def update_player(
    player_id: int,
    *,
    players_repo: Annotated[PlayersRepo, Depends(get_players_repo)],
    new_player: NewPlayer,
) -> Player:
    existing_player = await players_repo.get_by_id(player_id)
    player_exists_error = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Player with this nickname already exists",
    )
    if existing_player is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found")
    if existing_player.nickname != new_player.nickname:
        try:
            await players_repo.edit_nickname(player_id, new_player.nickname)
        except PlayerAlreadyExistsError:
            raise player_exists_error
    if existing_player.real_name != new_player.real_name:
        await players_repo.edit_real_name(player_id, new_player.real_name)
    return Player.model_construct(
        id=player_id,
        nickname=new_player.nickname,
        real_name=new_player.real_name,
    )


@router.delete("/{player_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_player(
    player_id: int,
    *,
    players_repo: Annotated[PlayersRepo, Depends(get_players_repo)],
) -> None:
    await players_repo.delete(player_id)


# TODO: disallow editing/removing if the player is participating in any game/tournament ^


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


@router.post("/")
async def create_player(
    new_player: NewPlayer,
    *,
    players_repo: Annotated[PlayersRepo, Depends(get_players_repo)],
) -> Player:
    try:
        player = await players_repo.create(new_player.nickname, real_name=new_player.real_name)
    except PlayerAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Player with this nickname already exists",
        )
    return player
