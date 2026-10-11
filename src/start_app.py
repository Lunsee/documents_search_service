import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.v1.router import router as api_v1_router
from src.config import settings
from src.infrastructure.database import engine, init_db
from src.infrastructure.elasticsearch import create_es_client, ensure_index

logging.basicConfig(level=settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    es = create_es_client()
    await init_db()
    await ensure_index(es)
    app.state.es = es
    yield
    await es.close()
    await engine.dispose()


app = FastAPI(
    title="Documents Search Service",
    description="Очень простой поисковик по текстам документов.",
    version="0.1.0",
    lifespan=lifespan,
)
app.include_router(api_v1_router)


@app.get("/health", tags=["service"], summary="Проверка работоспособности")
async def health() -> dict[str, str]:
    return {"status": "ok"}
