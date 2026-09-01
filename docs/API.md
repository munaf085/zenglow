# Zenglow — API Reference

## Base URL

```
http://localhost:8000/api/v1
```

Interactive documentation is available at `http://localhost:8000/docs` in development.

---

## Authentication

All protected endpoints require a Bearer token:

```
Authorization: Bearer <access_token>
```

### Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/auth/register` | Register new customer account |
| POST | `/auth/login` | Login with email + password → token pair |
| POST | `/auth/refresh` | Exchange refresh token for new token pair |
| POST | `/auth/logout` | Revoke current tokens |
| GET | `/auth/me` | Get current authenticated user |
| POST | `/auth/change-password` | Change password |

### Register
```http
POST /auth/register
Content-Type: application/json

{
  "email": "customer@example.com",
  "password": "Secure@1234",
  "first_name": "Emma",
  "last_name": "Wilson"
}
```

### Login
```http
POST /auth/login
Content-Type: application/json

{
  "email": "customer@example.com",
  "password": "Secure@1234"
}
```

Response:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

---

## Error Format

All errors use a consistent envelope:

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Business with id 'xxx' not found",
    "details": {}
  }
}
```

| HTTP Status | Code | Meaning |
|---|---|---|
| 400 | BUSINESS_RULE_VIOLATION | Violated a business rule |
| 401 | AUTHENTICATION_ERROR | Missing or invalid token |
| 402 | PAYMENT_ERROR | Payment failed |
| 403 | AUTHORIZATION_ERROR | Insufficient role/permissions |
| 404 | NOT_FOUND | Resource not found or tenant isolation |
| 409 | CONFLICT | Duplicate resource or slot unavailable |
| 422 | VALIDATION_ERROR | Request schema validation failed |
| 429 | RATE_LIMIT_EXCEEDED | Too many requests |
| 500 | INTERNAL_ERROR | Unexpected server error |

---

## Pagination

Paginated endpoints accept `page` and `page_size` query parameters and return:

```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "page_size": 20,
  "pages": 8
}
```

---

## Businesses

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/businesses` | Required | Create a business |
| GET | `/businesses` | Required | List my businesses |
| GET | `/businesses/search` | Public | Search businesses |
| GET | `/businesses/{id}` | Required | Get business (owner/staff) |
| GET | `/businesses/public/{slug}` | Public | Get active business by slug |
| PATCH | `/businesses/{id}` | Required | Update business |
| POST | `/businesses/{id}/branches` | Required | Create branch |
| GET | `/businesses/{id}/branches` | Required | List branches |
| PATCH | `/businesses/{id}/branches/{bid}` | Required | Update branch |
| PUT | `/businesses/{id}/branches/{bid}/working-hours` | Required | Set branch hours |
| GET | `/businesses/{id}/branches/{bid}/working-hours` | Public | Get branch hours |

### Create Business
```http
POST /businesses
Authorization: Bearer <token>

{
  "name": "Glow Studio",
  "category": "SALON",
  "description": "Premium hair salon",
  "phone": "+91 98765 43210",
  "booking_advance_days": 60,
  "cancellation_hours": 24,
  "branch": {
    "name": "Main Branch",
    "city": "Mumbai",
    "address_line1": "42 Fashion Street"
  }
}
```

---

## Staff

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/businesses/{id}/staff` | Required | Add staff member |
| GET | `/businesses/{id}/staff` | Required | List staff |
| GET | `/businesses/{id}/staff/{sid}` | Required | Get staff member |
| PATCH | `/businesses/{id}/staff/{sid}` | Required | Update staff |
| DELETE | `/businesses/{id}/staff/{sid}` | Required | Deactivate staff |
| PUT | `/businesses/{id}/staff/{sid}/working-hours` | Required | Set staff hours |
| GET | `/businesses/{id}/staff/{sid}/working-hours` | Required | Get staff hours |
| POST | `/businesses/{id}/staff/{sid}/leaves` | Required | Create leave |
| GET | `/businesses/{id}/staff/{sid}/leaves` | Required | List leaves |

---

## Services

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/businesses/{id}/services` | Required | Create service |
| GET | `/businesses/{id}/services` | Public | List services |
| GET | `/businesses/{id}/services/{sid}` | Public | Get service |
| PATCH | `/businesses/{id}/services/{sid}` | Required | Update service |
| DELETE | `/businesses/{id}/services/{sid}` | Required | Delete service |
| POST | `/businesses/{id}/services/categories` | Required | Create category |
| GET | `/businesses/{id}/services/categories` | Public | List categories |
| PATCH | `/businesses/{id}/services/categories/{cid}` | Required | Update category |
| DELETE | `/businesses/{id}/services/categories/{cid}` | Required | Delete category |

---

## Availability

```http
GET /availability?business_id=<uuid>&branch_id=<uuid>&service_id=<uuid>&date=2024-07-15
GET /availability?...&staff_id=<uuid>   # specific staff
```

Response:
```json
{
  "date": "2024-07-15",
  "service_id": "...",
  "service_name": "Haircut",
  "duration_minutes": 45,
  "slots": [
    {
      "start_time": "2024-07-15T09:00:00Z",
      "end_time": "2024-07-15T09:45:00Z",
      "staff_id": "...",
      "staff_name": "Alex Thompson",
      "available": true
    }
  ]
}
```

---

## Bookings

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/bookings` | Required | Create booking |
| GET | `/bookings/me` | Required | My bookings |
| GET | `/bookings/{id}` | Required | Get booking |
| POST | `/bookings/{id}/cancel` | Required | Cancel booking |
| GET | `/businesses/{id}/appointments` | Required | Business appointments |
| PATCH | `/businesses/{id}/appointments/{aid}/status` | Required | Update appointment status |

### Create Booking
```http
POST /bookings
Authorization: Bearer <token>

{
  "business_id": "...",
  "branch_id": "...",
  "items": [
    {
      "service_id": "...",
      "staff_id": "...",
      "start_time": "2024-07-15T10:00:00Z"
    }
  ],
  "customer_notes": "Please use organic products"
}
```

---

## Payments

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/payments/orders` | Required | Create payment order |
| POST | `/payments/verify` | Required | Verify + capture payment |
| POST | `/payments/webhook` | None (signature) | Provider webhook |
| GET | `/payments/{id}` | Required | Get payment |
| GET | `/businesses/{id}/payments` | Required | Business payments |
| POST | `/payments/{id}/refunds` | Required | Create refund |

### Payment Flow
```
1. POST /payments/orders  → get provider_order_id + payment_id
2. Customer pays via provider SDK (frontend)
3. POST /payments/verify  → server verifies signature → captures
```

> **Important**: Never confirm a booking based on frontend-reported payment status. Always call `/payments/verify` on the server before marking a booking as paid.

---

## Reviews

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/reviews` | Required | Submit review |
| GET | `/businesses/{id}/reviews` | Public | List business reviews |
| GET | `/businesses/{id}/reviews/stats` | Public | Average rating + count |
| POST | `/businesses/{id}/reviews/{rid}/reply` | Required | Owner reply |

---

## Customers

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/customers/me` | Required | Get my customer profile |
| PATCH | `/customers/me` | Required | Update my profile |
| GET | `/businesses/{id}/customers` | Required | Business CRM customers |
| GET | `/businesses/{id}/customers/{cid}` | Required | Get customer (business view) |
| PATCH | `/businesses/{id}/customers/{cid}` | Required | Update CRM notes/tags |

---

## Admin

All admin routes require `PLATFORM_ADMIN` role.

| Method | Path | Description |
|---|---|---|
| GET | `/admin/dashboard` | Platform stats |
| GET | `/admin/businesses` | List all businesses |
| PATCH | `/admin/businesses/{id}` | Update business status/verification |
| GET | `/admin/users` | List all users |
| PATCH | `/admin/users/{id}` | Update user (activate/deactivate) |
| GET | `/admin/bookings` | All bookings |
| GET | `/admin/payments` | All payments |
| GET | `/admin/subscription-plans` | List plans |
| POST | `/admin/subscription-plans` | Create plan |
| GET | `/admin/audit-logs` | Platform audit log |

---

## Health

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Application health |
| GET | `/ready` | Readiness (DB + Redis check) |
| GET | `/live` | Liveness probe |
