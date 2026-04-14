import secrets

from fastapi import Header, HTTPException, status

from .settings import settings


async def verify_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> None:
    expected = settings.api_key
    if x_api_key is None or not secrets.compare_digest(x_api_key, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
