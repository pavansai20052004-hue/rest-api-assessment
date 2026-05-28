from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI

from app.api.routes import router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.db.database import create_db_schema


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    if settings.database_auto_create:
        await create_db_schema()
    yield


app = FastAPI(
    title="GitHub Repository Metadata API",
    version="1.0.0",
    description="Async REST API that stores and refreshes GitHub repository metadata.",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    lifespan=lifespan,
)

register_exception_handlers(app)
app.include_router(router)
