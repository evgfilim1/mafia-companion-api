from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class StatusOk(BaseModel):
    status: Literal["ok"] = "ok"


@router.get("/health", response_model=StatusOk, tags=["healthcheck"])
async def healthcheck() -> StatusOk:
    # TODO: implement more complex healthcheck
    return StatusOk()
