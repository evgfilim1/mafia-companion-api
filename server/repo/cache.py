from datetime import timedelta
from typing import overload

from redis.asyncio import Redis

from ..utils.security import generate_auth_token, generate_refresh_token
from .base import BaseRepo


@overload
def _b2u(b: bytes) -> str: ...


@overload
def _b2u(b: str) -> str: ...


@overload
def _b2u(b: None) -> None: ...


def _b2u(b: bytes | str | None) -> str | None:
    """Converts bytes to string if needed."""
    if b is None:
        return None
    if isinstance(b, bytes):
        return b.decode()
    return b


class AuthRepo(BaseRepo[Redis]):
    _AUTH_FORMAT = "auth:{token}"
    _REFRESH_FORMAT = "refresh:{token}"
    _AUTH_EXPIRE = timedelta(hours=3)
    _REFRESH_EXPIRE = timedelta(days=14)

    async def _find_keys(self, user_id: str) -> tuple[list[str], list[str]]:
        auth_keys, refresh_keys = [], []
        async for key in self._conn.scan_iter(match=self._AUTH_FORMAT.format(token="*")):
            if await self._conn.get(key) == user_id:
                auth_keys.append(_b2u(key))
        async for key in self._conn.scan_iter(match=self._REFRESH_FORMAT.format(token="*")):
            if await self._conn.get(key) == user_id:
                refresh_keys.append(_b2u(key))
        return auth_keys, refresh_keys

    async def save_user_auth(self, user_id: str) -> tuple[str, str]:
        auth, refresh = generate_auth_token(), generate_refresh_token()
        await self._conn.set(
            self._AUTH_FORMAT.format(token=auth),
            user_id,
            ex=self._AUTH_EXPIRE,
        )
        await self._conn.set(
            self._REFRESH_FORMAT.format(token=refresh),
            user_id,
            ex=self._REFRESH_EXPIRE,
        )
        return auth, refresh

    async def get_user_id_by_auth(self, auth_token: str) -> str | None:
        res = await self._conn.get(self._AUTH_FORMAT.format(token=auth_token))
        if res is None:
            return None
        return _b2u(res)

    async def update_tokens_by_refresh(self, refresh_token: str) -> tuple[str, str] | None:
        user_id: bytes | str | None = _b2u(
            await self._conn.get(self._REFRESH_FORMAT.format(token=refresh_token))
        )
        if user_id is None:
            return None
        await self.revoke_all_tokens(user_id)
        return await self.save_user_auth(user_id)

    async def revoke_all_tokens(self, user_id: str) -> None:
        auth_keys, refresh_keys = await self._find_keys(user_id)
        await self._conn.delete(*auth_keys, *refresh_keys)
