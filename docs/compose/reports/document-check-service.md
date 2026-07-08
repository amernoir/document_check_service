---
feature: document-check-service
status: delivered
specs:
  - docs/compose/plans/2026-07-08-document-check-service.md
plans:
  - .mimocode/plans/1783518284032-sunny-garden.md
branch: develop
commits: 4f70abf..f4ecbca
---

# Document Check Service — Final Report

## What Was Built

A REST API service for verifying document packages for preferential loan programs. The service accepts uploaded document files (PDF, DOCX, JPG, PNG), classifies them by type (contract, specification, invoice, act), validates package completeness based on program type (federal/regional), and returns verification results with appropriate status codes.

The system stores all verification history in PostgreSQL, allowing users to review past checks and their outcomes. Files are stored locally with UUID-based names to prevent conflicts.

## Architecture

### Directory Structure

```
app/
├── api/checks.py          # FastAPI router (POST/GET endpoints)
├── schemas/check.py       # Pydantic response models
├── services/
│   ├── classifier.py      # Document type detection (pure function)
│   ├── validator.py       # Package completeness validation (pure function)
│   ├── status_resolver.py # Status determination (pure function)
│   └── check_service.py   # Orchestration layer
├── repositories/check_repository.py  # SQLAlchemy CRUD
├── models/check.py        # SQLAlchemy models (Check, Document, CheckIssue)
├── core/config.py         # Settings from .env
├── core/storage.py        # Local file storage
└── db/session.py          # Database session management
```

### Key Interfaces

- **classifier.classify_document(filename) → str | None**: Maps filename to document type using case-insensitive keyword matching
- **validator.validate_package(documents, program) → list[Issue]**: Validates package completeness and file properties
- **status_resolver.resolve_status(issues) → StatusResult**: Determines approved/rejected status based on issues
- **check_service.process_check(db, files, program) → dict**: Orchestrates the full verification pipeline

### Data Flow

```
POST /api/checks (multipart + program)
  → check_service.process_check()
    → storage.save_files() (save to uploads/)
    → classifier.classify_document() (per file)
    → validator.validate_package()
    → status_resolver.resolve_status()
    → check_repository.create() (persist to DB)
  → Return CheckResponse JSON
```

### Design Decisions

- **Pure business logic**: `classifier.py`, `validator.py`, `status_resolver.py` have zero dependencies on FastAPI or SQLAlchemy, making them trivially unit-testable
- **Keyword-based classification**: Uses longest-match-first algorithm to avoid partial matches (e.g., "спецификация" matches before "договор")
- **Stub extracted data**: Returns hardcoded contractor/amount/date/subject since real AI extraction would require additional services
- **Local file storage**: Simple `uploads/` directory with UUID filenames; suitable for test assignment scope

## Usage

### Start with Docker

```bash
docker compose up --build
docker compose exec app alembic upgrade head
```

Service: http://localhost:8000
Swagger: http://localhost:8000/docs

### API Examples

```bash
# Create check
curl -X POST http://localhost:8000/api/checks \
  -F "files=@договор.pdf" \
  -F "files=@спецификация.pdf" \
  -F "files=@счёт.pdf" \
  -F "files=@акт.pdf" \
  -F "program=federal"

# List checks
curl http://localhost:8000/api/checks

# Get check by ID
curl http://localhost:8000/api/checks/{check_id}
```

## Verification

### Test Summary

- **29 tests total** (all passing)
  - `test_classifier.py`: 11 tests (document type detection)
  - `test_validator.py`: 7 tests (package validation)
  - `test_status_resolver.py`: 5 tests (status determination)
  - `test_api.py`: 6 tests (integration tests)

### Manual Verification

- `docker compose up --build` starts successfully
- Health endpoint returns `{"status":"ok"}`
- POST /api/checks returns correct JSON format matching assignment spec
- GET /api/checks returns list of checks
- GET /api/checks/{id} returns full check details
- 404 returned for nonexistent check IDs
- 422 returned for invalid requests

## Journey Log

- [lesson] Port 5432 was already in use; switched to 5433 in docker-compose.yml
- [lesson] Alembic migrations must be generated inside Docker container to have correct DATABASE_URL
- [lesson] Keyword matching requires longest-match-first to avoid partial matches (e.g., "дог" matching inside "спецификация")

## Source Materials

| File | Role | Notes |
|------|------|-------|
| `.mimocode/plans/1783518284032-sunny-garden.md` | High-level plan | Architecture and task decomposition |
| `docs/compose/plans/2026-07-08-document-check-service.md` | Implementation plan | Detailed step-by-step guide |
