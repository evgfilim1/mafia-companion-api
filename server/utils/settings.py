import os
from dataclasses import dataclass
from typing import Self


# black has a bug with new type syntax: https://github.com/psf/black/issues/4071
# fmt: off
def _get_env[T](
    key: str,
    type_: type[T] = str,
    *,
    is_optional: bool = False,
    default: T | None = None,
) -> T | None:
    # fmt: on
    unset = object()
    value = os.getenv(key, unset)
    if value is unset:
        if is_optional:
            return default
        raise ValueError(f"Missing required environment variable {key}")
    return type_(value)


@dataclass(kw_only=True)
class Settings:
    postgres_host: str
    postgres_port: int = 5432
    postgres_user: str
    postgres_password: str
    postgres_db: str

    redis_host: str
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str | None = None

    invite_code: str | None = None

    @classmethod
    def from_env(cls) -> Self:
        return cls(
            postgres_host=_get_env("POSTGRES_HOST"),
            postgres_port=_get_env("POSTGRES_PORT", int, is_optional=True, default=5432),
            postgres_user=_get_env("POSTGRES_USER"),
            postgres_password=_get_env("POSTGRES_PASSWORD"),
            postgres_db=_get_env("POSTGRES_DB"),
            redis_host=_get_env("REDIS_HOST"),
            redis_port=_get_env("REDIS_PORT", int, is_optional=True, default=6379),
            redis_db=_get_env("REDIS_DB", int, is_optional=True, default=0),
            redis_password=_get_env("REDIS_PASSWORD", is_optional=True),
            invite_code=_get_env("INVITE_CODE", is_optional=True),
        )
