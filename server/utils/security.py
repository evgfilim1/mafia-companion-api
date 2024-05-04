import secrets

from passlib.context import CryptContext

password_context = CryptContext(
    schemes=["bcrypt_sha256"],
    deprecated="auto",
)


def generate_auth_token() -> str:
    return secrets.token_urlsafe(16)


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(32)
