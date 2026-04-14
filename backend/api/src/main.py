from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import payments_router, system_router, webhook_router
from .database import check_db_connection, engine_dispose

from .settings import settings
from .utils import log_msg

API_V1_PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan""" 
    # startup
    log_msg("INFO", "startup", "app_start", "1", "Application startup: initializing resources...")
    try:
        if not await check_db_connection():
            raise RuntimeError("Failed to connect to database")
        log_msg("INFO", "startup", "db_check", "2", "Database connection established successfully")

        yield

    except Exception as e:
        log_msg("ERROR", "startup", "app_start", "3", f"Application startup failed: {e}")
        raise

    finally:
        # shutdown
        log_msg("INFO", "shutdown", "cleanup", "1", "Application shutdown: cleaning up resources...")
        try:
            try:
                if await engine_dispose():
                    log_msg("INFO", "shutdown", "db_close", "2", "Database connection closed successfully")
                else:
                    log_msg("WARNING", "shutdown", "db_close", "3", "Error closing database connection")
            except Exception as e:
                log_msg("ERROR", "shutdown", "db_close", "4", f"Error closing database: {e}")

        except Exception as e:
            log_msg("ERROR", "shutdown", "cleanup", "5", f"Shutdown error: {e}")
            raise


app = FastAPI(
    title="PAYLY",
    description="Main API for managing the PAYLY platform",
    version="1.0.0",
    contact={
        "name": "Ruslan Akhmetshin",
        "email": "sccrsccr1@gmail.com",
    },
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(payments_router, prefix=API_V1_PREFIX)
app.include_router(system_router, prefix=API_V1_PREFIX)
app.include_router(webhook_router, prefix=API_V1_PREFIX)