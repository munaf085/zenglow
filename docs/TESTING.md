# Zenglow — Testing Guide

## Testing Philosophy

- **Test behaviour, not implementation** — test what the system does, not how
- **Real database for integration tests** — no mocks for the database layer
- **Tenant isolation tests are mandatory** — any regression here is a critical security bug
- **Idempotent tests** — each test starts with a clean slate (transaction rollback)

---

## Backend Tests

### Setup

```bash
cd backend

# Install test dependencies
pip install -r requirements.txt

# Ensure a test database exists
# (automatically created by infrastructure/docker/init-db.sql when using Docker)
createdb -U zenglow zenglow_test

# Set test environment
export DATABASE_TEST_URL=postgresql://zenglow:zenglow_dev@localhost:5432/zenglow_test
export REDIS_URL=redis://localhost:6379/15
export ENVIRONMENT=test
export JWT_SECRET_KEY=test-secret-key
export PAYMENT_PROVIDER=mock
export EMAIL_PROVIDER=console
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run a specific test file
pytest tests/test_auth.py -v

# Run a specific test class
pytest tests/test_tenant_isolation.py::TestTenantIsolation -v

# Run a specific test
pytest tests/test_booking.py::TestDoubleBookingPrevention::test_double_booking_rejected -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html --cov-report=term-missing

# Run fast (stop on first failure)
pytest tests/ -x --tb=short

# Run in parallel (install pytest-xdist)
pytest tests/ -n auto
```

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures (DB session, test client, user factories)
├── test_auth.py             # Auth: register, login, refresh, logout, tokens
├── test_business.py         # Business + branch CRUD
├── test_services.py         # Service catalog + staff CRUD + working hours
├── test_booking.py          # Availability, booking creation, double-booking, cancellation
├── test_tenant_isolation.py # Cross-tenant access prevention (critical security tests)
└── test_payments.py         # Payment orders, verify, webhook, refunds
```

### Test Fixtures

Key fixtures defined in `conftest.py`:

| Fixture | Description |
|---|---|
| `db` | Per-test async DB session (transaction-rolled-back after test) |
| `client` | `httpx.AsyncClient` with test DB injected |
| `roles` | All system roles seeded |
| `customer_user` | A customer user + JWT token |
| `admin_user` | A platform admin user + JWT token |
| `business_with_owner` | A business, branch, owner, and owner token |

---

## Tenant Isolation Tests

These are the most important tests in the suite. They verify that:

1. **Owner A cannot read Business B** → HTTP 404
2. **Owner A cannot update Business B** → HTTP 404
3. **Owner A cannot add staff to Business B** → HTTP 404
4. **Owner A cannot create services in Business B** → HTTP 404
5. **Unauthenticated requests get 401 on all protected routes**
6. **Platform admin bypasses isolation** (intentional, verified)
7. **Regular users cannot access admin routes** → HTTP 403

```bash
pytest tests/test_tenant_isolation.py -v
```

All 7 tests must pass on every PR.

---

## Frontend Tests

### Setup

```bash
# From monorepo root
pnpm install
```

### Running Tests

```bash
# Run all frontend tests
pnpm test

# Run tests for a specific app
pnpm --filter customer-web test
pnpm --filter business-web test

# Watch mode during development
pnpm --filter customer-web exec vitest
```

### Test Structure

```
apps/customer-web/src/tests/
├── setup.ts                    # @testing-library/jest-dom setup
├── components/
│   ├── SearchBar.test.tsx       # SearchBar component tests
│   └── BusinessCard.test.tsx    # BusinessCard component tests
└── lib/
    ├── utils.test.ts            # Utility functions
    └── api.test.ts              # API client tokens/errors

apps/business-web/src/tests/
├── setup.ts
└── lib/
    ├── utils.test.ts
    └── api.test.ts
```

---

## E2E Test Scenarios

These are the critical user journeys to test end-to-end:

### Customer Journey
```
1. GET /  → homepage loads
2. POST /auth/register → account created
3. POST /auth/login → token received
4. GET /businesses/search → businesses listed
5. GET /businesses/public/{slug} → business detail
6. GET /availability → slots returned
7. POST /bookings → booking confirmed
8. GET /bookings/me → booking appears in list
9. POST /bookings/{id}/cancel → booking cancelled
```

### Business Owner Journey
```
1. POST /auth/register → account created
2. POST /auth/login → token received
3. POST /businesses → business created
4. POST /businesses/{id}/services → service created
5. POST /businesses/{id}/staff → staff added
6. PUT /businesses/{id}/staff/{sid}/working-hours → hours set
7. GET /businesses/{id}/appointments → see bookings
```

### Admin Journey
```
1. POST /auth/login (admin credentials) → token received
2. GET /admin/dashboard → stats loaded
3. GET /admin/businesses → businesses listed
4. PATCH /admin/businesses/{id} → status updated
5. GET /admin/users → users listed
6. GET /admin/audit-logs → actions logged
```

---

## CI Test Execution

In GitHub Actions (`.github/workflows/ci.yml`):

1. Start PostgreSQL and Redis service containers
2. Apply Alembic migrations
3. Run `pytest tests/ --cov=app --cov-report=xml`
4. Upload coverage to Codecov

Frontend tests run in the same pipeline after `pnpm install`.

---

## Coverage Requirements

| Module | Minimum Coverage |
|---|---|
| `app/services/` | 75% |
| `app/api/v1/` | 70% |
| `app/core/` | 80% |
| Overall | 70% |

Coverage is enforced in `pyproject.toml`:
```toml
[tool.coverage.report]
fail_under = 70
```

---

## Writing New Tests

### Backend test template

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
class TestMyFeature:
    async def test_create_something(self, client: AsyncClient, customer_user):
        _, token = customer_user
        res = await client.post(
            "/api/v1/something",
            json={"field": "value"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 201
        assert res.json()["field"] == "value"
```

### Frontend test template

```tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MyComponent } from "@/components/MyComponent";

describe("MyComponent", () => {
  it("renders correctly", () => {
    render(<MyComponent title="Test" />);
    expect(screen.getByText("Test")).toBeInTheDocument();
  });
});
```
