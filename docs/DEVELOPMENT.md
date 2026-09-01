# Zenglow — Development Guide

## Prerequisites

| Tool | Version | Install |
|---|---|---|
| Python | 3.11+ | [python.org](https://python.org) |
| Node.js | 20+ | [nodejs.org](https://nodejs.org) |
| pnpm | 8+ | `npm install -g pnpm` |
| Docker | 24+ | [docker.com](https://docker.com) |
| Git | 2.40+ | [git-scm.com](https://git-scm.com) |

---

## Quick Start (Docker — Recommended)

```bash
# 1. Clone
git clone https://github.com/your-org/zenglow.git
cd zenglow

# 2. Environment
cp .env.example .env
# Defaults work for local Docker development — no edits needed

# 3. Start infrastructure + backend
docker compose up -d postgres redis backend celery-worker celery-beat

# 4. Run migrations
docker compose exec backend alembic upgrade head

# 5. Seed data
docker compose exec backend python scripts/seed.py

# 6. Start frontends (separate terminals or all at once)
docker compose up -d customer-web business-web admin-web
```

| Service | URL |
|---|---|
| Customer Web | http://localhost:3000 |
| Business Web | http://localhost:3001 |
| Admin Web | http://localhost:3002 |
| API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Flower | http://localhost:5555 (run with `--profile monitoring`) |

---

## Local Development Without Docker

### Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements-dev.txt

# Set environment (copy .env.example and adjust for local DB/Redis)
cp ../.env.example .env
# Edit .env: set DATABASE_URL to point to your local Postgres

# Run migrations
alembic upgrade head

# Seed data
python scripts/seed.py

# Start development server (hot-reload)
uvicorn app.main:app --reload --port 8000
```

### Frontend (all apps)

```bash
# From monorepo root
pnpm install

# Start all three frontends simultaneously
pnpm dev

# Or start individually
pnpm dev:customer   # port 3000
pnpm dev:business   # port 3001
pnpm dev:admin      # port 3002
```

---

## Project Structure Walk-Through

### Backend (`backend/`)

```
app/
├── api/v1/           # Route handlers — kept thin
│   ├── auth.py       # Register, login, refresh, logout, me
│   ├── businesses.py # Business + branch CRUD
│   ├── staff.py      # Staff CRUD + working hours + leaves
│   ├── services.py   # Service + category CRUD
│   ├── bookings.py   # Availability + booking creation/management
│   ├── payments.py   # Payment order, verify, webhook, refund
│   ├── customers.py  # Customer CRM
│   ├── reviews.py    # Reviews
│   ├── users.py      # User profile
│   └── admin.py      # Platform admin
│
├── core/
│   ├── config.py     # All settings from env vars (pydantic-settings)
│   ├── security.py   # Password hashing, JWT create/decode
│   ├── exceptions.py # Domain exceptions → HTTP status codes
│   ├── deps.py       # FastAPI dependencies (auth, RBAC, tenant check)
│   └── permissions.py # Role → permission mapping
│
├── models/           # SQLAlchemy ORM models (one file per domain)
├── schemas/          # Pydantic request/response schemas
├── services/         # All business logic lives here
├── repositories/     # Data-access layer (base + business repo)
├── providers/
│   ├── payment/      # PaymentProvider interface + Razorpay + Mock
│   └── notification/ # Email/SMS/WhatsApp/Push provider interfaces
└── workers/
    ├── celery_app.py # Celery configuration + beat schedule
    └── tasks.py      # All background tasks (reminders, reconciliation)
```

### Adding a New API Endpoint

1. Add Pydantic schemas in `app/schemas/`
2. Add business logic in `app/services/`
3. Add route handler in `app/api/v1/`
4. Register the router in `app/main.py`
5. Write tests in `backend/tests/`

### Adding a Database Table

1. Create SQLAlchemy model in `app/models/`
2. Import it in `app/models/__init__.py`
3. Run `alembic revision --autogenerate -m "add_xxx_table"`
4. Review the generated migration in `alembic/versions/`
5. Apply: `alembic upgrade head`

---

## Environment Variables

See `.env.example` for the full list. Key variables for local development:

```bash
DATABASE_URL=postgresql://zenglow:zenglow_dev@localhost:5432/zenglow_db
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=any-string-is-fine-for-local-dev
ENVIRONMENT=development
DEBUG=true
PAYMENT_PROVIDER=mock        # Use mock — no Razorpay credentials needed
EMAIL_PROVIDER=console       # Logs emails to stdout
SMS_PROVIDER=console         # Logs SMS to stdout
STORAGE_PROVIDER=local       # Saves uploads to ./uploads/
```

---

## Code Style

### Backend (Python)

- Formatter: **ruff format**
- Linter: **ruff check**
- Type checker: **mypy**

```bash
cd backend
ruff format .
ruff check .
mypy app/
```

### Frontend (TypeScript)

- Formatter: **prettier**
- Linter: **eslint** (next/core-web-vitals)
- Type checker: **tsc --noEmit**

```bash
pnpm lint
pnpm type-check
```

---

## Adding a New Payment Provider

1. Create `app/providers/payment/<name>_provider.py` implementing `PaymentProvider` ABC
2. Register it in `app/providers/payment/factory.py`
3. Add config vars to `app/core/config.py`
4. Add to `.env.example`

## Adding a New Notification Provider

1. Create `app/providers/notification/<name>_provider.py`
2. Register it in `app/providers/notification/factory.py`
3. Add config vars to `app/core/config.py`

---

## Hot Reload

- **Backend**: `uvicorn app.main:app --reload` picks up Python changes automatically
- **Frontend**: Next.js dev server uses Fast Refresh — saves are reflected instantly
- **Docker**: Backend and frontend services mount source directories as volumes in `docker-compose.yml`

---

## Useful Commands

```bash
# Backend
docker compose exec backend alembic upgrade head          # Run migrations
docker compose exec backend python scripts/seed.py        # Seed data
docker compose exec backend pytest tests/ -v              # Run tests
docker compose exec backend ruff check .                  # Lint

# Frontend
pnpm install                     # Install all dependencies
pnpm build                       # Production build all apps
pnpm test                        # Run all frontend tests
pnpm type-check                  # Type check all apps

# Docker
docker compose ps                # Check service status
docker compose logs -f backend   # Tail backend logs
docker compose down              # Stop all services
docker compose down -v           # Stop + remove volumes (resets DB)
```
