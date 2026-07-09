# Document Check Service

AI-агент проверки комплектности документальных пакетов для программ льготного кредитования.

## Быстрый старт

### Docker (рекомендуется)

```bash
docker compose up --build
```

После запуска примените миграции:

```bash
docker compose exec app alembic upgrade head
```

Сервис: http://localhost:8000
Swagger UI: http://localhost:8000/docs

### Локальная разработка

```bash
python -m venv venv
source venv/bin/activate

pip install -r requirements.txt

createdb doccheck
alembic upgrade head

uvicorn app.main:app --reload
```

## Тестирование

```bash
# Unit-тесты (без БД)
pytest tests/test_classifier.py tests/test_validator.py tests/test_status_resolver.py -v

# Интеграционные тесты (требуется запущенная БД)
pytest tests/test_api.py -v

# Все тесты
pytest tests/ -v
```

## Стек технологий

- **FastAPI** — async-фреймворк с автогенерируемой OpenAPI-спецификацией
- **PostgreSQL** — реляционная БД для хранения истории проверок
- **SQLAlchemy 2.0** — ORM с поддержкой Mapped-стиля
- **Alembic** — управление database migrations
- **Pydantic v2** — data validation и сериализация
- **Docker Compose** — контейнеризация и оркестрация сервисов
- **JWT + bcrypt** — аутентификация: хеширование паролей через bcrypt, JWT-токены, FastAPI `OAuth2PasswordBearer` dependency

## Архитектура

```
app/
├── api/              # HTTP-слой (FastAPI routers)
│   ├── auth.py       # Регистрация, логин
│   └── checks.py     # CRUD-операции с проверками
├── schemas/          # Pydantic-схемы (request/response models)
├── services/         # Бизнес-логика (чистые функции, без зависимости от Фреймворка)
│   ├── auth.py            # JWT, хеширование паролей, OAuth2 dependency
│   ├── classifier.py      # Определение типа документа по имени файла
│   ├── validator.py       # Валидация комплектности пакета
│   ├── status_resolver.py # Определение итогового статуса
│   └── check_service.py   # Оркестрация всего процесса
├── repositories/     # Database operations (CRUD)
├── models/           # SQLAlchemy ORM-модели
├── core/             # Конфигурация и утилиты
└── db/               # Управление сессиями БД
```

### Ключевые решения

- **Чистая бизнес-логика**: `classifier.py`, `validator.py`, `status_resolver.py` — чистые функции без зависимостей от FastAPI или SQLAlchemy, что обеспечивает простоту unit-тестирования
- **Stub извлечения данных**: интеграция с AI-модулем имитирована; реальное извлечение потребует отдельного AI-сервиса
- **Локальное хранение файлов**: файлы сохраняются в `uploads/` с UUID-именами для исключения коллизий
- **Аутентификация**: JWT-токены с time-to-live, bcrypt для хеширования паролей, FastAPI `Depends()` для injection authentication dependency

### Безопасность JWT-реализации

- **SECRET_KEY** — обязательная переменная окружения, без неё сервис не стартует
- **iat + exp** — каждый токен содержит время создания и время истечения
- **algorithms=["HS256"]** — явный список алгоритмов при decode, защита от атаки `alg: none`
- **30 минут TTL** — компромисс между удобством и безопасностью (без refresh-токена)
- **Единое сообщение ошибки** при логине — не раскрывает, существует ли пользователь

## Переменные окружения

| Переменная | Значение по умолчанию | Описание |
|------------|----------------------|----------|
| DATABASE_URL | postgresql://postgres:postgres@localhost:5432/doccheck | Строка подключения к PostgreSQL |
| UPLOAD_DIR | ./uploads | Директория для хранения загруженных файлов |
| APP_HOST | 0.0.0.0 | Хост сервера |
| APP_PORT | 8000 | Порт сервера |
| JWT_SECRET | *(обязательно)* | Секретный ключ для подписи JWT (минимум 32 байта) |
| JWT_EXPIRE_MINUTES | 30 | Время жизни токена в минутах |

## API Endpoints

### POST /api/auth/register

Регистрация нового пользователя. Возвращает JWT-токен.

**Request:**
```json
{"username": "admin", "password": "admin123"}
```

**Response:**
```json
{"access_token": "eyJ...", "token_type": "bearer"}
```

### POST /api/auth/login

Авторизация. Возвращает JWT-токен.

**Request:**
```json
{"username": "admin", "password": "admin123"}
```

### POST /api/checks

**Требуется:** `Authorization: Bearer <token>`

Загрузка пакета документов для проверки.

**Request (multipart/form-data):**
- `files` — файлы документов (PDF, DOCX, JPG, PNG)
- `program` — `federal` или `regional`

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

Получение списка всех выполненных проверок.

### GET /api/checks/{id}

Получение детальной информации о проверке по ID.

## Motivation

### Почему этот проект интересен?

Автоматизация рутинных процессов - это неотъемлемая часть прогресса, создавая подобные инструменты, мы делаем вклад в развитие человеческого потенциала. Проверка документов для получения льготных кредитов - это критически важный бизнес-процесс, который в настоящее время требует ручной обработки. Автоматизация этого процесса с помощью искусственного интеллекта сокращает время обработки с часов до секунд, исключает ошибки, вызванные человеческим фактором, и обеспечивает неизменное соблюдение требований программы.

### Роль в команде

Как бэкенд-разработчик, я бы сосредоточился на создании надежных и пригодных к тестированию API, которые станут фундаментом для систем обработки документов на базе искусственного интеллекта. Мой опыт работы с принципами чистой архитектуры в Школе21 и тщательным тестированием гарантирует надежность и удобство сопровождения системы.

### Сколько времени я готов уделять проекту 

Я готов вкладываться в проект столько, сколько он этого потребует, оптимальным для себя вижу 40 часов в неделю в виду серьезности и масштабности 
