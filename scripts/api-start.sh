#!/bin/sh

# source common logging function
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
. "${SCRIPT_DIR}/common.sh"

# wait for PostgreSQL to be ready
log_msg "INFO" "startup" "postgres_check" "4" "wait for PostgreSQL to be ready..."
MAX_ATTEMPTS=30
ATTEMPT=0
while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
  if python3 -c "
import asyncio
import sys
import os
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
PG_URL = os.getenv('PG_URL')
if not PG_URL:
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f\"{ts} | {'ERROR':<8} | startup:postgres_check:pg_url - PG_URL is not set\", file=sys.stderr, flush=True)
    sys.exit(1)
engine = create_async_engine(PG_URL, future=True, echo=False)
async def check():
    try:
        async with engine.connect() as conn:
            await conn.execute(text('SELECT 1'))
        await engine.dispose()
        return True
    except Exception as e:
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f\"{ts} | {'ERROR':<8} | startup:postgres_check:connect - Connection failed: {e}\", file=sys.stderr, flush=True)
        await engine.dispose()
        return False
sys.exit(0 if asyncio.run(check()) else 1)
" 2>&1; then
    log_msg "INFO" "startup" "postgres_check" "33" "PostgreSQL is ready"
    break
  fi
  ATTEMPT=$((ATTEMPT + 1))
  log_msg "DEBUG" "startup" "postgres_check" "37" "PostgreSQL is not ready yet, waiting... (attempt $ATTEMPT/$MAX_ATTEMPTS)"
  sleep 2
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
  log_msg "ERROR" "startup" "postgres_check" "42" "PostgreSQL is not ready after $MAX_ATTEMPTS attempts"
  exit 1
fi

# run migrations
log_msg "INFO" "startup" "migrations" "36" "run database migrations..."
if ! alembic -c src/alembic.ini upgrade head 2>&1; then
    log_msg "ERROR" "startup" "migrations" "37" "database migrations failed"
    exit 1
fi
log_msg "INFO" "startup" "migrations" "38" "database migrations completed successfully"

# verify PostgreSQL migrations
log_msg "INFO" "startup" "migrations_check" "37" "verify PostgreSQL migrations..."
python3 -c "
import asyncio
import sys
from datetime import datetime
from sqlalchemy import text
from src.database import engine

def log(level: str, name: str, function: str, line: str, message: str, *, err: bool = False) -> None:
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    lvl = f\"{level:<8}\"
    print(f\"{ts} | {lvl} | {name}:{function}:{line} - {message}\", file=(sys.stderr if err else sys.stdout), flush=True)

async def check_migrations():
    try:
        async with engine.connect() as conn:
            # Check alembic_version table exists
            version_result = await conn.execute(text(\"\"\"
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'alembic_version'
                )
            \"\"\"))
            version_table_exists = version_result.scalar()
            
            if not version_table_exists:
                log('ERROR', 'startup', 'migrations_check', 'version_table', 'alembic_version table does not exist', err=True)
                return 1
            
            # get current migration version
            current_version = await conn.execute(text('SELECT version_num FROM alembic_version'))
            version = current_version.scalar()
            
            if not version:
                log('ERROR', 'startup', 'migrations_check', 'version', 'No migration version found', err=True)
                return 1
            
            log('INFO', 'startup', 'migrations_check', 'version', f'PostgreSQL migrations: current version = {version}')
            return 0
    except Exception as e:
        log('ERROR', 'startup', 'migrations_check', 'exception', f'Migration check failed: {e}', err=True)
        return 1

sys.exit(asyncio.run(check_migrations()))
" || {
    log_msg "ERROR" "startup" "migrations_check" "38" "database migrations verification failed"
    exit 1
}
log_msg "INFO" "startup" "migrations_check" "39" "database migrations verified successfully"

# verify PostgreSQL tables exist
log_msg "INFO" "startup" "tables_check" "40" "verify PostgreSQL tables..."
python3 -c "
import asyncio
import sys
from datetime import datetime
from sqlalchemy import text
from src.database import engine

def log(level: str, name: str, function: str, line: str, message: str, *, err: bool = False) -> None:
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    lvl = f\"{level:<8}\"
    print(f\"{ts} | {lvl} | {name}:{function}:{line} - {message}\", file=(sys.stderr if err else sys.stdout), flush=True)

async def check_tables():
    try:
        async with engine.connect() as conn:
            # List of required tables
            required_tables = ['payments', 'outbox']
            missing_tables = []
            
            for table in required_tables:
                result = await conn.execute(text(f\"\"\"
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = '{table}'
                    )
                \"\"\"))
                exists = result.scalar()
                if not exists:
                    missing_tables.append(table)
            
            if missing_tables:
                log('ERROR', 'startup', 'tables_check', 'missing', f'Missing tables: {missing_tables}', err=True)
                return 1
            
            log('INFO', 'startup', 'tables_check', 'verified', f'PostgreSQL tables verified: {len(required_tables)} tables exist')
            return 0
    except Exception as e:
        log('ERROR', 'startup', 'tables_check', 'exception', f'Table check failed: {e}', err=True)
        return 1

sys.exit(asyncio.run(check_tables()))
" || {
    log_msg "ERROR" "startup" "tables_check" "41" "database tables verification failed"
    exit 1
}
log_msg "INFO" "startup" "tables_check" "42" "database tables verified successfully"

log_msg "INFO" "startup" "app_start" "237" "Starting application..."

uvicorn src.main:app --host 0.0.0.0 --port 5000