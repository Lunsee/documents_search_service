from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database import get_session
from src.repositories.documents import DocumentRepository
from src.repositories.search_index import SearchIndexRepository
from src.services.documents import DocumentService


def get_document_service(
    request: Request, session: Annotated[AsyncSession, Depends(get_session)]
) -> DocumentService:
    return DocumentService(
        session=session,
        documents=DocumentRepository(session),
        search_index=SearchIndexRepository(request.app.state.es),
    )


DocumentServiceDep = Annotated[DocumentService, Depends(get_document_service)]
