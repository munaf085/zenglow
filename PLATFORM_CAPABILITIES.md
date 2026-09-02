# Zenglow SaaS Platform: Capabilities & Gaps Matrix

As the platform owner, this document serves as your complete map of what has been built, and what gaps currently exist in the product. The Zenglow platform is a **multi-tenant B2B2C SaaS** divided into three distinct frontend web applications, powered by a unified Python backend.

---

## 🟢 PART 1: Current Capabilities (What is Built)

### 1. Customer Web App (`apps/customer-web`)
*The public-facing portal where end-users discover salons and book appointments.*

**Fully Implemented Screens & Routes:**
*   `/explore`: Search and filter businesses by category, location, and availability.
*   `/business/[id]`: Public business profiles showing the salon's service menu, operating hours, address, staff list, and past reviews.
*   `/book`: The complete checkout flow (Select service -> Pick staff -> Choose time slot -> Pay).
*   `/login` & `/register`: Customer authentication.
*   `/profile`: Customer dashboard to view past/upcoming appointments, manage favorites, and update account info.
*   `/review`: Interface for customers to leave 1-5 star ratings for completed appointments.

### 2. Business Web App (`apps/business-web`)
*The B2B Dashboard where salon owners and staff run their daily operations.*

**Fully Implemented Dashboard Screens (`/dashboard/*`):**
*   `/calendar` & `/schedule`: Interactive daily/weekly schedule views for all staff appointments.
*   `/services`: CRUD interface to build the salon's service menu (pricing, duration, categories).
*   `/staff`: Add employees, set their specific working hours, and assign them to branches.
*   `/customers`: A built-in CRM tracking client history and contact info.
*   `/pos` & `/payments`: Point of Sale digital cash register to ring up walk-in customers and process transactions.
*   `/inventory`: Track stock levels for physical products sold at the salon.
*   `/gift-cards`, `/memberships`, `/packages`: Create and sell digital gift cards, recurring VIP subscriptions, and bundled service packages.
*   `/invoices` & `/reports`: View revenue metrics and generate PDF invoices.
*   `/reviews`: Dashboard to read and respond to customer feedback.
*   `/settings`: Manage multi-branch setups, granular operating hours, business profile, and SaaS subscriptions.

### 3. Admin Web App (`apps/admin-web`)
*The global control center for the Platform Owner and internal staff.*

**Fully Implemented Admin Screens (`/(admin)/*`):**
*   `/verification`: KYC pipeline to review, approve, reject, or suspend newly registered salons.
*   `/businesses` & `/users`: Global view and management of every salon, owner, staff member, and customer on the platform.
*   `/bookings` & `/payments`: Global oversight of all appointments and financial transactions flowing through the platform.
*   `/dashboard` & `/reports`: High-level metrics showing total platform revenue, active businesses, and booking volume.
*   `/settings`: Platform-wide configuration and global SaaS billing plans.

### 4. Backend Engine (`backend/app`)
*The hidden powerhouse running on Python & FastAPI.*
*   **Security & Audit:** Strict Role-Based Access Control preventing data leaks between tenants. Uneditable security audit logs (`audit.py`).
*   **Physical Resources (`resource.py`):** Advanced scheduling that prevents double-booking physical rooms or equipment (e.g., reserving a specific massage room).
*   **Background Workers:** Celery integration for asynchronous tasks and automated state machines (e.g., booking statuses).
*   **Soft Deletes:** Preserves historical analytics by hiding, rather than permanently deleting, removed services or staff.

---

## 🟡 PART 2: Current Gaps & Feature Backlog (What is Missing)

While the core booking and commerce engine is incredibly robust, the platform currently has a few gaps in marketing, advanced scheduling, and UI polish. These are perfect tasks to assign to developers.

### 🟩 Beginner Gaps (UI & Simple Data)
*These features are missing simple database columns or frontend UI components.*
*   **Social Media Integration:** Businesses currently have no way to link their Instagram, Facebook, or TikTok on their public profiles.
*   **Business Amenities:** Customers cannot see if a salon has Free Wi-Fi, Parking, or Wheelchair Accessibility (needs toggle switches in settings).
*   **FAQ Section:** Businesses cannot add a list of Frequently Asked Questions to their public profile.
*   **Newsletter Capture:** There is no form on the customer website to capture emails for marketing.

### 🟨 Intermediate Gaps (Marketing & Logic)
*These features are missing core marketing and operational logic.*
*   **Promo Codes & Coupons Engine:** While appointments support discounts, there is no system to generate, track, and validate specific coupon codes (e.g., "SUMMER20").
*   **Appointment Waitlist:** If a day is fully booked, customers have no way to join a waitlist to be notified of cancellations.
*   **Custom Intake Forms:** Spas cannot ask customers to fill out mandatory health questionnaires (e.g., allergies) before booking a facial.

### 🟥 Advanced Gaps (High Value / Complex)
*These features require third-party integrations or file handling.*
*   **Staff Portfolios (Before/After Gallery):** Staff members currently cannot upload photos of their work to their profiles. (Requires file upload handling to S3/Minio).
*   **Automated SMS/Email Reminders:** The system does not actively text customers 24 hours before their appointment (Requires Twilio/SendGrid integration).
*   **Customer Referral Program:** No system exists to generate unique referral links that grant platform credits when shared with friends.
