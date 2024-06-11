import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response

from ..dependencies.auth import get_current_user_id
from ..dependencies.repo import get_games_repo, get_tables_repo, get_tournaments_repo
from ..models.page import PaginatedResponse
from ..models.score import ScoreRow
from ..models.tournament import NewTable, NewTournament, Table, Tournament
from ..repo.db import GamesRepo, TablesRepo, TournamentsRepo
from ..utils.calc_score import TournamentGame, calc_score
from ..utils.datetime_utils import get_current_datetime_utc

router = APIRouter(
    prefix="/tournaments",
    tags=["tournaments"],
)


@router.get("/")
async def get_all_tournaments(
    *,
    tournaments_repo: Annotated[TournamentsRepo, Depends(get_tournaments_repo)],
) -> PaginatedResponse[Tournament]:
    tournaments = await tournaments_repo.get_all()
    return PaginatedResponse(
        page=1,
        total_pages=1,
        result=tournaments,
    )


@router.get("/my")
async def get_my_tournaments(
    *,
    user_id: Annotated[str, Depends(get_current_user_id)],
    tournaments_repo: Annotated[TournamentsRepo, Depends(get_tournaments_repo)],
) -> PaginatedResponse[Tournament]:
    tournaments = await tournaments_repo.get_by_creator_user_id(user_id)
    return PaginatedResponse(
        page=1,
        total_pages=1,
        result=tournaments,
    )


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_tournament(
    *,
    current_user_id: Annotated[str, Depends(get_current_user_id)],
    tournaments_repo: Annotated[TournamentsRepo, Depends(get_tournaments_repo)],
    new_tournament: NewTournament,
) -> Tournament:
    if new_tournament.date_from >= new_tournament.date_to:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tournament start date must be before the end date",
        )
    if new_tournament.date_to < get_current_datetime_utc():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tournament end date must be in the future",
        )
    tournament = await tournaments_repo.create(
        new_tournament.name,
        date_from=new_tournament.date_from,
        date_to=new_tournament.date_to,
        created_by=current_user_id,
    )
    return tournament


@router.get("/{tournament_id}/")
async def get_tournament(
    tournament_id: UUID,
    *,
    tournaments_repo: Annotated[TournamentsRepo, Depends(get_tournaments_repo)],
) -> Tournament:
    tournament = await tournaments_repo.get_by_id(str(tournament_id))
    if tournament is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found")
    return tournament


@router.get("/{tournament_id}/scores", tags=["scores"])
async def get_tournament_scores(
    tournament_id: UUID,
    from_: Annotated[datetime.datetime | None, Query(alias="from")] = None,
    to: Annotated[datetime.datetime | None, Query()] = None,
    *,
    tournaments_repo: Annotated[TournamentsRepo, Depends(get_tournaments_repo)],
    tables_repo: Annotated[TablesRepo, Depends(get_tables_repo)],
    games_repo: Annotated[GamesRepo, Depends(get_games_repo)],
) -> PaginatedResponse[ScoreRow]:
    tournament = await tournaments_repo.get_by_id(str(tournament_id))
    if tournament is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found")
    tables = await tables_repo.get_by_tournament(str(tournament_id))
    data = []
    for table in tables:
        games = await games_repo.get_by_table(str(table.id), played_from=from_, played_to=to)
        for game in games:
            result = await games_repo.get_result(str(game.id))
            if result is not None:
                data.append(TournamentGame(game=game, result=result))
    score = calc_score(data)
    return PaginatedResponse(
        page=1,
        total_pages=1,
        result=score,
    )


@router.get("/{tournament_id}/scores.csv", tags=["scores"], include_in_schema=False)
async def get_tournament_scores_csv(
    tournament_id: int,
    *,
    tournaments_repo: Annotated[TournamentsRepo, Depends(get_tournaments_repo)],
    tables_repo: Annotated[TablesRepo, Depends(get_tables_repo)],
    games_repo: Annotated[GamesRepo, Depends(get_games_repo)],
) -> Response:
    # TODO: csv export
    # result = await get_tournament_scores(
    #     tournament_id,
    #     tournaments_repo=tournaments_repo,
    #     tables_repo=tables_repo,
    #     games_repo=games_repo,
    # )
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint not implemented",
    )


@router.get("/{tournament_id}/tables", tags=["tables"])
async def get_tournament_tables(
    tournament_id: UUID,
    *,
    tournaments_repo: Annotated[TournamentsRepo, Depends(get_tournaments_repo)],
    tables_repo: Annotated[TablesRepo, Depends(get_tables_repo)],
) -> PaginatedResponse[Table]:
    tournament = await tournaments_repo.get_by_id(str(tournament_id))
    if tournament is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found")
    tables = await tables_repo.get_by_tournament(str(tournament_id))
    return PaginatedResponse(
        page=1,
        total_pages=1,
        result=tables,
    )


@router.post("/{tournament_id}/tables", tags=["tables"], status_code=status.HTTP_201_CREATED)
async def create_table(
    tournament_id: UUID,
    *,
    new_table: NewTable,
    _: Annotated[int, Depends(get_current_user_id)],  # protect endpoint behind authorization
    tables_repo: Annotated[TablesRepo, Depends(get_tables_repo)],
) -> Table:
    table = await tables_repo.create(tournament_id, judge_username=new_table.judge_username)
    return table


@router.put("/{tournament_id}/")
async def update_tournament(
    tournament_id: UUID,
    *,
    _: Annotated[int, Depends(get_current_user_id)],  # protect endpoint behind authorization
    tournaments_repo: Annotated[TournamentsRepo, Depends(get_tournaments_repo)],
    new_tournament: NewTournament,
) -> Tournament:
    existing_tournament = await tournaments_repo.get_by_id(tournament_id)
    if existing_tournament is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found")
    if existing_tournament.name != new_tournament.name:
        await tournaments_repo.edit_name(tournament_id, new_tournament.name)
    if existing_tournament.date_from != new_tournament.date_from:
        await tournaments_repo.edit_date_from(tournament_id, new_tournament.date_from)
    if existing_tournament.date_to != new_tournament.date_to:
        await tournaments_repo.edit_date_to(tournament_id, new_tournament.date_to)
    return Tournament.model_construct(
        id=tournament_id,
        name=new_tournament.name,
        date_from=new_tournament.date_from,
        date_to=new_tournament.date_to,
    )
