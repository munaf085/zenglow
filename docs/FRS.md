# Zenglow — Functional Requirements Specification

## 1. Introduction

### 1.1 Purpose
Zenglow is an all-in-one B2B2C SaaS platform for salons, spas, barbers, beauty professionals, and wellness businesses. It enables businesses to manage their operations and customers to discover and book appointments.

### 1.2 Scope
This document covers the MVP feature set. Future phases (POS, memberships, packages, loyalty, mobile apps) are noted as out-of-scope for this version.

### 1.3 Stakeholders

| Role | Description |
|---|---|
| Platform Owner | Operates Zenglow, manages the marketplace and subscriptions |
| Business Owner | Runs a salon/spa, creates and manages their business on Zenglow |
| Business Staff | Stylists, therapists, receptionists — perform services, use the calendar |
| Customer | End-consumer who discovers businesses and books appointments |

---

## 2. User Stories

### 2.1 Customer

**Authentication**
- As a customer, I can register with email and password so I can book appointments
- As a customer, I can log in and receive a JWT token pair
- As a customer, I can refresh my access token without re-logging in
- As a customer, I can log out and have my tokens revoked
- As a customer, I can change my password
- As a customer, I can update my profile (name, phone, avatar)

**Discovery**
- As a customer, I can search businesses by name or keyword
- As a customer, I can filter businesses by category (salon, spa, barber, etc.)
- As a customer, I can filter businesses by city
- As a customer, I can view a business profile including: name, category, description, photos, services, reviews, location, opening hours
- As a customer, I can view individual service details: name, description, price, duration

**Booking**
- As a customer, I can view available time slots for a service on a given date
- As a customer, I can choose any available staff or select a specific staff member
- As a customer, I can book an appointment and receive immediate confirmation
- As a customer, I cannot book in the past
- As a customer, I cannot double-book (the system prevents concurrent slot conflicts)
- As a customer, I can view my upcoming and past appointments
- As a customer, I can cancel an appointment (subject to the business's cancellation policy)
- As a customer, I can view my booking details including services, staff, time, and amount

**Reviews**
- As a customer, I can submit a star rating and comment for a completed appointment
- As a customer, I cannot submit duplicate reviews for the same appointment

### 2.2 Business Owner

**Onboarding**
- As a business owner, I can register and create my business in a guided 3-step flow
- As a business owner, I can configure: name, category, description, contact information, cancellation policy, booking advance days
- As a business owner, I can manage multiple branches, each with its own address, contact, and opening hours

**Services**
- As a business owner, I can create service categories with custom colors
- As a business owner, I can create services with: name, description, price, tax rate, duration, buffer times, online booking toggle
- As a business owner, I can deactivate services without deleting them

**Staff**
- As a business owner, I can add staff members with: name, title, email, phone, bio
- As a business owner, I can assign services to staff members
- As a business owner, I can configure working hours per staff member (per day of week, with break times)
- As a business owner, I can create leave/absence records for staff
- As a business owner, I can deactivate staff members

**Calendar**
- As a business owner/staff, I can view a day or week view of all appointments
- As a business owner, I can see appointments colour-coded by status
- As a business owner, I can update an appointment status (confirmed, completed, no-show, cancelled)

**Payments**
- As a business owner, I can view all payment transactions for my business
- As a business owner, I can initiate a refund for a captured payment
- As a business owner, I can configure whether a deposit is required for bookings

**Customers (CRM)**
- As a business owner, I can view all customers who have booked with my business
- As a business owner, I can view a customer's booking and payment history
- As a business owner, I can add notes and tags to a customer profile

**Reviews**
- As a business owner, I can view reviews for my business
- As a business owner, I can reply to a review once

### 2.3 Platform Admin

**Business Management**
- As an admin, I can list and search all businesses on the platform
- As an admin, I can activate, suspend, or deactivate a business
- As an admin, I can mark a business as verified (shows verification badge)
- As an admin, I can feature a business in the marketplace

**User Management**
- As an admin, I can list and search all users
- As an admin, I can activate or deactivate a user account

**Subscription Plans**
- As an admin, I can create and manage subscription plans with configurable pricing and limits
- Pricing is never hardcoded — all plan prices are stored in the database

**Reporting**
- As an admin, I can view platform-wide dashboard stats: total businesses, users, bookings, and revenue
- As an admin, I can view all bookings and payments across the platform

**Audit**
- All admin actions (business status changes, user management) are audit-logged with actor, timestamp, and changed values

---

## 3. Non-Functional Requirements

### 3.1 Security
- Passwords stored as bcrypt hashes — never plaintext
- JWT access tokens expire in 30 minutes; refresh tokens in 30 days
- Refresh tokens are rotated on use; old tokens are revoked immediately
- Payment verification is always server-side — frontend payment status is never trusted
- Webhook signatures are verified before processing
- Tenant isolation enforced at service layer — not just frontend routing

### 3.2 Performance
- Availability query response < 500ms for typical business (up to 10 staff, 60-day window)
- API response time P95 < 300ms for CRUD operations
- Database queries use indexes on `business_id`, `start_time`, `staff_id`

### 3.3 Reliability
- Double-booking prevented via Redis slot lock + transactional DB conflict check
- Celery tasks are idempotent (safe to retry)
- Payment reconciliation job automatically expires stale pending payments
- Health endpoints for load balancer / container orchestrator checks

### 3.4 Scalability
- Stateless backend — multiple instances can run behind a load balancer
- No in-process state — all shared state via PostgreSQL or Redis
- Background jobs handled by separate Celery workers (horizontally scalable)

### 3.5 Availability
- Services are containerised with health checks and automatic restart policies
- PostgreSQL and Redis use persistent volumes for data durability

---

## 4. Out of Scope (MVP)

The following features are architecturally prepared but not implemented in this version:

- Point of Sale (POS) terminal integration
- Memberships and recurring subscriptions
- Pre-paid service packages
- Gift cards
- Loyalty/points system
- Marketing automation and campaigns
- Advanced analytics and revenue reports
- Native mobile applications (Android / iOS)
- Multi-language / i18n
- Inventory management
- Waitlist management
