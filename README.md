# Documents Search Service

Очень простой поисковик по текстам документов.

- **FastAPI** — HTTP API (асинхронный)
- **PostgreSQL** — хранение документов (SQLAlchemy 2 async + asyncpg)
- **Elasticsearch 8** — поисковый индекс (асинхронный клиент, русский анализатор)
- **uv** — управление зависимостями
- **Docker / docker compose** — запуск всего окружения

## Структура проекта

```
src/
├── start_app.py             # точка входа FastAPI, lifespan
├── config.py                # настройки из .env (pydantic-settings)
├── api/v1/
│   ├── router.py            # общий роутер /api/v1
│   └── documents.py         # роуты /api/v1/documents
├── dependencies/documents.py  # DI: сборка сервиса
├── infrastructure/
│   ├── database.py          # engine, сессии, создание таблиц
│   └── elasticsearch.py     # клиент ES, создание индекса
├── repositories/
│   ├── models.py            # ORM-модель Document
│   ├── documents.py         # работа с таблицей documents (PostgreSQL)
│   └── search_index.py      # работа с индексом (Elasticsearch)
├── services/documents.py    # бизнес-логика: поиск и удаление
├── schemas/documents.py     # pydantic-схемы ответов
└── scripts/load_data.py     # загрузка CSV в БД и индекс
data/posts.csv               # тестовый массив данных
docs.json                    # OpenAPI-документация
```

## Структуры данных

**БД (таблица `documents`):** `id`, `rubrics` (массив строк), `text`, `created_date`.

**Индекс (`documents`):** `id`, `text`.

## Быстрый старт (Docker)

1. Тестовые данные уже лежат в `data/posts.csv` (колонки: `text`, `created_date`, `rubrics`).
2. Создайте `.env` из примера:
   ```bash
   cp .env.example .env
   ```
3. Поднимите всё окружение:
   ```bash
   docker compose up -d --build
   ```

- поднимется `postgres` и `elasticsearch` (с healthcheck-ами);
- одноразовый сервис `loader` создаст таблицу и индекс и загрузит `data/posts.csv`
  (если в БД уже есть документы, загрузка пропускается);
- после успешной загрузки стартует `app` на `http://localhost:8000`.

Swagger UI: http://localhost:8000/docs

Перезалить данные с нуля (очистить БД и индекс):
```bash
docker compose run --rm loader python -m src.scripts.load_data --force
```

Остановить и удалить данные:
```bash
docker compose down -v
```

## Локальный запуск без Docker 

Нужны Python 3.12 и [uv](https://docs.astral.sh/uv/).

```bash
cp .env.example .env            # POSTGRES_HOST=localhost, ES_URL=http://localhost:9200
docker compose up -d postgres elasticsearch
uv sync
uv run python -m src.scripts.load_data          # загрузить data/posts.csv
uv run uvicorn src.start_app:app --reload
```

## Переменные окружения

| Переменная | По умолчанию | Описание |
|---|---|---|
| `APP_PORT` | `8000` | порт API на хосте |
| `SEARCH_LIMIT` | `20` | сколько документов возвращает поиск |
| `LOG_LEVEL` | `INFO` | уровень логирования |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | `search` | доступ к PostgreSQL |
| `POSTGRES_HOST` / `POSTGRES_PORT` | `localhost` / `5433` | адрес PostgreSQL с хоста (внутри compose — `postgres:5432`) |
| `ES_URL` | `http://localhost:9200` | адрес Elasticsearch (в compose — `http://elasticsearch:9200`) |
| `ES_INDEX` | `documents` | имя индекса |
| `ES_PORT` | `9200` | порт Elasticsearch на хосте |
| `DATA_PATH` | `data/posts.csv` | путь к CSV для загрузчика |

## API

Полное описание — в [`docs.json`](docs.json) (OpenAPI 3.1).

### Поиск

```
GET /api/v1/documents/search?query=<текст>
```

Ищет по тексту в Elasticsearch, берёт первые 20 релевантных документов и возвращает их
со всеми полями из БД, отсортированными по `created_date` (новые первыми).

```bash
curl "http://localhost:8000/api/v1/documents/search?query=волга"
```

```json
[
  {
    "id": 20,
    "rubrics": ["VK-1603736028819866", "VK-36585482909", "VK-21780001620"],
    "text": "Stage 4 надеюсь последний. ...",
    "created_date": "2019-08-09T16:20:26"
  }
]
```

### Удаление

```
DELETE /api/v1/documents/{id}
```

Удаляет документ из БД и из индекса. `204` — удалён, `404` — не найден.

```bash
curl -X DELETE http://localhost:8000/api/v1/documents/20
```

### Healthcheck

```
GET /health
```

## Тесты

Функциональные тесты ходят в API через httpx и работают с настоящими Postgres и Elasticsearch.
Используются отдельная база `search_test` (создаётся автоматически) и индекс `documents_test`,
так что основные данные не затрагиваются.

```bash
docker compose up -d postgres elasticsearch
uv sync
uv run pytest -v
```

## Обновление docs.json

```bash
uv run python -c "import json; from src.start_app import app; json.dump(app.openapi(), open('docs.json','w',encoding='utf-8'), ensure_ascii=False, indent=2)"
```
