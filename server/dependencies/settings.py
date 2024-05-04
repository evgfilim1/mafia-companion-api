from fastapi import FastAPI, Request

from ..utils.settings import Settings


async def get_app_settings(request: Request) -> Settings:
    app: FastAPI = request.app
    return app.state.settings
