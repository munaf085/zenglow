# Zenglow — Database Design

## Engine

**PostgreSQL 16** with **SQLAlchemy 2.0** (async) and **Alembic** migrations.

---

## Design Principles

- All primary keys are **UUID v4** (prevents enumeration attacks, globally unique across tenants)
- All timestamps are **timezone-aware** (`TIMESTAMPTZ`)
- Soft delete via `deleted_at` column where data retention matters (users, businesses, staff, services, appointments)
- `business_id` on every tenant-scoped table — indexed for tenant isolation and performance
- Composite indexes for common query patterns (availability lookups, calendar views)

---

## Entity Relationship Summary

```
users
  └── user_roles (role_id, business_id?)  → roles → role_permissions → permissions
  └── customer_profile                    → customers
  └── businesses (owner_id)
        └── branches
        │     └── working_hours (entity_type='branch')
        │     └── resources
        └── staff
        │     └── staff_services          → services
        │     └── working_hours (entity_type='staff')
        │     └── staff_leaves
        └── service_categories
        └── services
        └── appointments
              └── appointment_items (service_id, staff_id, resource_id?)
              └── payments
                    └── refunds
                    └── invoices
              └── reviews

subscriptions → subscription_plans
audit_logs
notifications
```

---

## Tables

### `users`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| email | VARCHAR(255) UNIQUE | Lowercase, indexed |
| phone | VARCHAR(30) | Indexed |
| hashed_password | VARCHAR(255) | bcrypt |
| first_name | VARCHAR(100) | |
| last_name | VARCHAR(100) | |
| avatar_url | VARCHAR(500) | |
| is_active | BOOLEAN | Default true |
| is_verified | BOOLEAN | Email verification |
| is_superuser | BOOLEAN | Platform admin override |
| refresh_token_hash | VARCHAR(255) | Current valid refresh token hash |
| deleted_at | TIMESTAMPTZ | Soft delete |

### `roles`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| name | ENUM | PLATFORM_ADMIN, BUSINESS_OWNER, BUSINESS_MANAGER, STAFF, RECEPTIONIST, CUSTOMER |
| description | TEXT | |
| is_system | BOOLEAN | System-defined roles |

### `permissions`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| name | VARCHAR(100) UNIQUE | e.g. `booking.create`, `staff.update` |
| description | TEXT | |

### `role_permissions`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| role_id | UUID FK → roles | |
| permission_id | UUID FK → permissions | |
| UNIQUE | (role_id, permission_id) | |

### `user_roles`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| user_id | UUID FK → users | Indexed |
| role_id | UUID FK → roles | |
| business_id | UUID FK → businesses NULL | NULL = platform role, non-null = tenant role |
| UNIQUE | (user_id, role_id, business_id) | |

### `subscription_plans`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| tier | ENUM | FREE, STARTER, PROFESSIONAL, ENTERPRISE |
| name | VARCHAR(100) | |
| monthly_price | NUMERIC(10,2) | Not hardcoded — managed by platform admin |
| yearly_price | NUMERIC(10,2) | |
| max_branches | INT | |
| max_staff | INT | |
| max_services | INT | |
| max_bookings_per_month | INT | |

### `businesses`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| owner_id | UUID FK → users | Indexed |
| name | VARCHAR(255) | Indexed |
| slug | VARCHAR(255) UNIQUE | URL-friendly identifier |
| category | ENUM | SALON, SPA, BARBER, BEAUTY, WELLNESS, NAIL_STUDIO, MASSAGE, OTHER |
| status | ENUM | PENDING, ACTIVE, SUSPENDED, DEACTIVATED |
| is_verified | BOOLEAN | Platform-verified badge |
| is_featured | BOOLEAN | Featured in marketplace |
| booking_advance_days | INT | How far ahead customers can book |
| cancellation_hours | INT | Min hours before appointment to cancel |
| deposit_required | BOOLEAN | |
| deposit_percentage | NUMERIC(5,2) | |
| subscription_plan_id | UUID FK → subscription_plans NULL | |
| deleted_at | TIMESTAMPTZ | Soft delete |

### `branches`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| business_id | UUID FK → businesses | Indexed |
| name | VARCHAR(255) | |
| is_primary | BOOLEAN | One primary per business |
| is_active | BOOLEAN | |
| address_line1/2 | VARCHAR(255) | |
| city, state, country | VARCHAR | |
| postal_code | VARCHAR(20) | |
| latitude, longitude | NUMERIC | For geo features |
| deleted_at | TIMESTAMPTZ | |

### `service_categories`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| business_id | UUID FK → businesses | Indexed |
| name | VARCHAR(100) | |
| color | VARCHAR(7) | Hex color for calendar display |
| sort_order | INT | |

### `services`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| business_id | UUID FK → businesses | Indexed |
| category_id | UUID FK → service_categories NULL | |
| name | VARCHAR(255) | |
| price | NUMERIC(10,2) | |
| tax_rate | NUMERIC(5,2) | Default 0 |
| duration_minutes | INT | |
| buffer_before_minutes | INT | Gap before service |
| buffer_after_minutes | INT | Cleanup/reset time |
| is_active | BOOLEAN | |
| online_booking_enabled | BOOLEAN | |
| deleted_at | TIMESTAMPTZ | |

### `staff`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| business_id | UUID FK → businesses | Indexed |
| branch_id | UUID FK → branches NULL | |
| user_id | UUID FK → users NULL | If staff has a login |
| first_name, last_name | VARCHAR(100) | |
| status | ENUM | ACTIVE, INACTIVE, ON_LEAVE |
| bookable | BOOLEAN | Whether customers can choose this staff |
| deleted_at | TIMESTAMPTZ | |

### `staff_services`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| staff_id | UUID FK → staff | Indexed |
| service_id | UUID FK → services | Indexed |
| duration_override_minutes | INT NULL | Staff-specific duration |
| price_override | NUMERIC NULL | Staff-specific pricing |

### `working_hours`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| entity_type | VARCHAR(10) | 'branch' or 'staff' |
| entity_id | UUID | ID of the branch or staff member |
| business_id | UUID FK → businesses | Indexed |
| day_of_week | INT | 0=Monday … 6=Sunday |
| is_open | BOOLEAN | |
| open_time | VARCHAR(5) | HH:MM format |
| close_time | VARCHAR(5) | |
| break_start | VARCHAR(5) NULL | |
| break_end | VARCHAR(5) NULL | |
| INDEX | (entity_type, entity_id) | |

### `staff_leaves`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| staff_id | UUID FK → staff | Indexed |
| business_id | UUID FK → businesses | |
| leave_type | ENUM | ANNUAL, SICK, PERSONAL, BLOCKED |
| start_date | VARCHAR(10) | ISO date YYYY-MM-DD |
| end_date | VARCHAR(10) | |
| approved | BOOLEAN | |

### `customers`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| user_id | UUID FK → users UNIQUE | One customer profile per user |
| notes | TEXT NULL | Staff notes |
| tags | TEXT NULL | Comma-separated tags |
| marketing_opt_in | BOOLEAN | |
| sms_opt_in | BOOLEAN | |
| deleted_at | TIMESTAMPTZ | |

### `appointments`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| business_id | UUID FK → businesses | Indexed |
| branch_id | UUID FK → branches | |
| customer_id | UUID FK → customers | Indexed |
| start_time | TIMESTAMPTZ | Indexed |
| end_time | TIMESTAMPTZ | |
| status | ENUM | PENDING, CONFIRMED, IN_PROGRESS, COMPLETED, CANCELLED, NO_SHOW, RESCHEDULED |
| source | ENUM | ONLINE, WALK_IN, PHONE, STAFF |
| subtotal | NUMERIC(10,2) | Snapshot at booking time |
| tax_amount | NUMERIC(10,2) | |
| total_amount | NUMERIC(10,2) | |
| deposit_amount | NUMERIC(10,2) | |
| reminder_24h_sent | BOOLEAN | Idempotency flag for Celery |
| reminder_2h_sent | BOOLEAN | |
| deleted_at | TIMESTAMPTZ | |

### `appointment_items`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| appointment_id | UUID FK → appointments CASCADE | Indexed |
| service_id | UUID FK → services | |
| staff_id | UUID FK → staff | Indexed |
| resource_id | UUID FK → resources NULL | |
| service_name | VARCHAR(255) | Snapshot |
| duration_minutes | INT | Snapshot |
| price | NUMERIC(10,2) | Snapshot |
| tax_rate | NUMERIC(5,2) | Snapshot |
| start_time | TIMESTAMPTZ | |
| end_time | TIMESTAMPTZ | |

### `payments`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| business_id | UUID FK → businesses | Indexed |
| appointment_id | UUID FK → appointments NULL | |
| customer_id | UUID FK → customers | |
| amount | NUMERIC(10,2) | |
| currency | VARCHAR(3) | Default INR |
| provider | ENUM | RAZORPAY, CASH, MOCK |
| status | ENUM | PENDING, PROCESSING, CAPTURED, FAILED, REFUNDED, PARTIALLY_REFUNDED, CANCELLED |
| provider_order_id | VARCHAR(255) | |
| provider_payment_id | VARCHAR(255) | |
| provider_signature | VARCHAR(500) | Stored for audit |
| paid_at | TIMESTAMPTZ NULL | |

### `refunds`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| payment_id | UUID FK → payments CASCADE | |
| business_id | UUID FK → businesses | |
| amount | NUMERIC(10,2) | |
| reason | TEXT NULL | |
| provider_refund_id | VARCHAR(255) NULL | |
| status | VARCHAR(50) | PENDING, PROCESSED, FAILED |
| processed_by_id | UUID FK → users NULL | |
| processed_at | TIMESTAMPTZ NULL | |

### `invoices`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| payment_id | UUID FK → payments CASCADE | |
| business_id | UUID FK | |
| customer_id | UUID FK | |
| invoice_number | VARCHAR(50) UNIQUE | Auto-generated INV-YYYYMMDD-NNNNN |
| subtotal, tax_amount, discount_amount, total_amount | NUMERIC | |
| issued_at | TIMESTAMPTZ NULL | |

### `reviews`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| business_id | UUID FK → businesses | Indexed |
| customer_id | UUID FK → customers | |
| appointment_id | UUID FK → appointments NULL | |
| rating | INT | CHECK (1–5) |
| comment | TEXT NULL | |
| is_published | BOOLEAN | |
| owner_reply | TEXT NULL | |

### `notifications`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| user_id | UUID FK → users NULL | |
| business_id | UUID FK → businesses NULL | |
| channel | ENUM | EMAIL, SMS, WHATSAPP, PUSH, IN_APP |
| notification_type | ENUM | APPOINTMENT_CONFIRMED, REMINDER_24H, etc. |
| recipient | VARCHAR(255) | Email/phone/token |
| subject | VARCHAR(500) NULL | For emails |
| body | TEXT | |
| status | ENUM | PENDING, SENT, FAILED, DELIVERED |
| sent_at | TIMESTAMPTZ NULL | |
| reference_id | VARCHAR(255) NULL | e.g. appointment UUID |

### `subscriptions`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| business_id | UUID FK → businesses | |
| plan_id | UUID FK → subscription_plans | |
| status | ENUM | ACTIVE, EXPIRED, CANCELLED, TRIAL, PAST_DUE |
| billing_cycle | ENUM | MONTHLY, YEARLY |
| start_date | TIMESTAMPTZ | |
| end_date | TIMESTAMPTZ NULL | |
| trial_end_date | TIMESTAMPTZ NULL | |

### `audit_logs`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| actor_id | UUID FK → users NULL | |
| business_id | UUID FK → businesses NULL | |
| action | VARCHAR(100) | e.g. `admin.business.update` |
| entity_type | VARCHAR(100) NULL | |
| entity_id | VARCHAR(255) NULL | |
| old_values | TEXT NULL | JSON |
| new_values | TEXT NULL | JSON |
| ip_address | VARCHAR(50) NULL | |

### `resources`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| business_id | UUID FK → businesses | |
| branch_id | UUID FK → branches NULL | |
| name | VARCHAR(100) | e.g. "Room 1", "Chair 3" |
| resource_type | VARCHAR(50) | ROOM, CHAIR, EQUIPMENT |
| quantity | INT | |

---

## Indexes

Beyond primary keys, the following indexes are created:

```sql
-- Tenant isolation (most critical)
idx businesses(owner_id)
idx businesses(slug)
idx businesses(status)
idx branches(business_id)
idx staff(business_id)
idx staff(branch_id)
idx services(business_id)
idx service_categories(business_id)
idx appointments(business_id)
idx appointments(customer_id)
idx appointments(start_time)       -- calendar queries
idx appointment_items(appointment_id)
idx appointment_items(staff_id)    -- availability queries
idx working_hours(entity_type, entity_id)
idx working_hours(business_id)
idx payments(business_id)
idx reviews(business_id)
idx user_roles(user_id)
idx user_roles(business_id)
idx audit_logs(actor_id)
idx audit_logs(business_id)
```

---

## Migrations

Migrations are managed with **Alembic**:

```bash
# Apply all migrations
alembic upgrade head

# Create a new migration
alembic revision --autogenerate -m "description"

# Downgrade one step
alembic downgrade -1

# View migration history
alembic history
```

All migrations live in `backend/alembic/versions/`.

---

## Future Schema Extensions

The following tables are architected but not yet implemented (Phase 2+):

| Table | Purpose |
|---|---|
| `memberships` | Recurring membership plans per business |
| `packages` | Pre-paid service bundles |
| `gift_cards` | Purchasable and redeemable gift cards |
| `loyalty_points` | Points accumulation and redemption |
| `inventory_items` | Product inventory per branch |
| `marketing_campaigns` | Email/SMS campaign management |
| `waitlist_entries` | Waitlist for fully-booked slots |
