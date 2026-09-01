# Zenglow — Architecture

## Overview

Zenglow is a B2B2C multi-tenant SaaS platform for salons, spas, and wellness businesses.
It is structured as a **monorepo** containing three Next.js web applications, a FastAPI backend, shared packages, infrastructure configuration, and documentation.

---

## Monorepo Layout

```
zenglow/
├── apps/
│   ├── customer-web/        # Customer-facing booking site  (port 3000)
│   ├── business-web/        # Business management dashboard (port 3001)
│   └── admin-web/           # Platform admin portal         (port 3002)
├── backend/
│   ├── app/
│   │   ├── api/v1/          # FastAPI route handlers (thin — delegate to services)
│   │   ├── core/            # Config, security, exceptions, deps, permissions
│   │   ├── db/              # SQLAlchemy engine, session, Redis client
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── providers/       # Payment & notification provider abstractions
│   │   ├── repositories/    # Data-access layer
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   ├── services/        # Domain/business logic
│   │   └── workers/         # Celery tasks and app
│   ├── alembic/             # Database migrations
│   ├── scripts/             # Seed data, utilities
│   └── tests/               # Pytest test suite
├── packages/
│   ├── types/               # Shared TypeScript types
│   └── config/              # Shared API client + constants
├── infrastructure/
│   └── docker/              # All Dockerfiles + init SQL
├── docs/                    # Documentation
└── .github/workflows/       # CI/CD pipelines
```

---

## Backend Architecture

### Request Flow

```
HTTP Request
    ↓
FastAPI Router (app/api/v1/)
    ↓  (validates Pydantic schema, injects dependencies)
Service Layer (app/services/)
    ↓  (business logic, tenant + RBAC checks)
Repository Layer (app/repositories/)
    ↓  (data access queries)
SQLAlchemy ORM → PostgreSQL
```

Background work:
```
Service Layer → Celery Task Queue (Redis) → Worker → DB / Notification Providers
```

### Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Async ORM | SQLAlchemy 2.0 async | Native async support, type-safe, production-proven |
| Migration tool | Alembic | Industry standard for SQLAlchemy projects |
| Auth | JWT (access + refresh) | Stateless, mobile-ready, rotate-on-refresh |
| Token revocation | Redis blocklist | Fast O(1) lookup, TTL-based expiry |
| Background jobs | Celery + Redis | Reliable, supports retries, scheduling, monitoring |
| Multi-tenancy | Row-level, business_id FK | Simple, no schema overhead, index-optimised |
| Slot locking | Redis SETNX with TTL | Prevents race conditions without DB transactions |
| Payment verify | Server-side signature | Never trust frontend payment status |
| Notifications | Provider abstraction | Swap email/SMS/WhatsApp without code changes |

---

## Frontend Architecture

### Three Applications

| App | Purpose | Auth |
|---|---|---|
| `customer-web` | Discover businesses, book appointments | Optional (guest browse, auth to book) |
| `business-web` | Manage business operations | Required (business owner/staff) |
| `admin-web` | Platform administration | Required (platform admin role only) |

All three applications are **Next.js 14 App Router** projects using:
- **TypeScript** — strict mode
- **Tailwind CSS** — utility-first styling
- **TanStack Query** — server state management
- **React Hook Form + Zod** — form validation
- **Sonner** — toast notifications
- **Lucide React** — icons

### Shared Packages

- `@zenglow/types` — TypeScript interfaces that mirror backend Pydantic schemas
- `@zenglow/config` — `API_BASE_URL`, category constants, shared API client

---

## Multi-Tenancy

Every business-owned resource carries a `business_id` foreign key. The backend enforces isolation at the **service layer** via `assert_business_access(user, business_id)` before any read or write operation. This function:

1. Checks `user.is_superuser` (platform admins bypass all tenant checks)
2. Checks `UserRole` records for a role scoped to the given `business_id`
3. Raises `TenantIsolationError` if neither condition is met — returned as **HTTP 404** to avoid leaking resource existence

Database indexes on `business_id` columns ensure queries remain fast at scale.

---

## RBAC

Roles are stored in the `roles` table. `UserRole` links a user to a role, optionally scoped to a `business_id`:

- `business_id = NULL` → platform-level role (e.g. `PLATFORM_ADMIN`)
- `business_id = <uuid>` → tenant-scoped role (e.g. `BUSINESS_OWNER`, `STAFF`)

Permissions are defined in `app/core/permissions.py` and mapped to roles. Services check permissions at the service layer — not scattered through route handlers.

---

## Booking Engine

The booking engine (`app/services/availability_service.py` + `booking_service.py`) follows this flow:

```
1. Validate business is ACTIVE
2. Validate branch is active
3. Find eligible staff (assigned to service, bookable, ACTIVE status)
4. For each staff: compute working hours for target date
5. Check staff leave (StaffLeave table)
6. Load existing booked windows (AppointmentItem start/end)
7. Load Redis-locked windows (slot locks from concurrent requests)
8. Generate candidate slots on 15-minute grid
9. Filter out: past times, break overlaps, booked/locked overlaps
10. Return available slots

On booking creation:
1. SETNX Redis lock for the slot (TTL = 5 minutes)
2. Re-check DB for conflicts inside a transaction (double-check after lock)
3. Persist Appointment + AppointmentItems
4. Release Redis lock
5. Queue notification task
```

---

## Security Architecture

| Concern | Implementation |
|---|---|
| Password storage | bcrypt via passlib |
| JWT signing | HS256, configurable secret |
| Refresh token rotation | New pair on every refresh, old token revoked in Redis |
| Tenant isolation | Service-layer `assert_business_access()` on every operation |
| Payment verification | Server-side HMAC signature check before capturing payment |
| Webhook authenticity | Razorpay signature verification before processing |
| CORS | Configurable allow-list via `ALLOWED_ORIGINS` env var |
| Secrets | Environment variables only — never committed |
| Audit trail | `AuditLog` table for all admin actions |

---

## Observability

- **Structured logging** via `structlog` — JSON in production, coloured in development
- **Request IDs** — `X-Request-ID` header added to every response
- **Health endpoints** — `/health`, `/ready`, `/live`
- **Sentry** — DSN configured via `SENTRY_DSN` env var
- **OpenTelemetry** — OTLP export endpoint via `OTEL_EXPORTER_OTLP_ENDPOINT`
- **Celery Flower** — task monitoring UI on port 5555 (optional Docker profile)

---

## Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for full on-prem deployment instructions.

The stack is entirely containerised and has **no hard dependency on AWS/Azure**:
- PostgreSQL 16 (any host)
- Redis 7 (any host)
- Docker + Docker Compose
- GitHub Actions for CI/CD → SSH deploy via `docker compose pull && up -d`
