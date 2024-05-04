from typing import Annotated, Callable

from fastapi import Depends, FastAPI, Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from ..repo.cache import AuthRepo
from ..repo.db import GamesRepo, PlayersRepo, TablesRepo, TournamentsRepo, UsersRepo


async def get_db_connection(request: Request) -> AsyncSession:
    app: FastAPI = request.app
    pool: Callable[[], AsyncSession] = app.state.db_pool
    async with pool() as connection:
        yield connection
        await connection.commit()


def get_users_repo(
    connection: Annotated[AsyncSession, Depends(get_db_connection)],
) -> UsersRepo:
    return UsersRepo(connection)


def get_players_repo(
    connection: Annotated[AsyncSession, Depends(get_db_connection)],
) -> PlayersRepo:
    return PlayersRepo(connection)


def get_tournaments_repo(
    connection: Annotated[AsyncSession, Depends(get_db_connection)],
) -> TournamentsRepo:
    return TournamentsRepo(connection)


def get_tables_repo(
    connection: Annotated[AsyncSession, Depends(get_db_connection)],
) -> TablesRepo:
    return TablesRepo(connection)


def get_games_repo(
    connection: Annotated[AsyncSession, Depends(get_db_connection)],
) -> GamesRepo:
    return GamesRepo(connection)


def get_cache_connection(request: Request) -> Redis:
    app: FastAPI = request.app
    return app.state.redis_pool


def get_auth_repo(
    connection: Annotated[Redis, Depends(get_cache_connection)],
) -> AuthRepo:
    return AuthRepo(connection)
