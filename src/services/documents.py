from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.repositories.documents import DocumentRepository
from src.repositories.models import Document
from src.repositories.search_index import SearchIndexRepository


class DocumentNotFoundError(Exception):
    pass


class DocumentService:
    def __init__(
        self,
        session: AsyncSession,
        documents: DocumentRepository,
        search_index: SearchIndexRepository,
    ) -> None:
        self.session = session
        self.documents = documents
        self.search_index = search_index

    async def search(self, query: str) -> list[Document]:
        ids = await self.search_index.search_ids(query, settings.search_limit)
        if not ids:
            return []
        return await self.documents.get_by_ids_ordered_by_date(ids)

    async def delete(self, document_id: int) -> None:
        async with self.session.begin():
            if not await self.documents.delete(document_id):
                raise DocumentNotFoundError(document_id)
            await self.search_index.delete(document_id)
