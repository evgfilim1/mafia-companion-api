from fastapi import APIRouter, FastAPI, HTTPException, Request, status
from fastapi.responses import RedirectResponse

router = APIRouter()


@router.get("/", response_model=None, include_in_schema=False)
def redirect_to_docs(request: Request) -> RedirectResponse:
    current_app: FastAPI = request.app
    docs = current_app.docs_url
    if docs is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return RedirectResponse(docs.removeprefix("/"))
