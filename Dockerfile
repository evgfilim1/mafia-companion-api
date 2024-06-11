# syntax=docker/dockerfile:1
FROM postgres:16 AS db

COPY --from=ghcr.io/fboulnois/pg_uuidv7:1.5.0 \
    /usr/lib/postgresql/$PG_MAJOR/lib/pg_uuidv7.so \
    /usr/lib/postgresql/$PG_MAJOR/lib/pg_uuidv7.so
COPY --from=ghcr.io/fboulnois/pg_uuidv7:1.5.0 \
    /usr/share/postgresql/$PG_MAJOR/extension/pg_uuidv7.control \
    /usr/share/postgresql/$PG_MAJOR/extension/pg_uuidv7--1.5.sql \
    /usr/share/postgresql/$PG_MAJOR/extension/

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
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt \
    rm -f /etc/apt/apt.conf.d/docker-clean \
    && apt-get update \
    && apt-get install --no-install-recommends -y curl \
    && rm -rf /var/log/*
COPY server server

USER 1000
ENTRYPOINT ["/app/.venv/bin/python", "-m", "uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]

FROM runtime-base AS runtime

COPY --from=deps /app/.venv .venv
