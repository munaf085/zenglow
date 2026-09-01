# Zenglow

An all-in-one multi-tenant SaaS platform for salons, spas, barbers, beauty professionals, and wellness businesses.

**B2B2C model:** Businesses manage operations via the Business Portal. Customers discover and book via the Customer Site. Platform owners administrate via the Admin Portal.

---

## What's Inside

| App | Port | Description |
|---|---|---|
| Customer Web | 3000 | Discovery, booking, account management |
| Business Web | 3001 | Business management dashboard, calendar, CRM |
| Admin Web | 3002 | Platform administration portal |
| Backend API | 8000 | FastAPI REST API + OpenAPI docs |
| PostgreSQL | 5432 | Primary database |
| Redis | 6379 | Cache, slot locking, Celery broker |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14, React 18, TypeScript, Tailwind CSS |
| Backend | Python 3.11, FastAPI, SQLAlchemy 2.0 (async) |
| Database | PostgreSQL 16 |
| Cache / Jobs | Redis 7, Celery |
| Auth | JWT (access + refresh), bcrypt, RBAC |
| Payments | Razorpay (mock provider for development) |
| Notifications | Email (SMTP), SMS, WhatsApp, Push (console in dev) |
| Monorepo | pnpm workspaces + Turborepo |
| Containers | Docker, Docker Compose |
| CI/CD | GitHub Actions |

---

## Quick Start

### Prerequisites

- Docker 24+ and Docker Compose
- Git

### 1 — Clone

```bash
git clone https://github.com/your-org/zenglow.git
cd zenglow
```

### 2 — Configure environment

```bash
cp .env.example .env
# Default values work for local Docker development.
# No edits required to run locally.
```

### 3 — Start services

```bash
docker compose up -d postgres redis backend celery-worker celery-beat
```

### 4 — Run database migrations

```bash
docker compose exec backend alembic upgrade head
```

### 5 — Seed demo data

```bash
docker compose exec backend python scripts/seed.py
```

### 6 — Start frontend applications

```bash
docker compose up -d customer-web business-web admin-web
```

### 7 — Open in browser

| Service | URL |
|---|---|
| Customer Site | http://localhost:3000 |
| Business Portal | http://localhost:3001 |
| Admin Portal | http://localhost:3002 |
| API Docs (Swagger) | http://localhost:8000/docs |
| API Health | http://localhost:8000/health |

---

## Demo Credentials

> These credentials are for local development only. Never use in production.

| Role | Email | Password |
|---|---|---|
| Platform Admin | admin@zenglow.com | Admin@1234 |
| Business Owner | owner@glowstudio.com | Owner@1234 |
| Business Owner 2 | owner@urbancuts.com | Owner@1234 |
| Business Owner 3 | owner@serenityspa.com | Owner@1234 |
| Staff | staff@glowstudio.com | Staff@1234 |
| Customer | customer@example.com | Customer@1234 |

### Seeded Businesses

| Business | Type | City |
|---|---|---|
| Glow Studio | Salon | Mumbai |
| Urban Cuts | Barbershop | Delhi |
| Serenity Spa | Spa | Bangalore |

---

## Running Without Docker

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

# Copy and adjust .env to point to your local Postgres + Redis
alembic upgrade head
python scripts/seed.py
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
# From repo root
npm install -g pnpm@8
pnpm install
pnpm dev          # starts all three apps
# or individually:
pnpm dev:customer   # http://localhost:3000
pnpm dev:business   # http://localhost:3001
pnpm dev:admin      # http://localhost:3002
```

---

## Running Tests

### Backend

```bash
# Requires postgres + redis running (use docker compose up -d postgres redis)
cd backend
pip install -r requirements.txt
pytest tests/ -v

# With coverage
pytest tests/ --cov=app --cov-report=term-missing
```

### Frontend

```bash
pnpm test
# or per app:
pnpm --filter customer-web test
pnpm --filter business-web test
```

---

## Project Structure

```
zenglow/
├── apps/
│   ├── customer-web/          # Next.js — customer site
│   ├── business-web/          # Next.js — business dashboard
│   └── admin-web/             # Next.js — admin portal
├── backend/
│   ├── app/
│   │   ├── api/v1/            # Route handlers
│   │   ├── core/              # Config, security, exceptions, RBAC
│   │   ├── db/                # DB session, Redis client
│   │   ├── models/            # SQLAlchemy models
│   │   ├── providers/         # Payment + notification abstractions
│   │   ├── repositories/      # Data access layer
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # Business logic
│   │   └── workers/           # Celery tasks
│   ├── alembic/               # Migrations
│   ├── scripts/               # Seed data
│   └── tests/                 # Test suite
├── packages/
│   ├── types/                 # Shared TypeScript types
│   └── config/                # Shared API client + constants
├── infrastructure/
│   └── docker/                # Dockerfiles + init SQL
├── docs/                      # Documentation
├── .github/workflows/         # CI/CD
├── docker-compose.yml
└── .env.example
```

---

## API

The REST API is documented interactively at `http://localhost:8000/docs` (Swagger UI).

Key endpoint groups:

| Group | Base path |
|---|---|
| Auth | `/api/v1/auth` |
| Businesses | `/api/v1/businesses` |
| Staff | `/api/v1/businesses/{id}/staff` |
| Services | `/api/v1/businesses/{id}/services` |
| Availability | `/api/v1/availability` |
| Bookings | `/api/v1/bookings` |
| Payments | `/api/v1/payments` |
| Customers | `/api/v1/customers` |
| Reviews | `/api/v1/reviews` |
| Admin | `/api/v1/admin` |

See [docs/API.md](docs/API.md) for the full reference.

---

## Architecture

Zenglow uses a clean layered architecture:

```
HTTP Request → FastAPI Router → Service → Repository → PostgreSQL
                                    ↓
                             Celery Worker (async jobs)
                                    ↓
                         Notification Providers (email/SMS/push)
```

Key design decisions:
- **Multi-tenancy** — row-level via `business_id`, enforced in the service layer
- **RBAC** — role/permission mapping in `app/core/permissions.py`
- **Booking engine** — Redis slot locking + transactional DB conflict check prevents double-booking
- **Payment safety** — server-side signature verification; frontend status is never trusted
- **Provider abstractions** — payment and notification providers are swappable without code changes

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full design.

---

## Docker Commands

```bash
# Start everything
docker compose up -d

# View logs
docker compose logs -f backend
docker compose logs -f celery-worker

# Run migrations
docker compose exec backend alembic upgrade head

# Seed data
docker compose exec backend python scripts/seed.py

# Run backend tests inside container
docker compose exec backend pytest tests/ -v

# Stop everything
docker compose down

# Stop and remove volumes (resets database)
docker compose down -v

# Start with Celery Flower monitoring (http://localhost:5555)
docker compose --profile monitoring up -d
```

---

## CI/CD

Two GitHub Actions workflows:

| Workflow | Trigger | Steps |
|---|---|---|
| `ci.yml` | Every PR + push | Lint → Type check → Backend tests → Frontend tests → Docker build validation |
| `deploy.yml` | Push to `main` + version tags | Build Docker images → Push to GHCR → SSH deploy to server |

Configure these secrets in your GitHub repository for deployment:
- `DEPLOY_HOST` — server IP or hostname
- `DEPLOY_USER` — SSH user
- `DEPLOY_SSH_KEY` — private SSH key

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for full deployment instructions.

---

## Environment Variables

Copy `.env.example` to `.env` and configure. Key variables:

```bash
DATABASE_URL=postgresql://zenglow:zenglow_dev@postgres:5432/zenglow_db
REDIS_URL=redis://redis:6379/0
JWT_SECRET_KEY=change-this-in-production
ENVIRONMENT=development
PAYMENT_PROVIDER=mock          # razorpay in production
EMAIL_PROVIDER=console         # smtp in production
```

See `.env.example` for the complete list with descriptions.

---

## Documentation

| Document | Description |
|---|---|
| [docs/FRS.md](docs/FRS.md) | Functional Requirements Specification |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture and design decisions |
| [docs/DATABASE.md](docs/DATABASE.md) | Database schema reference |
| [docs/API.md](docs/API.md) | API endpoint reference |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | On-prem deployment guide |
| [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) | Local development setup |
| [docs/TESTING.md](docs/TESTING.md) | Testing guide and conventions |
| [docs/GIT-WORKFLOW.md](docs/GIT-WORKFLOW.md) | Branch strategy and commit conventions |

---

## License

Proprietary. All rights reserved.
