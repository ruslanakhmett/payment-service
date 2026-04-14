#!/bin/sh

set -e

# source common logging function
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
. "${SCRIPT_DIR}/common.sh"

log_msg "INFO" "startup" "preflight" "1" "wait for PostgreSQL + required tables..."
python3 -c "
import asyncio
import os
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

PG_URL = os.getenv('PG_URL')
if not PG_URL:
    print('PG_URL is not set', file=sys.stderr, flush=True)
    raise SystemExit(1)

REQUIRED_TABLES = ('payments',)
MAX_ATTEMPTS = 90
SLEEP_S = 1.0

engine = create_async_engine(PG_URL, future=True, echo=False)

async def check_once() -> list[str]:
    async with engine.connect() as conn:
        await conn.execute(text('SELECT 1'))
        missing: list[str] = []
        for t in REQUIRED_TABLES:
            exists = await conn.execute(
                text(
                    \"\"\"
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_schema = 'public'
                          AND table_name = :t
                    )
                    \"\"\"
                ),
                {'t': t},
            )
            if not exists.scalar():
                missing.append(t)
        return missing

async def main() -> int:
    try:
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                missing = await check_once()
                if not missing:
                    return 0
                print(f'waiting for tables: {missing} (attempt {attempt}/{MAX_ATTEMPTS})', flush=True)
            except Exception as e:
                print(f'preflight failed: {e} (attempt {attempt}/{MAX_ATTEMPTS})', flush=True)
            await asyncio.sleep(SLEEP_S)
        return 1
    finally:
        await engine.dispose()

raise SystemExit(asyncio.run(main()))
"

log_msg "INFO" "startup" "app_start" "2" "Starting consumer..."
exec python -m src.main