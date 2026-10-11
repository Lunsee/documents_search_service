from collections.abc import Sequence

from sqlalchemy import delete, func, insert, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.models import Document


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_ids_ordered_by_date(self, ids: Sequence[int]) -> list[Document]:
        result = await self.session.scalars(
            select(Document)
            .where(Document.id.in_(ids))
            .order_by(Document.created_date.desc(), Document.id.desc())
        )
        return list(result)

    async def delete(self, document_id: int) -> bool:
        deleted_id = await self.session.scalar(
            delete(Document).where(Document.id == document_id).returning(Document.id)
        )
        return deleted_id is not None

    async def count(self) -> int:
        return await self.session.scalar(select(func.count()).select_from(Document)) or 0

    async def truncate(self) -> None:
        await self.session.execute(text(f"TRUNCATE {Document.__tablename__} RESTART IDENTITY"))

    async def bulk_create(self, rows: list[dict]) -> list[tuple[int, str]]:
        result = await self.session.execute(
            insert(Document).returning(Document.id, Document.text), rows
        )
        return [(row.id, row.text) for row in result]

    async def sync_id_sequence(self) -> None:
        await self.session.execute(
            text(
                f"SELECT setval(pg_get_serial_sequence('{Document.__tablename__}', 'id'), "
                f"COALESCE((SELECT MAX(id) FROM {Document.__tablename__}), 1))"
            )
        )
