from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status

from ..dependencies.auth import get_current_user_id
from ..dependencies.repo import get_games_repo, get_tables_repo, get_users_repo
from ..models.game import Game, GameResult, NewGameResult
from ..repo.db import GamesRepo, TablesRepo, UsersRepo

router = APIRouter(
    prefix="/games",
    tags=["games"],
)


@router.get("/{game_id}/")
async def get_game(
    game_id: UUID,
    *,
    games_repo: Annotated[GamesRepo, Depends(get_games_repo)],
) -> Game:
    game = await games_repo.get_by_id(str(game_id))
    if game is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")
    return game


@router.get("/{game_id}/result", response_model=GameResult)
async def get_game_result(
    game_id: UUID,
    *,
    games_repo: Annotated[GamesRepo, Depends(get_games_repo)],
) -> GameResult | Response:
    game = await games_repo.get_by_id(str(game_id))
    if game is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")
    result = await games_repo.get_result(str(game_id))
    if result is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return result


@router.post("/{game_id}/result")
async def set_game_result(
    game_id: UUID,
    *,
    current_user_id: Annotated[str, Depends(get_current_user_id)],
    users_repo: Annotated[UsersRepo, Depends(get_users_repo)],
    tables_repo: Annotated[TablesRepo, Depends(get_tables_repo)],
    games_repo: Annotated[GamesRepo, Depends(get_games_repo)],
    result: NewGameResult,
) -> GameResult:
    game = await games_repo.get_by_id(str(game_id))
    if game is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")
    table = await tables_repo.get_by_id(str(game.table_id))
    if table is None:
        raise AssertionError("Game table not found")
    current_user = await users_repo.get_by_id(current_user_id)
    if table.judge_nickname != current_user.nickname:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only judge can set game result",
        )
    return await games_repo.set_result(str(game_id), result)
