from elasticsearch import AsyncElasticsearch

from src.config import settings

INDEX_BODY = {
    "settings": {"number_of_shards": 1, "number_of_replicas": 0},
    "mappings": {
        "properties": {
            "id": {"type": "long"},
            "text": {"type": "text", "analyzer": "russian"},
        }
    },
}


def create_es_client() -> AsyncElasticsearch:
    return AsyncElasticsearch(settings.es_url)


async def ensure_index(es: AsyncElasticsearch, recreate: bool = False) -> None:
    index = settings.es_index
    if recreate:
        await es.options(ignore_status=404).indices.delete(index=index)
    if not await es.indices.exists(index=index):
        await es.indices.create(index=index, **INDEX_BODY)
