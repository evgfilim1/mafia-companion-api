from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute

from .routes.auth import router as auth_router
from .routes.games import router as games_router
from .routes.health import router as health_router
from .routes.players import router as players_router
from .routes.root import router as root_router
from .routes.tables import router as tables_router
from .routes.tournaments import router as tournaments_router
from .routes.users import router as users_router
from .utils.app_lifespan import lifespan

app = FastAPI(
    title="Mafia companion API",
    version="0.1.0-alpha.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

for router in [
    auth_router,
    games_router,
    health_router,
    players_router,
    root_router,
    tables_router,
    tournaments_router,
    users_router,
]:
    app.include_router(router)

for route in app.routes:
    if isinstance(route, APIRoute):
        route.operation_id = route.name
