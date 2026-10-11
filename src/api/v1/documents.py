from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, status

from src.dependencies.documents import DocumentServiceDep
from src.schemas.documents import DocumentOut, ErrorOut
from src.services.documents import DocumentNotFoundError

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get(
    "/search",
    response_model=list[DocumentOut],
    summary="Поиск документов по тексту",
    description=(
        "Ищет по тексту документа в индексе Elasticsearch и возвращает первые 20 "
        "найденных документов со всеми полями БД, упорядоченные по дате создания (новые первыми)."
    ),
)
async def search_documents(
    service: DocumentServiceDep,
    query: Annotated[str, Query(min_length=1, description="Произвольный текстовый запрос")],
) -> list[DocumentOut]:
    documents = await service.search(query)
    return [DocumentOut.model_validate(doc) for doc in documents]


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаление документа",
    description="Удаляет документ из БД и из поискового индекса по `id`.",
    responses={404: {"model": ErrorOut, "description": "Документ не найден"}},
)
async def delete_document(
    service: DocumentServiceDep,
    document_id: Annotated[int, Path(description="id документа")],
) -> None:
    try:
        await service.delete(document_id)
    except DocumentNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found") from None
