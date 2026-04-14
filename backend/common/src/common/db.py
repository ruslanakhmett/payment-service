import asyncio
from collections.abc import AsyncIterator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine


def create_engine_and_session_factory(
    pg_url: str,
    *,
    pool_size: int = 20,
    max_overflow: int = 10,
    pool_timeout: int = 30,
    pool_recycle: int = 3600,
    echo: bool = False,
) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(
        pg_url,
        future=True,
        echo=echo,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=pool_timeout,
        pool_recycle=pool_recycle,
    )
    session_factory = async_sessionmaker(engine, autoflush=False, expire_on_commit=False)
    return engine, session_factory


async def get_session(session_factory: async_sessionmaker[AsyncSession]) -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        yield session


async def check_db_connection(session_factory: async_sessionmaker[AsyncSession]) -> bool:
    try:
        async with session_factory() as session:
            await session.execute(text("SELECT 1"))
            return True
    except Exception:
        return False


async def engine_dispose(engine: AsyncEngine) -> bool:
    try:
        await asyncio.wait_for(engine.dispose(), timeout=5.0)
        return True
    except Exception:
        return False
