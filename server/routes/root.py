from typing import Literal

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

router = APIRouter()


class StatusOk(BaseModel):
    status: Literal["ok"] = "ok"


@router.get("/", response_model=None, include_in_schema=False)
def redirect_to_docs(request: Request) -> RedirectResponse | StatusOk:
    current_app: FastAPI = request.app
    docs = current_app.docs_url
    if docs is None:
        return StatusOk()
    return RedirectResponse(docs.removeprefix("/"))
