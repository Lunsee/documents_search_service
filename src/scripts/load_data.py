import argparse
import ast
import asyncio
import csv
import logging
from collections.abc import Iterator
from datetime import datetime
from itertools import batched
from pathlib import Path

from src.config import settings
from src.infrastructure.database import SessionLocal, engine, init_db
from src.infrastructure.elasticsearch import create_es_client, ensure_index
from src.repositories.documents import DocumentRepository
from src.repositories.search_index import SearchIndexRepository

logger = logging.getLogger("load_data")

csv.field_size_limit(2**31 - 1)


def parse_rubrics(raw: str | None) -> list[str]:
    raw = (raw or "").strip()
    if not raw:
        return []
    try:
        value = ast.literal_eval(raw)
    except (ValueError, SyntaxError):
        value = raw.split(",")
    if isinstance(value, str):
        value = [value]
    return [str(item).strip() for item in value if str(item).strip()]


def read_csv(path: Path) -> Iterator[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            record = {
                "text": row["text"],
                "created_date": datetime.fromisoformat(row["created_date"].strip()),
                "rubrics": parse_rubrics(row.get("rubrics")),
            }
            if row.get("id"):
                record["id"] = int(row["id"])
            yield record


async def load(path: Path, force: bool, batch_size: int) -> None:
    if not path.exists():
        logger.warning("Файл %s не найден — загрузка пропущена", path)
        return

    es = create_es_client()
    search_index = SearchIndexRepository(es)
    try:
        await init_db()
        async with SessionLocal() as session:
            count = await DocumentRepository(session).count()
        if count and not force:
            logger.info("В БД уже %s документов — загрузка пропущена (используйте --force)", count)
            await ensure_index(es)
            return

        async with SessionLocal() as session, session.begin():
            await DocumentRepository(session).truncate()
        await ensure_index(es, recreate=True)

        total = 0
        for batch in batched(read_csv(path), batch_size):
            async with SessionLocal() as session, session.begin():
                inserted = await DocumentRepository(session).bulk_create(list(batch))
            await search_index.bulk_index(inserted)
            total += len(inserted)
            logger.info("Загружено %s документов", total)

        async with SessionLocal() as session, session.begin():
            await DocumentRepository(session).sync_id_sequence()
        await search_index.refresh()
        logger.info("Готово: %s документов", total)
    finally:
        await es.close()
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Загрузка CSV в Postgres и Elasticsearch")
    parser.add_argument("path", nargs="?", default=settings.data_path, type=Path)
    parser.add_argument("--force", action="store_true", help="очистить БД и индекс и загрузить заново")
    parser.add_argument("--batch-size", type=int, default=500)
    args = parser.parse_args()

    logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(message)s")
    asyncio.run(load(args.path, args.force, args.batch_size))


if __name__ == "__main__":
    main()
