from collections.abc import Iterable

from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk

from src.config import settings


class SearchIndexRepository:
    def __init__(self, es: AsyncElasticsearch, index: str = settings.es_index) -> None:
        self.es = es
        self.index = index

    async def search_ids(self, query: str, limit: int) -> list[int]:
        response = await self.es.search(
            index=self.index,
            query={"match": {"text": {"query": query}}},
            size=limit,
            source=False,
        )
        return [int(hit["_id"]) for hit in response["hits"]["hits"]]

    async def delete(self, document_id: int) -> None:
        await self.es.options(ignore_status=404).delete(
            index=self.index, id=str(document_id), refresh=True
        )

    async def bulk_index(self, documents: Iterable[tuple[int, str]]) -> None:
        actions = (
            {"_index": self.index, "_id": str(doc_id), "id": doc_id, "text": text}
            for doc_id, text in documents
        )
        await async_bulk(self.es, actions)

    async def refresh(self) -> None:
        await self.es.indices.refresh(index=self.index)
