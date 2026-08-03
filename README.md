# Enterprise Expense & Procurement Workflow Platform - Phase 1 Foundation

This repository contains the production-ready project foundation and skeleton for the Enterprise Expense & Procurement Workflow Platform. The codebase is organized around Clean Architecture, Domain Driven Design (DDD) principles, and SOLID design patterns.

---

## 1. Project Directory Structure

All application source code resides under the `src/` directory. Subfolders are organized by domain bounded contexts or structural middleware/database utilities:

```text
project/ (workspace root)
├── src/
│   ├── api/              # API router registrations and system probes
│   ├── auth/             # Authentication & Authorization context (placeholder)
│   ├── employees/        # Employees bounded context (placeholder)
│   ├── expenses/         # Expenses bounded context (placeholder)
│   ├── procurement/      # Procurement bounded context (placeholder)
│   ├── vendors/          # Vendors bounded context (placeholder)
│   ├── invoices/         # Invoices bounded context (placeholder)
│   ├── assets/           # Assets bounded context (placeholder)
│   ├── approval/         # Approvals bounded context (placeholder)
│   ├── policy/           # Policies bounded context (placeholder)
│   ├── analytics/        # Analytics bounded context (placeholder)
│   ├── audit/            # Audit logging context (placeholder)
│   ├── admin/            # Administrative actions context (placeholder)
│   ├── notifications/    # Message and mail delivery systems (placeholder)
│   ├── storage/          # Document storage service wrappers (S3/Supabase) (placeholder)
│   ├── database/         # Session setup, async engines, and base model declarations
│   ├── models/           # Shared database models
│   ├── repositories/     # Repositories folder (contains generic BaseRepository)
│   ├── services/         # Shared service interfaces
│   ├── schemas/          # Shared validation models (Pydantic)
│   ├── middleware/       # Custom ASGI middlewares (Request ID, Logging, Security)
│   ├── core/             # Application config, logger initialization, constants
│   ├── utils/            # Shared helper functions
│   └── main.py           # FastAPI Application Entrypoint
├── alembic/              # Database migration configurations and version history
├── tests/                # Unit, integration, and startup testing suites
├── docs/                 # Documentation folder
├── scripts/              # Setup and administration utility scripts
├── docker/               # Docker configurations
├── .env.example          # Environment variables template
├── .gitignore            # Git exclusion patterns
├── README.md             # Project developer handbook
├── requirements.txt      # Python dependencies
├── pyproject.toml        # Tooling configuration (pytest, black, ruff)
├── docker-compose.yml    # Development multi-container orchestration
└── Dockerfile            # Multi-stage production container build file
```

---

## 2. Technology Stack & Configuration

- **FastAPI**: Serving as the ASGI application framework.
- **SQLAlchemy 2.0 & asyncpg**: Direct asynchronous database interaction.
- **Pydantic v2**: Environment variables loading, validation, and request/response model definitions.
- **Alembic**: Database schema migrations configured asynchronously.
- **Supabase PostgreSQL**: Configured via connection pooling over the PostgreSQL protocol.

### Required Environment Variables

Create a `.env` file in the project root following the structure in `.env.example`:

| Variable | Description |
| :--- | :--- |
| `ENVIRONMENT` | One of `development`, `testing`, `staging`, `production`. |
| `LOG_LEVEL` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`). |
| `DATABASE_URL` | Async DSN connection string: `postgresql+asyncpg://[user]:[password]@[host]:5432/[db]`. |
| `SUPABASE_URL` | Supabase endpoint URL. |
| `SUPABASE_KEY` | Supabase anonymous API key. |
| `JWT_SECRET` | Secret key used for signing JWT access tokens. |
| `AWS_REGION` | Core AWS region (e.g. `us-east-1`). |
| `AWS_ACCESS_KEY_ID` | AWS service credential access key. |
| `AWS_SECRET_ACCESS_KEY` | AWS service credential secret key. |
| `TEXTRACT_REGION` | AWS Region designated for AWS Textract OCR operations. |

---

## 3. Logging & Custom Middlewares

### Middlewares Flow

The application executes middlewares in a chain structure to guarantee request isolation and security:

```
Request ────> CORS / Trusted Host ────> ExceptionMiddleware ────> LoggingMiddleware ────> RequestIdMiddleware ────> SecurityHeaders ────> Endpoint
                                                                                                                                      │
Response <──── CORS / Trusted Host <──── ExceptionMiddleware <──── LoggingMiddleware <──── RequestIdMiddleware <──── SecurityHeaders <────┘
```

1. **Exception Middleware**: Catches unhandled errors, logs a detailed traceback along with the active Request ID, and yields a standardized `500 Internal Server Error` response.
2. **Logging Middleware**: Logs incoming HTTP details and measures execution time, reporting to both console and a rotating log file.
3. **Request ID Middleware**: Generates or extracts `X-Request-ID` and sets it in context-local thread-safe storage (`contextvars`).
4. **Security Headers Middleware**: Injects `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Strict-Transport-Security`, and restrictive `Content-Security-Policy`.
5. **GZip Compression Middleware**: Dynamically compresses payload sizes exceeding 1000 bytes.

---

## 4. Run & Test Instructions

### Running Locally

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
2. **Run FastAPI Server**:
   ```bash
   uvicorn src.main:app --reload
   ```
3. **Access Interactive API Docs (Swagger UI)**:
   - Navigate to `http://localhost:8000/docs` in your browser.

### Running with Docker

Start both the FastAPI application and the local PostgreSQL backend:
```bash
docker compose up --build -d
```
Verify the container liveness status:
```bash
docker compose ps
```

### Running Automated Tests

Run the test suite using pytest:
```bash
python -m pytest -v
```
All tests check endpoints, config setups, logging output, and mocked database connection probes.
