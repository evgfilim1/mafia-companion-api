# syntax=docker/dockerfile:1
FROM python:3.12-slim AS deps

WORKDIR /app

RUN python -m venv .venv
RUN --mount=type=bind,source=requirements.txt,target=requirements.txt \
    --mount=type=cache,target=/root/.cache/pip \
    .venv/bin/pip install -r requirements.txt uvicorn

FROM deps AS deps-dev

RUN --mount=type=bind,source=dev-requirements.txt,target=dev-requirements.txt \
    --mount=type=cache,target=/root/.cache/pip \
    .venv/bin/pip install -r dev-requirements.txt

FROM python:3.12-slim AS db-migrate

WORKDIR /app

COPY --from=deps-dev /app/.venv .venv
COPY alembic.ini .
COPY migrations migrations

USER 1000
ENTRYPOINT ["/app/.venv/bin/python", "-m", "alembic"]
CMD ["upgrade", "head"]

FROM python:3.12-slim AS runtime-base

EXPOSE 8000
WORKDIR /app
COPY server server

USER 1000
ENTRYPOINT ["/app/.venv/bin/python", "-m", "uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]

FROM runtime-base AS runtime

COPY --from=deps /app/.venv .venv
