from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from redis.asyncio import Redis
from sqlalchemy import URL, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ..db import models as db_models
from .settings import Settings


@asynccontextmanager
async def lifespan(current_app: FastAPI) -> AsyncIterator[None]:
    env = Settings.from_env()
    redis = Redis(
        host=env.redis_host,
        port=env.redis_port,
        db=env.redis_db,
        password=env.redis_password,
    )
    engine = create_async_engine(
        URL.create(
            drivername="postgresql+asyncpg",
            username=env.postgres_user,
            password=env.postgres_password,
            host=env.postgres_host,
            port=env.postgres_port,
            database=env.postgres_db,
        )
    )
    db_sessions = async_sessionmaker(engine)
    if env.invite_code is None:
        session: AsyncSession
        async with db_sessions() as session:
            first_user = (await session.execute(select(db_models.User).limit(1))).scalars().first()
            if first_user is None:
                raise RuntimeError(
                    "Invite code must be set if no users are present in the database"
                )

    current_app.state.settings = env
    current_app.state.redis_pool = redis
    current_app.state.db_pool = db_sessions
    yield

    await redis.aclose()
    await engine.dispose()
