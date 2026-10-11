from datetime import datetime, timedelta

from httpx import AsyncClient

from src.config import settings
from src.infrastructure.database import SessionLocal
from src.repositories.models import Document
from src.start_app import app
from tests.conftest import seed

SEARCH_URL = "/api/v1/documents/search"


async def test_health(client: AsyncClient):
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_search_returns_documents_sorted_by_date(client: AsyncClient, document_ids):
    response = await client.get(SEARCH_URL, params={"query": "волга"})

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert set(data[0]) == {"id", "rubrics", "text", "created_date"}
    assert data[0]["text"] == "Новая волга на оценку"
    assert data[0]["rubrics"] == ["VK-1", "VK-2"]
    assert data[1]["text"] == "Волга с двигателем от BMW"


async def test_search_no_results(client: AsyncClient, document_ids):
    response = await client.get(SEARCH_URL, params={"query": "абракадабра"})

    assert response.status_code == 200
    assert response.json() == []


async def test_search_empty_query(client: AsyncClient):
    response = await client.get(SEARCH_URL, params={"query": ""})

    assert response.status_code == 422


async def test_search_returns_max_20(client: AsyncClient):
    start = datetime(2020, 1, 1)
    await seed([
        {"text": f"пост про котов {i}", "created_date": start + timedelta(days=i), "rubrics": []}
        for i in range(25)
    ])

    response = await client.get(SEARCH_URL, params={"query": "коты"})

    assert response.status_code == 200
    dates = [doc["created_date"] for doc in response.json()]
    assert len(dates) == 20
    assert dates == sorted(dates, reverse=True)


async def test_delete_document(client: AsyncClient, document_ids):
    doc_id = document_ids[0]

    response = await client.delete(f"/api/v1/documents/{doc_id}")

    assert response.status_code == 204
    async with SessionLocal() as session:
        assert await session.get(Document, doc_id) is None
    assert not await app.state.es.exists(index=settings.es_index, id=str(doc_id))

    response = await client.get(SEARCH_URL, params={"query": "волга"})
    assert doc_id not in [doc["id"] for doc in response.json()]


async def test_delete_not_found(client: AsyncClient, document_ids):
    response = await client.delete("/api/v1/documents/999999")

    assert response.status_code == 404
