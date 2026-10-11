import asyncio
import os
from collections.abc import AsyncIterator
from datetime import datetime

import asyncpg
import pytest
from httpx import ASGITransport, AsyncClient

os.environ["POSTGRES_DB"] = os.getenv("TEST_POSTGRES_DB", "search_test")
os.environ["ES_INDEX"] = os.getenv("TEST_ES_INDEX", "documents_test")

from src.config import settings  # noqa: E402
from src.infrastructure.database import SessionLocal, init_db  # noqa: E402
from src.infrastructure.elasticsearch import ensure_index  # noqa: E402
from src.repositories.documents import DocumentRepository  # noqa: E402
from src.repositories.search_index import SearchIndexRepository  # noqa: E402
from src.start_app import app  # noqa: E402

DOCUMENTS = [
    {"text": "Волга с двигателем от BMW", "created_date": datetime(2019, 1, 1), "rubrics": ["VK-1"]},
    {"text": "Новая волга на оценку", "created_date": datetime(2019, 6, 1), "rubrics": ["VK-1", "VK-2"]},
    {"text": "Конкурс на новый скин", "created_date": datetime(2019, 3, 1), "rubrics": []},
]


async def create_test_database() -> None:
    conn = await asyncpg.connect(
        user=settings.postgres_user,
        password=settings.postgres_password,
        host=settings.postgres_host,
        port=settings.postgres_port,
        database="postgres",
    )
    try:
        exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", settings.postgres_db)
        if not exists:
            await conn.execute(f'CREATE DATABASE "{settings.postgres_db}"')
    finally:
        await conn.close()


def pytest_sessionstart(session: pytest.Session) -> None:
    asyncio.run(create_test_database())


async def seed(documents: list[dict]) -> list[int]:
    async with SessionLocal() as session, session.begin():
        repo = DocumentRepository(session)
        await repo.truncate()
        inserted = await repo.bulk_create(documents) if documents else []

    search_index = SearchIndexRepository(app.state.es)
    await ensure_index(app.state.es, recreate=True)
    await search_index.bulk_index(inserted)
    await search_index.refresh()
    return [doc_id for doc_id, _ in inserted]


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    await init_db()
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client


@pytest.fixture
async def document_ids(client: AsyncClient) -> list[int]:
    return await seed(DOCUMENTS)
