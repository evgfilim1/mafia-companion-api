from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, status

from ..dependencies.auth import get_current_user_id
from ..dependencies.repo import get_games_repo, get_tables_repo, get_users_repo
from ..models.game import Game, NewGame
from ..models.page import PaginatedResponse
from ..models.tournament import Table
from ..repo.db import GamesRepo, TablesRepo, UsersRepo

router = APIRouter(
    prefix="/tables",
    tags=["tables"],
)


@router.get("/{table_id}/")
async def get_table(
    table_id: UUID,
    *,
    tables_repo: Annotated[TablesRepo, Depends(get_tables_repo)],
) -> Table:
    table = await tables_repo.get_by_id(str(table_id))
    if table is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Table not found")
    return table


@router.delete("/{table_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_table(
    table_id: UUID,
    *,
    _: Annotated[int, Depends(get_current_user_id)],  # protect endpoint behind authorization
    tables_repo: Annotated[TablesRepo, Depends(get_tables_repo)],
) -> None:
    await tables_repo.delete(str(table_id))


@router.get("/{table_id}/games/", tags=["games"])
async def get_table_games(
    table_id: UUID,
    *,
    games_repo: Annotated[GamesRepo, Depends(get_games_repo)],
) -> PaginatedResponse[Game]:
    games = await games_repo.get_by_table(str(table_id))
    return PaginatedResponse(
        page=1,
        total_pages=1,
        result=games,
    )


async def create_table_game_impl(
    table_id: UUID,
    game_id: Annotated[UUID | None, Path()],
    *,
    new_game: NewGame,
    current_user_id: Annotated[str, Depends(get_current_user_id)],
    users_repo: Annotated[UsersRepo, Depends(get_users_repo)],
    tables_repo: Annotated[TablesRepo, Depends(get_tables_repo)],
    games_repo: Annotated[GamesRepo, Depends(get_games_repo)],
) -> Game:
    table = await tables_repo.get_by_id(str(table_id))
    if table is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Table not found")
    current_user = await users_repo.get_by_id(current_user_id)
    if table.judge_nickname != current_user.nickname:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the judge can create games",
        )
    if game_id is not None:
        existing_game = await games_repo.get_by_id(str(game_id))
        if existing_game is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot edit existing games",
            )
    game = await games_repo.create(str(table_id), players=new_game.players, id_=game_id)
    return game


@router.post("/{table_id}/games/", tags=["games"], status_code=status.HTTP_201_CREATED)
async def create_table_game(
    table_id: UUID,
    *,
    new_game: NewGame,
    current_user_id: Annotated[str, Depends(get_current_user_id)],
    users_repo: Annotated[UsersRepo, Depends(get_users_repo)],
    tables_repo: Annotated[TablesRepo, Depends(get_tables_repo)],
    games_repo: Annotated[GamesRepo, Depends(get_games_repo)],
) -> Game:
    return await create_table_game_impl(
        table_id=table_id,
        game_id=None,
        new_game=new_game,
        current_user_id=current_user_id,
        users_repo=users_repo,
        tables_repo=tables_repo,
        games_repo=games_repo,
    )


@router.put("/{table_id}/games/{game_id}", tags=["games"])
async def put_table_game(
    table_id: UUID,
    game_id: UUID,
    *,
    new_game: NewGame,
    current_user_id: Annotated[str, Depends(get_current_user_id)],
    users_repo: Annotated[UsersRepo, Depends(get_users_repo)],
    tables_repo: Annotated[TablesRepo, Depends(get_tables_repo)],
    games_repo: Annotated[GamesRepo, Depends(get_games_repo)],
) -> Game:
    return await create_table_game_impl(
        table_id=table_id,
        game_id=game_id,
        new_game=new_game,
        current_user_id=current_user_id,
        users_repo=users_repo,
        tables_repo=tables_repo,
        games_repo=games_repo,
    )
