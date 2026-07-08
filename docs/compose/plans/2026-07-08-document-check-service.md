# Document Check Service Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use compose:subagent (recommended) or compose:execute to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a FastAPI REST API service for verifying document packages for preferential loan programs, with PostgreSQL storage, history, and Docker deployment.

**Architecture:** Clean layering with pure business logic (classifier, validator, status_resolver) isolated from FastAPI/SQLAlchemy. Each service function is independently testable. PostgreSQL stores check history with JSONB for extracted data. Files stored locally in `uploads/`.

**Tech Stack:** Python 3.11, FastAPI, PostgreSQL, SQLAlchemy (sync), Alembic, Pydantic v2, pytest

## Global Constraints

- Python 3.11+
- All business logic functions must be pure (no DB/FastAPI dependencies) for unit testing
- POST /api/checks response format must exactly match the example in the assignment spec
- File storage: local `uploads/` directory with UUID-based filenames
- `extracted` data: stub response (hardcoded), documented in README as placeholder for AI module
- `check_in_progress` status: not used in sync implementation (documented in README)
- Document type detection: case-insensitive keyword matching in Russian and English
- Allowed file formats: PDF, DOCX, JPG, PNG only
- Max file size: 20 MB

---

## File Structure

```
document_check_service/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app, lifespan, CORS
│   ├── api/
│   │   ├── __init__.py
│   │   └── checks.py            # Router: POST/GET /api/checks
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── check.py             # Pydantic response/request models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── classifier.py        # Pure function: filename → type
│   │   ├── validator.py         # Pure function: docs + program → issues
│   │   ├── status_resolver.py   # Pure function: issues → status
│   │   └── check_service.py     # Orchestrator: files → saved check
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── check_repository.py  # CRUD for Check/Document/Issue
│   ├── models/
│   │   ├── __init__.py
│   │   └── check.py             # SQLAlchemy models
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py            # Settings from .env
│   │   └── storage.py           # Local file storage
│   └── db/
│       ├── __init__.py
│       └── session.py           # DB engine + session
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_classifier.py
│   ├── test_validator.py
│   ├── test_status_resolver.py
│   └── test_api.py
├── alembic/
│   ├── env.py
│   └── versions/
├── alembic.ini
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .env
└── README.md
```

---

### Task 0: Project Skeleton + Docker

**Files:**
- Create: `requirements.txt`
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `.env`
- Create: `.env.example`
- Create: `app/__init__.py`
- Create: `app/main.py`
- Create: `app/core/__init__.py`
- Create: `app/core/config.py`

- [ ] **Step 1: Create requirements.txt**

```
fastapi==0.115.0
uvicorn[standard]==0.30.0
sqlalchemy==2.0.35
alembic==1.13.0
psycopg2-binary==2.9.9
pydantic==2.9.0
pydantic-settings==2.5.0
python-multipart==0.0.12
pytest==8.3.0
httpx==0.27.0
```

- [ ] **Step 2: Create .env.example**

```
DATABASE_URL=postgresql://postgres:postgres@db:5432/doccheck
UPLOAD_DIR=./uploads
APP_HOST=0.0.0.0
APP_PORT=8000
```

- [ ] **Step 3: Create .env (copy of .env.example for local dev)**

```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/doccheck
UPLOAD_DIR=./uploads
APP_HOST=0.0.0.0
APP_PORT=8000
```

- [ ] **Step 4: Create app/core/config.py**

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/doccheck"
    UPLOAD_DIR: str = "./uploads"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    model_config = {"env_file": ".env"}


settings = Settings()
```

- [ ] **Step 5: Create app/main.py**

```python
from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(
        title="Document Check Service",
        description="AI-agent for document package verification",
        version="1.0.0",
    )

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()
```

- [ ] **Step 6: Create empty __init__.py files**

Create: `app/__init__.py`, `app/core/__init__.py`

- [ ] **Step 7: Create Dockerfile**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 8: Create docker-compose.yml**

```yaml
version: "3.8"

services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: doccheck
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://postgres:postgres@db:5432/doccheck
      UPLOAD_DIR: ./uploads
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - uploads:/app/uploads

volumes:
  pgdata:
  uploads:
```

- [ ] **Step 9: Verify skeleton runs**

Run: `docker compose up --build -d && sleep 3 && curl http://localhost:8000/health`
Expected: `{"status":"ok"}`

- [ ] **Step 10: Commit**

```bash
git add .
git commit -m "feat: project skeleton with Docker and FastAPI"
```

---

### Task 1: SQLAlchemy Models + Alembic

**Files:**
- Create: `app/db/__init__.py`
- Create: `app/db/session.py`
- Create: `app/models/__init__.py`
- Create: `app/models/check.py`
- Create: `alembic.ini`
- Create: `alembic/env.py`
- Create: `alembic/script.py.mako`
- Create: `alembic/versions/` (directory)

- [ ] **Step 1: Create app/db/session.py**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 2: Create app/models/check.py**

```python
import uuid
from datetime import datetime

from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Check(Base):
    __tablename__ = "checks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    program: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20))
    status_label: Mapped[str] = mapped_column(String(100))
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    document_count: Mapped[int] = mapped_column(Integer, default=0)
    extracted_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    documents: Mapped[list["Document"]] = relationship(back_populates="check", cascade="all, delete-orphan")
    issues: Mapped[list["CheckIssue"]] = relationship(back_populates="check", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    check_id: Mapped[str] = mapped_column(String(36), ForeignKey("checks.id"))
    filename: Mapped[str] = mapped_column(String(255))
    detected_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    file_path: Mapped[str] = mapped_column(String(500))
    size_kb: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    check: Mapped["Check"] = relationship(back_populates="documents")


class CheckIssue(Base):
    __tablename__ = "check_issues"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    check_id: Mapped[str] = mapped_column(String(36), ForeignKey("checks.id"))
    level: Mapped[str] = mapped_column(String(10))
    message: Mapped[str] = mapped_column(Text)

    check: Mapped["Check"] = relationship(back_populates="issues")
```

- [ ] **Step 3: Create app/models/__init__.py**

```python
from app.models.check import Check, Document, CheckIssue

__all__ = ["Check", "Document", "CheckIssue"]
```

- [ ] **Step 4: Create alembic.ini**

```ini
[alembic]
script_location = alembic
prepend_sys_path = .
sqlalchemy.url = postgresql://postgres:postgres@localhost:5432/doccheck

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

- [ ] **Step 5: Create alembic/env.py**

```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

from app.db.session import Base
from app.models import Check, Document, CheckIssue  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 6: Create alembic/script.py.mako**

```mako
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
```

- [ ] **Step 7: Create initial migration**

Run: `alembic revision --autogenerate -m "initial tables"`
Expected: Creates `alembic/versions/xxxx_initial_tables.py`

- [ ] **Step 8: Verify migration applies**

Run: `docker compose exec db psql -U postgres -d doccheck -c "\dt"`
Run: `alembic upgrade head`
Expected: Tables `checks`, `documents`, `check_issues` exist

- [ ] **Step 9: Commit**

```bash
git add .
git commit -m "feat: SQLAlchemy models and Alembic migration"
```

---

### Task 2: Classifier — Pure Function + Unit Tests

**Files:**
- Create: `app/services/__init__.py`
- Create: `app/services/classifier.py`
- Create: `tests/__init__.py`
- Create: `tests/test_classifier.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_classifier.py`:

```python
import pytest
from app.services.classifier import classify_document


class TestClassifyDocument:
    def test_contract_russian(self):
        assert classify_document("Договор_47.pdf") == "contract"

    def test_contract_english(self):
        assert classify_document("contract_agreement.docx") == "contract"

    def test_specification_russian(self):
        assert classify_document("спецификация_к_договору.pdf") == "specification"

    def test_specification_english(self):
        assert classify_document("specification_v2.docx") == "specification"

    def test_invoice_russian(self):
        assert classify_document("счёт_на_оплату.pdf") == "invoice"

    def test_invoice_transliteration(self):
        assert classify_document("schet_001.pdf") == "invoice"

    def test_act_russian(self):
        assert classify_document("акт_приемки.jpg") == "act"

    def test_act_upd(self):
        assert classify_document("УПД_акт.pdf") == "act"

    def test_unknown_file(self):
        assert classify_document("scan_0041.jpg") is None

    def test_case_insensitive(self):
        assert classify_document("ДОГОВОР_01.PDF") == "contract"

    def test_empty_filename(self):
        assert classify_document("") is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_classifier.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.classifier'`

- [ ] **Step 3: Implement classifier**

Create `app/services/classifier.py`:

```python
from pathlib import Path


TYPE_KEYWORDS: dict[str, list[str]] = {
    "contract": ["договор", "contract", "дог", "dog"],
    "specification": ["спецификация", "specification", "спец", "spec"],
    "invoice": ["счёт", "счет", "счёт-фактура", "invoice", "сч", "schet"],
    "act": ["акт", "акт_приемки", "act", "upd", "упд"],
}


def classify_document(filename: str) -> str | None:
    stem = Path(filename).stem.lower()
    if not stem:
        return None
    for doc_type, keywords in TYPE_KEYWORDS.items():
        for kw in keywords:
            if kw in stem:
                return doc_type
    return None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_classifier.py -v`
Expected: 11 passed

- [ ] **Step 5: Commit**

```bash
git add app/services/classifier.py tests/test_classifier.py
git commit -m "feat: document classifier with unit tests"
```

---

### Task 3: Validator — Pure Function + Unit Tests

**Files:**
- Create: `app/services/validator.py`
- Create: `tests/test_validator.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_validator.py`:

```python
import pytest
from app.services.validator import validate_package, Issue


class TestValidatePackage:
    def test_federal_complete(self):
        docs = [("contract.pdf", "contract"), ("spec.pdf", "specification"), ("invoice.pdf", "invoice"), ("act.pdf", "act")]
        issues = validate_package(docs, "federal")
        assert len([i for i in issues if i.level == "error"]) == 0

    def test_federal_missing_specification(self):
        docs = [("contract.pdf", "contract"), ("invoice.pdf", "invoice"), ("act.pdf", "act")]
        issues = validate_package(docs, "federal")
        error_msgs = [i.message for i in issues if i.level == "error"]
        assert any("спецификация" in msg.lower() for msg in error_msgs)

    def test_regional_complete(self):
        docs = [("contract.pdf", "contract"), ("invoice.pdf", "invoice"), ("act.pdf", "act")]
        issues = validate_package(docs, "regional")
        assert len([i for i in issues if i.level == "error"]) == 0

    def test_regional_missing_act(self):
        docs = [("contract.pdf", "contract"), ("invoice.pdf", "invoice")]
        issues = validate_package(docs, "regional")
        error_msgs = [i.message for i in issues if i.level == "error"]
        assert any("акт" in msg.lower() for msg in error_msgs)

    def test_unknown_format_warning(self):
        docs = [("report.exe", None)]
        issues = validate_package(docs, "federal")
        warnings = [i.message for i in issues if i.level == "warning"]
        assert any("формат" in msg.lower() for msg in warnings)

    def test_oversized_file_warning(self):
        docs = [("big.pdf", "contract", 25000)]
        issues = validate_package(docs, "federal")
        warnings = [i.message for i in issues if i.level == "warning"]
        assert any("20 мб" in msg.lower() or "20 mb" in msg.lower() for msg in warnings)

    def test_unrecognized_filename_warning(self):
        docs = [("random_name.jpg", None)]
        issues = validate_package(docs, "federal")
        warnings = [i.message for i in issues if i.level == "warning"]
        assert any("нераспознан" in msg.lower() or "определить тип" in msg.lower() for msg in warnings)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_validator.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement validator**

Create `app/services/validator.py`:

```python
from dataclasses import dataclass

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".jpg", ".png"}
MAX_SIZE_KB = 20 * 1024  # 20 MB

REQUIRED_TYPES = {
    "federal": {"contract", "specification", "invoice", "act"},
    "regional": {"contract", "invoice", "act"},
}


@dataclass
class Issue:
    level: str  # "error" or "warning"
    message: str


def validate_package(
    documents: list[tuple[str, str | None, int | None]],
    program: str,
) -> list[Issue]:
    issues: list[Issue] = []
    detected_types: set[str] = set()

    for filename, detected_type, *rest in documents:
        size_kb = rest[0] if rest else None

        # Check file extension
        ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in ALLOWED_EXTENSIONS:
            issues.append(Issue(level="warning", message=f"Недопустимый формат файла: «{filename}»"))

        # Check file size
        if size_kb and size_kb > MAX_SIZE_KB:
            issues.append(Issue(level="warning", message=f"Файл «{filename}» превышает 20 МБ"))

        # Check unrecognized type
        if detected_type is None:
            issues.append(Issue(level="warning", message=f"Не удалось определить тип документа: «{filename}»"))
        else:
            detected_types.add(detected_type)

    # Check required types
    required = REQUIRED_TYPES.get(program, set())
    missing = required - detected_types
    type_names = {
        "contract": "договор",
        "specification": "спецификация",
        "invoice": "счёт",
        "act": "акт",
    }
    for t in sorted(missing):
        issues.append(Issue(level="error", message=f"Отсутствует обязательный документ: {type_names.get(t, t)}"))

    return issues
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_validator.py -v`
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add app/services/validator.py tests/test_validator.py
git commit -m "feat: package validator with unit tests"
```

---

### Task 4: Status Resolver — Pure Function + Unit Tests

**Files:**
- Create: `app/services/status_resolver.py`
- Create: `tests/test_status_resolver.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_status_resolver.py`:

```python
import pytest
from app.services.status_resolver import resolve_status, StatusResult
from app.services.validator import Issue


class TestResolveStatus:
    def test_no_issues_approved(self):
        result = resolve_status([])
        assert result.status == "approved"
        assert result.status_label == "Нельзя заявлять в банк" or "approved" in result.status

    def test_has_errors_rejected(self):
        issues = [Issue(level="error", message="Missing contract")]
        result = resolve_status(issues)
        assert result.status == "rejected"

    def test_only_warnings_approved(self):
        issues = [Issue(level="warning", message="Unknown file type")]
        result = resolve_status(issues)
        assert result.status == "approved"

    def test_mixed_errors_and_warnings_rejected(self):
        issues = [
            Issue(level="error", message="Missing specification"),
            Issue(level="warning", message="Large file"),
        ]
        result = resolve_status(issues)
        assert result.status == "rejected"

    def test_empty_list_approved(self):
        result = resolve_status([])
        assert result.status == "approved"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_status_resolver.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement status resolver**

Create `app/services/status_resolver.py`:

```python
from dataclasses import dataclass

from app.services.validator import Issue


STATUS_APPROVED = "approved"
STATUS_REJECTED = "rejected"
STATUS_IN_PROGRESS = "check_in_progress"


@dataclass
class StatusResult:
    status: str
    status_label: str
    reason: str | None


def resolve_status(issues: list[Issue]) -> StatusResult:
    has_errors = any(i.level == "error" for i in issues)

    if has_errors:
        error_messages = [i.message for i in issues if i.level == "error"]
        reason = "; ".join(error_messages)
        return StatusResult(
            status=STATUS_REJECTED,
            status_label="Нельзя заявлять в банк",
            reason=reason,
        )

    return StatusResult(
        status=STATUS_APPROVED,
        status_label="Можно заявлять в банк",
        reason=None,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_status_resolver.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add app/services/status_resolver.py tests/test_status_resolver.py
git commit -m "feat: status resolver with unit tests"
```

---

### Task 5: Storage + Check Service Orchestrator

**Files:**
- Create: `app/core/storage.py`
- Create: `app/services/check_service.py`
- Create: `app/repositories/__init__.py`
- Create: `app/repositories/check_repository.py`

- [ ] **Step 1: Create storage.py**

```python
import uuid
from pathlib import Path

from app.core.config import settings


def save_files(files: list[tuple[str, bytes]]) -> list[tuple[str, str, int]]:
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    saved = []
    for filename, content in files:
        ext = Path(filename).suffix
        unique_name = f"{uuid.uuid4()}{ext}"
        file_path = upload_dir / unique_name
        file_path.write_bytes(content)
        size_kb = len(content) // 1024
        saved.append((filename, str(file_path), size_kb))
    return saved
```

- [ ] **Step 2: Create check_repository.py**

```python
from sqlalchemy.orm import Session

from app.models import Check, Document, CheckIssue


def create_check(
    db: Session,
    program: str,
    status: str,
    status_label: str,
    reason: str | None,
    document_count: int,
    extracted_data: dict | None,
    documents: list[dict],
    issues: list[dict],
) -> Check:
    check = Check(
        program=program,
        status=status,
        status_label=status_label,
        reason=reason,
        document_count=document_count,
        extracted_data=extracted_data,
    )
    db.add(check)
    db.flush()

    for doc in documents:
        db.add(Document(check_id=check.id, **doc))

    for issue in issues:
        db.add(CheckIssue(check_id=check.id, **issue))

    db.commit()
    db.refresh(check)
    return check


def get_check(db: Session, check_id: str) -> Check | None:
    return db.query(Check).filter(Check.id == check_id).first()


def list_checks(db: Session) -> list[Check]:
    return db.query(Check).order_by(Check.created_at.desc()).all()
```

- [ ] **Step 3: Create check_service.py**

```python
from sqlalchemy.orm import Session

from app.core.storage import save_files
from app.repositories.check_repository import create_check
from app.services.classifier import classify_document
from app.services.validator import validate_package
from app.services.status_resolver import resolve_status


def process_check(
    db: Session,
    files: list[tuple[str, bytes]],
    program: str,
) -> dict:
    # 1. Save files to disk
    saved_files = save_files(files)

    # 2. Classify each document
    doc_infos = []
    for original_name, file_path, size_kb in saved_files:
        detected_type = classify_document(original_name)
        doc_infos.append({
            "filename": original_name,
            "detected_type": detected_type,
            "file_path": file_path,
            "size_kb": size_kb,
        })

    # 3. Validate package completeness
    validation_input = [
        (d["filename"], d["detected_type"], d["size_kb"])
        for d in doc_infos
    ]
    issues = validate_package(validation_input, program)

    # 4. Resolve status
    status_result = resolve_status(issues)

    # 5. Prepare extracted data (stub)
    extracted_data = {
        "contractor": "ООО «ТехАгро»",
        "amount": "1 250 000 ₽",
        "date": "01.03.2025",
        "subject": "Поставка минеральных удобрений",
    }

    # 6. Save to database
    check = create_check(
        db=db,
        program=program,
        status=status_result.status,
        status_label=status_result.status_label,
        reason=status_result.reason,
        document_count=len(doc_infos),
        extracted_data=extracted_data,
        documents=doc_infos,
        issues=[{"level": i.level, "message": i.message} for i in issues],
    )

    return {
        "check_id": check.id,
        "status": check.status,
        "status_label": check.status_label,
        "reason": check.reason,
        "issues": [{"level": i.level, "message": i.message} for i in issues],
        "documents": [
            {"name": d["filename"], "detected_type": d["detected_type"], "size_kb": d["size_kb"]}
            for d in doc_infos
        ],
        "extracted": extracted_data,
        "checked_at": check.created_at.isoformat() + "Z",
    }
```

- [ ] **Step 4: Commit**

```bash
git add app/core/storage.py app/services/check_service.py app/repositories/
git commit -m "feat: storage, repository, and check service orchestrator"
```

---

### Task 6: Pydantic Schemas + API Endpoints

**Files:**
- Create: `app/schemas/__init__.py`
- Create: `app/schemas/check.py`
- Create: `app/api/__init__.py`
- Create: `app/api/checks.py`
- Modify: `app/main.py`

- [ ] **Step 1: Create Pydantic schemas**

Create `app/schemas/check.py`:

```python
from pydantic import BaseModel


class IssueSchema(BaseModel):
    level: str
    message: str


class DocumentSchema(BaseModel):
    name: str
    detected_type: str | None
    size_kb: int


class ExtractedData(BaseModel):
    contractor: str | None = None
    amount: str | None = None
    date: str | None = None
    subject: str | None = None


class CheckResponse(BaseModel):
    check_id: str
    status: str
    status_label: str
    reason: str | None = None
    issues: list[IssueSchema]
    documents: list[DocumentSchema]
    extracted: ExtractedData | None = None
    checked_at: str


class CheckListItem(BaseModel):
    id: str
    created_at: str
    program: str
    status: str
    document_count: int
```

- [ ] **Step 2: Create API router**

Create `app/api/checks.py`:

```python
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.check_repository import get_check, list_checks
from app.schemas.check import CheckResponse, CheckListItem
from app.services.check_service import process_check

router = APIRouter(prefix="/api/checks", tags=["checks"])


@router.post("", response_model=CheckResponse)
async def create_check(
    files: list[UploadFile] = File(...),
    program: str = Form(...),
    db: Session = Depends(get_db),
):
    if program not in ("federal", "regional"):
        raise HTTPException(status_code=400, detail="Program must be 'federal' or 'regional'")

    if not files:
        raise HTTPException(status_code=400, detail="At least one file is required")

    file_data = []
    for f in files:
        content = await f.read()
        file_data.append((f.filename, content))

    result = process_check(db, file_data, program)
    return result


@router.get("", response_model=list[CheckListItem])
def list_all_checks(db: Session = Depends(get_db)):
    checks = list_checks(db)
    return [
        CheckListItem(
            id=c.id,
            created_at=c.created_at.isoformat() + "Z",
            program=c.program,
            status=c.status,
            document_count=c.document_count,
        )
        for c in checks
    ]


@router.get("/{check_id}", response_model=CheckResponse)
def get_check_by_id(check_id: str, db: Session = Depends(get_db)):
    check = get_check(db, check_id)
    if not check:
        raise HTTPException(status_code=404, detail="Check not found")

    issues = [{"level": i.level, "message": i.message} for i in check.issues]
    documents = [
        {"name": d.filename, "detected_type": d.detected_type, "size_kb": d.size_kb}
        for d in check.documents
    ]

    return CheckResponse(
        check_id=check.id,
        status=check.status,
        status_label=check.status_label,
        reason=check.reason,
        issues=issues,
        documents=documents,
        extracted=check.extracted_data,
        checked_at=check.created_at.isoformat() + "Z",
    )
```

- [ ] **Step 3: Register router in main.py**

Modify `app/main.py`:

```python
from fastapi import FastAPI

from app.api.checks import router as checks_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Document Check Service",
        description="AI-agent for document package verification",
        version="1.0.0",
    )

    app.include_router(checks_router)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()
```

- [ ] **Step 4: Verify API works**

Run: `docker compose up --build -d && sleep 3 && curl http://localhost:8000/health`
Expected: `{"status":"ok"}`

Run: `curl http://localhost:8000/docs`
Expected: Swagger UI loads

- [ ] **Step 5: Commit**

```bash
git add app/schemas/ app/api/ app/main.py
git commit -m "feat: API endpoints with Pydantic schemas"
```

---

### Task 7: Integration Tests

**Files:**
- Create: `tests/conftest.py`
- Create: `tests/test_api.py`

- [ ] **Step 1: Create conftest.py**

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.session import Base, get_db
from app.main import create_app


@pytest.fixture(scope="session")
def engine():
    engine = create_engine("sqlite:///./test.db")
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(engine):
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    app = create_app()

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
```

- [ ] **Step 2: Write integration tests**

Create `tests/test_api.py`:

```python
import io
import pytest


class TestPostChecks:
    def test_create_check_success(self, client):
        files = [
            ("files", ("договор.pdf", b"fake pdf content", "application/pdf")),
            ("files", ("спецификация.pdf", b"fake pdf content", "application/pdf")),
            ("files", ("счёт.pdf", b"fake pdf content", "application/pdf")),
            ("files", ("акт.pdf", b"fake pdf content", "application/pdf")),
        ]
        response = client.post("/api/checks", files=files, data={"program": "federal"})
        assert response.status_code == 200
        data = response.json()
        assert "check_id" in data
        assert data["status"] == "approved"
        assert len(data["documents"]) == 4

    def test_create_check_empty_files(self, client):
        response = client.post("/api/checks", files=[], data={"program": "federal"})
        assert response.status_code == 422

    def test_create_check_invalid_program(self, client):
        files = [("files", ("test.pdf", b"content", "application/pdf"))]
        response = client.post("/api/checks", files=files, data={"program": "invalid"})
        assert response.status_code == 400


class TestGetChecks:
    def test_list_checks(self, client):
        response = client.get("/api/checks")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_check_not_found(self, client):
        response = client.get("/api/checks/nonexistent-id")
        assert response.status_code == 404

    def test_get_check_by_id(self, client):
        # First create a check
        files = [("files", ("договор.pdf", b"content", "application/pdf"))]
        create_resp = client.post("/api/checks", files=files, data={"program": "regional"})
        check_id = create_resp.json()["check_id"]

        response = client.get(f"/api/checks/{check_id}")
        assert response.status_code == 200
        assert response.json()["check_id"] == check_id
```

- [ ] **Step 3: Run all tests**

Run: `pytest tests/ -v`
Expected: All tests pass (classifier: 11, validator: 7, status_resolver: 5, api: 6 = 29 total)

- [ ] **Step 4: Commit**

```bash
git add tests/
git commit -m "feat: integration tests for API endpoints"
```

---

### Task 8: Docker Compose Verification + README

**Files:**
- Modify: `docker-compose.yml` (ensure health checks work)
- Create: `README.md`

- [ ] **Step 1: Full Docker verification**

Run:
```bash
docker compose down -v
docker compose up --build -d
sleep 5
curl http://localhost:8000/health
curl http://localhost:8000/api/checks
```
Expected: All endpoints respond correctly

- [ ] **Step 2: Test POST via curl**

Run:
```bash
curl -X POST http://localhost:8000/api/checks \
  -F "files=@test_file.pdf" \
  -F "program=federal"
```
(With a real or dummy PDF file)

Expected: 200 with JSON response matching spec format

- [ ] **Step 3: Create README.md**

Create `README.md` with all required sections:

```markdown
# Document Check Service

AI-agent for automated verification of document packages for preferential loan programs.

## Quick Start

### With Docker (recommended)

```bash
docker compose up --build
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

### Why this project?

Document verification for preferential loans is a critical business process that currently requires manual effort. Automating this with AI reduces processing time from hours to seconds, eliminates human error, and ensures consistent compliance with program requirements.

### Role in the team

As a backend developer, I would focus on building robust, testable APIs that serve as the foundation for AI-powered document processing. My strength in clean architecture and thorough testing ensures the system is reliable and maintainable.

### Time commitment

I can dedicate 15-20 hours per week for 2-3 months to this project.
```

- [ ] **Step 4: Final full test run**

Run: `pytest tests/ -v --tb=short`
Expected: All 29 tests pass

- [ ] **Step 5: Commit**

```bash
git add README.md
git commit -m "docs: comprehensive README with setup, architecture, and API docs"
```

---

### Task 9: Final Verification Checklist

- [ ] `docker compose up --build` — both services start successfully
- [ ] `curl http://localhost:8000/health` returns `{"status":"ok"}`
- [ ] Swagger UI loads at `http://localhost:8000/docs`
- [ ] POST /api/checks with test files returns correct JSON format
- [ ] GET /api/checks returns list of checks
- [ ] GET /api/checks/{id} returns full check details
- [ ] GET /api/checks/{nonexistent} returns 404
- [ ] POST with empty files returns 422
- [ ] POST with invalid program returns 400
- [ ] `pytest tests/` — all tests pass
- [ ] README contains: quick start, test instructions, technologies, architecture, env vars
- [ ] .env.example exists with all variables
- [ ] Response format matches assignment spec exactly (check_id, status, status_label, reason, issues, documents, extracted, checked_at)
