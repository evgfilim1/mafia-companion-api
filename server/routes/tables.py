from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from ..dependencies.auth import get_current_user_id
from ..dependencies.repo import get_games_repo, get_players_repo, get_tables_repo
from ..models.game import Game, NewGame
from ..models.page import PaginatedResponse
from ..models.tournament import Table
from ..repo.db import GamesRepo, PlayersRepo, TablesRepo

router = APIRouter(
    prefix="/tables",
    tags=["tables"],
)


@router.get("/{table_id}/")
async def get_table(
    table_id: int,
    *,
    tables_repo: Annotated[TablesRepo, Depends(get_tables_repo)],
) -> Table:
    table = await tables_repo.get_by_id(table_id)
    if table is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Table not found")
    return table


@router.delete("/{table_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_table(
    table_id: int,
    *,
    _: Annotated[int, Depends(get_current_user_id)],  # protect endpoint behind authorization
    tables_repo: Annotated[TablesRepo, Depends(get_tables_repo)],
) -> None:
    await tables_repo.delete(table_id)


@router.get("/{table_id}/games", tags=["games"])
async def get_table_games(
    table_id: int,
    *,
    games_repo: Annotated[GamesRepo, Depends(get_games_repo)],
) -> PaginatedResponse[Game]:
    games = await games_repo.get_by_table(table_id)
    return PaginatedResponse(
        page=1,
        total_pages=1,
        result=games,
    )


@router.post("/{table_id}/games", tags=["games"], status_code=status.HTTP_201_CREATED)
async def create_table_game(
    table_id: int,
    *,
    new_game: NewGame,
    current_user_id: Annotated[int, Depends(get_current_user_id)],
    players_repo: Annotated[PlayersRepo, Depends(get_players_repo)],
    tables_repo: Annotated[TablesRepo, Depends(get_tables_repo)],
    games_repo: Annotated[GamesRepo, Depends(get_games_repo)],
) -> Game:
    table = await tables_repo.get_by_id(table_id)
    if table is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Table not found")
    current_user = await players_repo.get_by_id(current_user_id)
    if table.judge_nickname != current_user.nickname:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the judge can create games",
        )
    game = await games_repo.create(table_id, players=new_game.players)
    return game
