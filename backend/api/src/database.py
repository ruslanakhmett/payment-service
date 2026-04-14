from collections.abc import AsyncIterator
from pathlib import Path
import sys

from sqlalchemy.ext.asyncio import AsyncAttrs, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from .settings import settings

try:
    from common.db import (
        check_db_connection as _check_db_connection,
        create_engine_and_session_factory,
        engine_dispose as _engine_dispose,
        get_session as _get_session,
    )
except ModuleNotFoundError:
    # локальный запуск вне docker-compose (common пакет не на PYTHONPATH)
    common_src = Path(__file__).resolve().parents[2] / "common" / "src"
    sys.path.append(str(common_src))
    from common.db import (  # type: ignore
        check_db_connection as _check_db_connection,
        create_engine_and_session_factory,
        engine_dispose as _engine_dispose,
        get_session as _get_session,
    )


pg_url = settings.postgres.pg_url

engine, AsyncSessionFactory = create_engine_and_session_factory(
    pg_url, pool_size=20, max_overflow=10, pool_timeout=30, pool_recycle=3600
)


class Base(AsyncAttrs, DeclarativeBase):
    pass


async def get_session() -> AsyncIterator[AsyncSession]:
    async for s in _get_session(AsyncSessionFactory):
        yield s


async def check_db_connection():
    return await _check_db_connection(AsyncSessionFactory)


async def engine_dispose():
    return await _engine_dispose(engine)
