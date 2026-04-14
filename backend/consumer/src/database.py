from pathlib import Path
import sys

try:
    from common.db import (
        check_db_connection as _check_db_connection,
        create_engine_and_session_factory,
        engine_dispose as _engine_dispose,
    )
except ModuleNotFoundError:
    common_src = Path(__file__).resolve().parents[2] / "common" / "src"
    sys.path.append(str(common_src))
    from common.db import (  # type: ignore
        check_db_connection as _check_db_connection,
        create_engine_and_session_factory,
        engine_dispose as _engine_dispose,
    )

from .settings import settings


engine, AsyncSessionFactory = create_engine_and_session_factory(
    settings.postgres.url, pool_size=10, max_overflow=10
)

async def check_db_connection() -> bool:
    return await _check_db_connection(AsyncSessionFactory)


async def engine_dispose() -> bool:
    return await _engine_dispose(engine)

