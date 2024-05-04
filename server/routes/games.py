from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from ..dependencies.auth import get_current_user_id
from ..dependencies.repo import get_games_repo, get_players_repo, get_tables_repo
from ..models.game import Game, GameResult, NewGameResult
from ..repo.db import GamesRepo, PlayersRepo, TablesRepo

router = APIRouter(
    prefix="/games",
    tags=["games"],
)


@router.get("/{game_id}/")
async def get_game(
    game_id: int,
    *,
    games_repo: Annotated[GamesRepo, Depends(get_games_repo)],
) -> Game:
    game = await games_repo.get_by_id(game_id)
    if game is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")
    return game


@router.get("/{game_id}/result", response_model=GameResult)
async def get_game_result(
    game_id: int,
    *,
    games_repo: Annotated[GamesRepo, Depends(get_games_repo)],
) -> GameResult | Response:
    game = await games_repo.get_by_id(game_id)
    if game is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")
    result = await games_repo.get_result(game_id)
    if result is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return result


@router.post("/{game_id}/result")
async def set_game_result(
    game_id: int,
    *,
    current_user_id: Annotated[int, Depends(get_current_user_id)],
    players_repo: Annotated[PlayersRepo, Depends(get_players_repo)],
    tables_repo: Annotated[TablesRepo, Depends(get_tables_repo)],
    games_repo: Annotated[GamesRepo, Depends(get_games_repo)],
    result: NewGameResult,
) -> GameResult:
    game = await games_repo.get_by_id(game_id)
    if game is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")
    table = await tables_repo.get_by_id(game.table_id)
    if table is None:
        raise AssertionError("Game table not found")
    current_user = await players_repo.get_by_id(current_user_id)
    if table.judge_nickname != current_user.nickname:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only judge can set game result",
        )
    return await games_repo.set_result(game_id, result)
