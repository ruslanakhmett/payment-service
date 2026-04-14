#!/bin/bash
set -euo pipefail

# source common logging function
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
. "${SCRIPT_DIR}/common.sh"

POSTGRES_SUPER_USER="${POSTGRES_USER}"
POSTGRES_SUPER_PASSWORD="${POSTGRES_PASSWORD}"

POSTGRES_APP_USER="${POSTGRES_USER_PROD}"
POSTGRES_APP_PASSWORD="${POSTGRES_PASSWORD_PROD}"
POSTGRES_APP_DB="${POSTGRES_DB_PROD}"

wait_for_postgres() {
  local max_attempts=30
  for ((attempt=1; attempt<=max_attempts; attempt++)); do
    if psql -U "$POSTGRES_SUPER_USER" -c "SELECT 1;" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done
  log_msg "ERROR" "postgres_init" "wait_for_postgres" "1" "PostgreSQL not ready after $max_attempts attempts"
  exit 1
}

initialize_database() {
  log_msg "INFO" "postgres_init" "initialize_database" "1" "Updating superuser password..."
  psql -U "$POSTGRES_SUPER_USER" -c "ALTER USER \"${POSTGRES_SUPER_USER}\" WITH PASSWORD '${POSTGRES_SUPER_PASSWORD}';"

  log_msg "INFO" "postgres_init" "initialize_database" "2" "Ensuring application user exists..."
  psql -U "$POSTGRES_SUPER_USER" -tc "SELECT 1 FROM pg_roles WHERE rolname='${POSTGRES_APP_USER}'" | grep -q 1 \
    && psql -U "$POSTGRES_SUPER_USER" -c "ALTER USER \"${POSTGRES_APP_USER}\" WITH PASSWORD '${POSTGRES_APP_PASSWORD}';" \
    || psql -U "$POSTGRES_SUPER_USER" -c "CREATE USER \"${POSTGRES_APP_USER}\" WITH PASSWORD '${POSTGRES_APP_PASSWORD}';"

  log_msg "INFO" "postgres_init" "initialize_database" "3" "Ensuring application database exists..."
  psql -U "$POSTGRES_SUPER_USER" -tc "SELECT 1 FROM pg_database WHERE datname='${POSTGRES_APP_DB}'" | grep -q 1 \
    || psql -U "$POSTGRES_SUPER_USER" -c "CREATE DATABASE \"${POSTGRES_APP_DB}\" OWNER \"${POSTGRES_APP_USER}\" ENCODING 'UTF8';"

  log_msg "INFO" "postgres_init" "initialize_database" "4" "Granting privileges..."
  psql -U "$POSTGRES_SUPER_USER" -c "GRANT ALL PRIVILEGES ON DATABASE \"${POSTGRES_APP_DB}\" TO \"${POSTGRES_APP_USER}\";"
  psql -U "$POSTGRES_SUPER_USER" -d "$POSTGRES_APP_DB" -c "GRANT ALL PRIVILEGES ON SCHEMA public TO \"${POSTGRES_APP_USER}\";"
  psql -U "$POSTGRES_SUPER_USER" -d "$POSTGRES_APP_DB" -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO \"${POSTGRES_APP_USER}\";"
  psql -U "$POSTGRES_SUPER_USER" -d "$POSTGRES_APP_DB" -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON SEQUENCES TO \"${POSTGRES_APP_USER}\";"
  psql -U "$POSTGRES_SUPER_USER" -c "GRANT CONNECT ON DATABASE \"${POSTGRES_APP_DB}\" TO \"${POSTGRES_APP_USER}\";"

  log_msg "INFO" "postgres_init" "initialize_database" "9" "database initialization completed successfully"
}

wait_for_postgres
initialize_database