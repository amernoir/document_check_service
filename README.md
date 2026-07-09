# Document Check Service

AI-agent for automated verification of document packages for preferential loan programs.

## Quick Start

### With Docker (recommended)

```bash
docker compose up --build
```

After starting, run the migration:
```bash
docker compose exec app alembic upgrade head
```

Service available at: http://localhost:8000
Swagger UI: http://localhost:8000/docs

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up database
createdb doccheck
alembic upgrade head

# Run server
uvicorn app.main:app --reload
```

## Running Tests

```bash
# Unit tests
pytest tests/test_classifier.py tests/test_validator.py tests/test_status_resolver.py -v

# Integration tests (requires running DB)
pytest tests/test_api.py -v

# All tests
pytest tests/ -v
```

## Technologies

- **FastAPI** — modern async web framework with automatic OpenAPI docs
- **PostgreSQL** — relational database for storing check history
- **SQLAlchemy 2.0** — ORM for database operations
- **Alembic** — database migration management
- **Pydantic v2** — data validation and serialization
- **Docker Compose** — containerized deployment

## Architecture

```
app/
├── api/          # FastAPI routers (HTTP layer)
├── schemas/      # Pydantic models (request/response)
├── services/     # Business logic (pure functions, no DB deps)
│   ├── classifier.py      # Document type detection
│   ├── validator.py       # Package completeness validation
│   ├── status_resolver.py # Status determination
│   └── check_service.py   # Orchestrator
├── repositories/ # Database operations (CRUD)
├── models/       # SQLAlchemy models
├── core/         # Config and utilities
└── db/           # Database session management
```

### Design Decisions

- **Pure business logic**: `classifier.py`, `validator.py`, `status_resolver.py` are pure functions with no dependencies on FastAPI or SQLAlchemy — easy to unit test
- **Stub extracted data**: AI module integration is simulated; real extraction would require additional AI services
- **Local file storage**: Files stored in `uploads/` directory with UUID-based names

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| DATABASE_URL | postgresql://postgres:postgres@localhost:5432/doccheck | PostgreSQL connection string |
| UPLOAD_DIR | ./uploads | Directory for storing uploaded files |
| APP_HOST | 0.0.0.0 | Server host |
| APP_PORT | 8000 | Server port |

## API Endpoints

### POST /api/checks

Upload document package for verification.

**Request:**
- `files`: Multiple files (multipart/form-data)
- `program`: "federal" or "regional"

**Response:**
```json
{
  "check_id": "abc123",
  "status": "approved",
  "status_label": "Можно заявлять в банк",
  "reason": null,
  "issues": [],
  "documents": [
    {"name": "договор.pdf", "detected_type": "contract", "size_kb": 142}
  ],
  "extracted": {
    "contractor": "ООО «ТехАгро»",
    "amount": "1 250 000 ₽",
    "date": "01.03.2025",
    "subject": "Поставка минеральных удобрений"
  },
  "checked_at": "2025-03-15T14:32:00Z"
}
```

### GET /api/checks

List all verification checks.

### GET /api/checks/{id}

Get details of a specific check.

## Motivation

### Почему этот проект интересен?

Автоматизация рутинных процессов - это неотъемлемая часть прогресса, создавая подобные инструменты, мы делаем вклад в развитие человеческого потенциала. Проверка документов для получения льготных кредитов - это критически важный бизнес-процесс, который в настоящее время требует ручной обработки. Автоматизация этого процесса с помощью искусственного интеллекта сокращает время обработки с часов до секунд, исключает ошибки, вызванные человеческим фактором, и обеспечивает неизменное соблюдение требований программы.

### Роль в команде

Как бэкенд-разработчик, я бы сосредоточился на создании надежных и пригодных к тестированию API, которые станут фундаментом для систем обработки документов на базе искусственного интеллекта. Мой опыт работы с принципами чистой архитектуры в Школе21 и тщательным тестированием гарантирует надежность и удобство сопровождения системы.

### Сколько времени я готов уделять проекту 

Я готов вкладываться в проект столько, сколько он этого потребует, оптимальным для себя вижу 40 часов в неделю в виду серьезности и масштабности 
