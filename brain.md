# ProcureSync — Comprehensive System Architecture & Knowledge Brain (`brain.md`)

Welcome to the central architectural, technical, and operational knowledge repository for **ProcureSync (Enterprise Expense & Procurement Management Platform)**. This document provides an exhaustive, end-to-end breakdown of the system design, data models, workflows, API specifications, frontend architecture, security/RBAC rules, test suites, and deployment guidelines.

---

## 1. Executive Summary & System Overview

**ProcureSync** is a unified, cloud-native Enterprise Resource Planning (ERP) subsystem designed to streamline and automate:
1. **Corporate Expense Management & Automated OCR Extraction**: Employee reimbursement lifecycle with multi-receipt uploads, OCR text extraction (Tesseract OCR / AWS Textract), fraud/duplicate detection, policy validations, and multi-tier approval routing.
2. **End-to-End Procurement Lifecycle**: Requisition (PR), RFQ dispatch, vendor quotation bidding & comparison matrices, automated Purchase Order (PO) generation, contract management, delivery tracking, Goods Receipt Notes (GRN), and physical asset inventory registry.
3. **Automated 3-Way Matching & Invoicing**: Automated matching of PO lines, GRN accepted quantities, and Vendor Invoice billings with discrepancy tolerances and payment authorization workflows.
4. **Asset Lifecycle & Incident Management**: Corporate asset tagging, assignment tracking, incident reporting (damage, loss, maintenance), repair/replacement approval workflows, and employee offboarding asset reclamation.
5. **Multi-Role Executive Approvals & Unified Inbox**: Centralized approval inbox for Managers, Procurement Officers, Finance Managers, CFOs, and CEOs with single-click actions, audit trails, and strict role segregation.

---

## 2. Technical Stack & System Architecture

```mermaid
graph TD
    Client["React 18 SPA (Vite + TS + Tailwind)"] -->|HTTPS / REST API| Gateway["FastAPI Web Framework"]
    Gateway --> Middleware["Middleware: Security, CORS, GZip, RequestID, Logging"]
    Middleware --> Routers["FastAPI Routers (/api/v1/...)"]
    
    Routers --> AuthModule["Auth & RBAC Service"]
    Routers --> ExpenseModule["Expense & OCR Service"]
    Routers --> ProcureModule["Procurement & PO Service"]
    Routers --> MatchingModule["3-Way Matching & Invoice Service"]
    Routers --> AssetModule["Asset & Incident Service"]
    Routers --> ApprovalModule["Approval Matrix Engine"]
    
    ExpenseModule --> Tesseract["Tesseract OCR / AWS Textract"]
    
    AuthModule --> DB[(PostgreSQL / SQLite via SQLAlchemy 2.0 Async)]
    ProcureModule --> DB
    ExpenseModule --> DB
    MatchingModule --> DB
    AssetModule --> DB
    ApprovalModule --> DB
    
    Routers --> CacheManager["Cache Layer (Redis / In-Memory)"]
    Routers --> Schedulers["Async Background Job Scheduler"]
```

### 2.1 Backend Architecture
- **Framework**: FastAPI (Python 3.11 - 3.14 compatible)
- **Database ORM**: SQLAlchemy 2.0 (fully asynchronous via `AsyncSession` & `create_async_engine`)
- **Database Dialect**: PostgreSQL (`asyncpg` for Supabase / Production PostgreSQL) and SQLite (`aiosqlite` for local dev/testing)
- **Data Validation & Serializers**: Pydantic V2 with custom validators, strict type checking, and response models
- **Database Migrations**: Alembic for structured schema versioning
- **OCR Engines**: Dual-mode engine supporting local Tesseract OCR (`pytesseract`) and AWS Textract
- **Caching**: Multi-tier caching (`InMemoryCache` and `RedisCache`) with factory pattern
- **Background Tasks**: Async Job Scheduler for scheduled reports, email queue processing, and system metric collection

### 2.2 Frontend Architecture
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite 5 (optimized chunk splitting for charts, lucide icons, and vendors)
- **Routing**: React Router (configured with `HashRouter` for reliable client-side SPA routing across static CDN hosts and Render)
- **Styling**: Vanilla CSS + TailwindCSS utility classes + custom UI design tokens
- **Data Fetching**: Custom Axios instance (`src/services/api.ts`) with request/response interceptors, automatic JWT bearer injection, and refresh token handling
- **Charts & Visualization**: Recharts for dynamic analytics dashboards, spending trends, and category distribution

### 2.3 DevOps & Deployment
- **Containerization**: Multi-stage `Dockerfile` and `docker-compose.yml` (App, PostgreSQL, Redis, Frontend)
- **Cloud Hosting**: Render Web Service (`render.yaml`) & SPA Static Site with `public/_redirects`
- **Reverse Proxy**: Nginx configuration (`frontend/nginx.conf`)

---

## 3. Database Architecture & Schema Reference

The system database comprises **12 core domains** modeled cleanly in `src/models/`:

```mermaid
erDiagram
    USERS ||--o{ USER_ROLES : has
    ROLES ||--o{ USER_ROLES : assigned_to
    USERS ||--o{ EXPENSE_REPORTS : creates
    EXPENSE_REPORTS ||--o{ RECEIPTS : contains
    EXPENSE_REPORTS ||--o{ EXPENSE_APPROVALS : undergoes
    
    USERS ||--o{ PURCHASE_REQUISITIONS : requests
    PURCHASE_REQUISITIONS ||--o{ PR_ITEMS : contains
    PURCHASE_REQUISITIONS ||--o{ APPROVAL_WORKFLOWS : governed_by
    APPROVAL_WORKFLOWS ||--o{ APPROVAL_STEPS : consists_of
    
    PURCHASE_REQUISITIONS ||--o{ PURCHASE_ORDERS : originates
    PURCHASE_ORDERS ||--o{ PO_ITEMS : contains
    VENDORS ||--o{ PURCHASE_ORDERS : fulfills
    
    PURCHASE_ORDERS ||--o{ DELIVERIES : ships
    DELIVERIES ||--o{ INSPECTION_REPORTS : inspected_in
    DELIVERIES ||--o{ GOODS_RECEIPTS : logged_as
    
    PURCHASE_ORDERS ||--o{ VENDOR_INVOICES : billed_by
    GOODS_RECEIPTS ||--o{ THREE_WAY_MATCHING : matched_with
    VENDOR_INVOICES ||--o{ THREE_WAY_MATCHING : verified_in
    
    ASSETS ||--o{ ASSET_ASSIGNMENTS : assigned_to
    ASSETS ||--o{ ASSET_INCIDENTS : suffers
    USERS ||--o{ OFFBOARDING_TASKS : completes
```

### 3.1 Domain Breakdown

#### 1. Identity & Access Management (RBAC) (`src/models/auth.py`)
- `users`: User profiles with `employee_code`, `email`, `department_id`, `designation_id`, `manager_id`, `employee_type` (Full-Time, Contractor, Intern), and status.
- `roles`: Role definitions (`Employee`, `Manager`, `Department Head`, `Procurement Officer`, `Finance Manager`, `CFO`, `CEO`, `Admin`, `Vendor`).
- `permissions`: Granular permission flags (e.g., `expense:create`, `pr:approve`, `payment:authorize`).
- `user_roles` & `role_permissions`: Association tables enforcing RBAC mapping.
- `login_sessions`, `login_history`, `refresh_tokens`, `otp_requests`: Authentication security, MFA, and token lifecycle.

#### 2. Organization Structure (`src/models/organization.py`)
- `departments`: Department entity with unique department codes.
- `designations`: Corporate job roles and seniority hierarchy.
- `cost_centres`: Financial allocation units.
- `budget_codes`: Accounting line codes for expense and procurement tracking.
- `org_settings`: Global organizational thresholds (approval limits, currency, fiscal year).

#### 3. Expense Management (`src/models/expense.py`)
- `expense_reports`: Header record with `employee_id`, `purpose`, `justification`, `total_amount`, `status` (`Draft`, `Submitted`, `Pending Manager Approval`, `Pending Finance Approval`, `Approved`, `Payment Authorized`, `Paid`, `Rejected`), `payment_status`, `payment_reference`.
- `receipts`: Line-level receipts containing OCR scanned fields (`merchant_name`, `receipt_date`, `receipt_number`, `category`, `ocr_amount`, `verified_amount`, `tax`, `ocr_confidence`, `image_path`).
- `expense_approvals`: Multi-tier approval step records with approver ID, timestamp, decision, and comments.

#### 4. Procurement & Requisitions (`src/models/purchase_requisition.py`)
- `purchase_requisitions`: Requisition record (`pr_number`, `requestor_id`, `department_id`, `total_estimated_amount`, `justification`, `status`, `is_inventory_allocation`, `allocated_asset_id`).
- `pr_items`: Requisition item details (`item_name`, `description`, `quantity`, `estimated_unit_price`, `total_price`, `category`).
- `pr_attachments`: Attached vendor quotes, specifications, or requirement documents.

#### 5. Multi-Tier Approval Workflow Engine (`src/models/approval.py`)
- `approval_matrices`: Configurable matrix defining approval thresholds based on Department, Cost Center, Amount Range, and Approver Role.
- `approval_workflows`: Workflow tracking parent entity with strict exclusive parent ownership constraint:
  $$\text{claim\_id} \oplus \text{pr\_id} \oplus \text{po\_id} \oplus \text{invoice\_id} = 1$$
- `approval_steps`: Individual tier steps (`step_order`, `approver_id`, `role_id`, `status`, `comments`, `actioned_at`).
- `workflow_history`, `approval_history`, `approval_comments`: Complete immutable audit history.

#### 6. Vendor & Sourcing Management (`src/models/vendor.py`, `src/models/rfq.py`, `src/models/quotation.py`)
- `vendors`: Supplier directory (`vendor_code`, `vendor_name`, `tax_id`, `rating`, `payment_terms`, `is_blacklisted`).
- `vendor_contacts`, `vendor_documents`, `vendor_blacklists`: Vendor compliance, documents, and disciplinary records.
- `request_for_quotations` (RFQ): Sourcing requests created from PRs.
- `rfq_items` & `rfq_vendors`: Targeted lines and invited vendors.
- `vendor_quotations` & `quotation_items`: Submitted supplier bids.
- `quotation_comparisons`: Evaluation and selection matrix.

#### 7. Purchase Orders & Contracts (`src/models/purchase_order.py`, `src/models/contract.py`)
- `purchase_orders`: Official legal PO documents issued to vendors (`po_number`, `vendor_id`, `pr_id`, `total_amount`, `status`, `payment_terms`).
- `purchase_order_items`: Line items with unit pricing and committed quantities.
- `contracts`, `subscription_contracts`, `amc_contracts`, `rate_contracts`: Vendor SLA and service agreements.

#### 8. Logistics, Deliveries, Inspections & GRN (`src/models/delivery.py`, `src/models/inspection.py`, `src/models/grn.py`)
- `deliveries` & `delivery_items`: Shipment tracking and tracking numbers.
- `inspection_reports` & `inspection_items`: Quality control records (`passed_quantity`, `rejected_quantity`, `defect_reason`).
- `goods_receipts` & `goods_receipt_items`: GRN warehouse ledger confirming received inventory.

#### 9. Asset Inventory & Incident Tracking (`src/models/assets.py`, `src/models/offboarding.py`)
- `asset_categories`: Asset taxonomy (e.g., Laptops, Monitors, Machinery, Vehicles).
- `assets`: Asset master record (`asset_tag`, `serial_number`, `purchase_cost`, `current_value`, `status`: `Available`, `Assigned`, `Under Maintenance`, `Decommissioned`).
- `asset_assignments`: Assignment ledger tracking employee custody, check-out, and check-in dates.
- `asset_incidents`: Incident claims reported by employees (`incident_type`: `Damaged`, `Lost`, `Stolen`, `Performance Issue`, `action`: `Repair`, `Replace`, `Dispose`, `status`).
- `offboarding_tasks`: Separation checklists ensuring 100% asset recovery before final clearance.

#### 10. Accounts Payable, 3-Way Matching & Invoicing (`src/models/invoice.py`, `src/models/matching.py`, `src/models/payments.py`)
- `vendor_invoices` & `invoice_items`: Invoices received from vendors.
- `three_way_matching`: Algorithmic reconciliation between PO, GRN, and Invoice with discrepancy status (`Matched`, `Quantity Mismatch`, `Price Mismatch`, `Tolerance Exceeded`).
- `payment_requests` & `payment_approvals`: Payment release authorizations with CFO / Finance Manager sign-offs.

#### 11. Platform Services & Governance (`src/models/platform_services.py`)
- `audit_logs`: Immutable security log capturing every user action, IP, timestamp, and payload changes.
- `activity_logs`: Entity-level user activity streams.
- `notifications` & `notification_preferences`: In-app bell alerts and email notifications.
- `reports` & `scheduled_reports`: BI exports and automated analytics generation.
- `system_health` & `system_metrics`: Uptime, DB latency, and background worker monitoring.
- `system_settings`: Key-value runtime configuration parameters.

---

## 4. End-to-End Business Workflows & State Machines

### 4.1 Expense Claim Lifecycle

```
[Employee creates Draft]
       │
       ▼
[Upload Receipts & Run OCR] ──► OCR parses Amount, Merchant, Category, Date
       │
       ▼
[Submit Expense Report] ──► Validates justification & receipt existence
       │
       ▼
[Manager Approval] ──► If Total <= Threshold ($1,000)
       │                        │
       ├────────────────────────┘
       ▼
[Finance Manager Approval] ──► If Total > $1,000 or Executive claim
       │
       ▼
[CFO / Payment Authorization] ──► Exclusive to Finance Manager / CFO
       │
       ▼
[Disbursement & Mark Paid] ──► Final status: "Paid" (with transaction reference)
```

### 4.2 Purchase Requisition to Procurement & Fulfillment

```
[Employee submits PR]
       │
       ▼
[Check Inventory] ──► If asset in stock: Allocate directly from Inventory
       │
       ▼ (If Purchase needed)
[Multi-Tier PR Approval Matrix]
       │
       ▼
[Procurement Officer creates RFQ] ──► Invite Approved Vendors
       │
       ▼
[Vendors Submit Quotations] ──► Automatic Comparison Matrix & Vendor Scoring
       │
       ▼
[Award Quotation & Issue PO] ──► Transmitted to Vendor
       │
       ▼
[Vendor Ships Items] ──► Delivery Recorded
       │
       ▼
[QA Quality Inspection] ──► Pass / Reject Items
       │
       ▼
[Generate Goods Receipt Note (GRN)] ──► Assets Tagged in Asset Inventory
       │
       ▼
[Vendor Submits Invoice]
       │
       ▼
[Automated 3-Way Match] (PO Line Items == GRN Received Qty == Invoice Billed Amount)
       │
       ▼
[Payment Release & Procurement Closure]
```

### 4.3 Asset Incident & Replacement Workflow

```
[Employee Reports Asset Incident] (e.g. Broken Laptop Screen)
       │
       ▼
[IT / Asset Manager Reviews Incident]
       │
       ├──► (If Repairable): Assign to IT Tech / Vendor Maintenance ──► Asset restored to "Assigned"
       │
       └──► (If Replacement Needed):
                │
                ├──► In-Stock Replacement: Issue spare asset instantly
                │
                └──► Out-of-Stock: Auto-generate Purchase Requisition for new asset
```

---

## 5. API Surface & Route Catalog

The FastAPI application mounts routers under `/api/v1` and core utility routes:

| Router / Tag | Prefix | Primary Responsibilities |
|---|---|---|
| **Health & Ready** | `/health`, `/ready` | Service liveness, readiness probe, DB latency check |
| **Auth** | `/api/v1/auth` | Login, Logout, Supabase Auth sync, MFA OTP, Token refresh, Password reset |
| **Users** | `/api/v1/users` | User CRUD, role assignments, department linking, employee profile |
| **Roles & Permissions** | `/api/v1/roles`, `/api/v1/permissions` | RBAC role definitions and permission mapping |
| **Organization** | `/api/v1/departments`, `/api/v1/designations`, `/api/v1/cost-centres`, `/api/v1/budget-codes`, `/api/v1/org-settings` | Organizational metadata, hierarchy, cost centers |
| **Expenses** | `/api/v1/expenses` | Expense reports CRUD, receipt upload & OCR extraction, submit, approve, reject, authorize payment, payout |
| **Approvals Inbox** | `/api/v1/approvals/inbox` | Unified cross-module approvals (Expenses, PRs, POs, Invoices, Assets) |
| **Purchase Requisitions** | `/api/v1/purchase-requisitions` | PR creation, line items, attachments, workflow submission, department filter |
| **Vendors** | `/api/v1/vendors` | Vendor directory, compliance documents, rating, blacklisting |
| **RFQ & Quotations** | `/api/v1/rfq`, `/api/v1/quotations` | RFQ dispatch, vendor bids submission, comparison matrix |
| **Purchase Orders** | `/api/v1/purchase-orders` | PO generation, approvals, PDF export, status management |
| **Deliveries & GRN** | `/api/v1/deliveries`, `/api/v1/grn` | Shipment records, QA inspections, warehouse receipt ledger |
| **Assets & Incidents** | `/api/v1/assets`, `/api/v1/asset-incidents` | Asset registry, check-in/out, incident logging, repair/replace approval |
| **Offboarding** | `/api/v1/offboarding` | Employee separation checklists, asset reclamation |
| **Invoices & Matching** | `/api/v1/invoices` | Vendor invoice processing, 3-way matching engine, payment requests |
| **Analytics & Reports** | `/api/v1/analytics`, `/api/v1/reports`, `/api/v1/dashboard` | Executive KPIs, spend analytics, scheduled CSV/PDF exports |
| **Platform Services** | `/api/v1/notifications`, `/api/v1/audit`, `/api/v1/search`, `/api/v1/monitoring`, `/api/v1/settings` | Notification stream, security audit trails, elastic search, system health |

---

## 6. Role-Based Access Control (RBAC) Matrix

| Module / Feature | Employee | Manager | Procurement Officer | Finance Manager | CFO / CEO | Admin |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Create Expense Claim** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Approve Dept Expenses** | ❌ | ✅ | ❌ | ✅ | ✅ | ✅ |
| **Authorize Expense Payout** | ❌ | ❌ | ❌ | ✅ | ✅ (CFO) | ❌ |
| **Create Purchase Requisition** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Approve PRs** | ❌ | ✅ (Tier 1) | ❌ | ✅ (Tier 2) | ✅ (Tier 3) | ✅ |
| **Manage RFQs & Issue POs** | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ |
| **Vendor Blacklisting & KYC** | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ |
| **Inspect Goods & Issue GRN** | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ |
| **Asset Registry & Tagging** | View Mine | View Team | ✅ | ✅ | ✅ | ✅ |
| **Report Asset Incident** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Approve Asset Replacement** | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ |
| **3-Way Match Reconciliation** | ❌ | ❌ | View | ✅ | ✅ | ✅ |
| **Disburse Payments** | ❌ | ❌ | ❌ | ✅ | ✅ (CFO) | ❌ |
| **User & Role Management** | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Security Audit Logs** | ❌ | ❌ | ❌ | ❌ | View | ✅ |

---

## 7. Frontend Application Architecture

### 7.1 Directory Layout (`frontend/src/`)
```
frontend/src/
├── App.tsx                     # Top-level Router, ThemeProvider & AuthProvider wrapper
├── index.css                   # Tailwind styles, color tokens, animations & toast positioning
├── main.tsx                    # React DOM entrypoint
├── components/
│   ├── ErrorBoundary.tsx       # React lifecycle error boundary
│   ├── ui.tsx                  # Core atomic UI library (Buttons, Cards, Inputs, Modals, Badges)
│   ├── ui/TypewriterText.tsx   # Premium interactive text animation for popups
│   └── expenses/               # Expense-specific subcomponents & OCR previewer
├── hooks/
│   ├── useAuth.tsx             # Authentication context, login, logout, token refresh
│   ├── usePermissions.ts       # RBAC permission evaluation helper hook
│   └── useTheme.tsx            # Dark/Light theme switcher state
├── layouts/
│   └── DashboardLayout.tsx     # Enterprise Sidebar, Header, Notification Bell, User Menu
├── pages/                      # 22 High-fidelity views
│   ├── Analytics.tsx           # Spend charts, ROI graphs, monthly trend forecasts
│   ├── Approvals.tsx           # Multi-entity unified approval inbox with filters
│   ├── Assets.tsx              # Corporate Asset Inventory & Category hierarchy
│   ├── AuditLogs.tsx           # System activity and security audit trail viewer
│   ├── Contracts.tsx           # Vendor contract & SLA management
│   ├── Dashboard.tsx           # Main executive role-based dashboard
│   ├── Deliveries.tsx          # Logistics shipment tracking
│   ├── DeliveredItems.tsx      # Line item receiving list
│   ├── Expenses.tsx            # Expense claims, OCR upload modal, receipt manager
│   ├── GlobalSearch.tsx        # Omni-search for PRs, POs, Assets, Users, Invoices
│   ├── GRNs.tsx                # Goods Receipt Notes management
│   ├── Invoices.tsx            # Vendor Invoices & 3-way matching console
│   ├── Login.tsx               # Login with MFA OTP & Google SSO
│   ├── MyAssets.tsx            # Employee personal asset custody & incident reporter
│   ├── ProcurementDashboard.tsx# Sourcing KPI console
│   ├── PurchaseOrders.tsx      # PO management, approvals & printouts
│   ├── PurchaseRequisitions.tsx# PR submission, department requisitions, inventory check
│   ├── Quotations.tsx          # RFQ bidding comparison matrix
│   ├── RFQs.tsx                # RFQ creation & dispatch
│   ├── Reports.tsx             # Exportable operational & financial reports
│   ├── Settings.tsx            # User profile & organization preferences
│   ├── SystemHealth.tsx        # Uptime, API metrics, and database connection status
│   ├── Users.tsx               # User management, role assignment, department tagging
│   └── VendorPortal.tsx        # Dedicated portal for external suppliers
├── routes/
│   └── AppRoutes.tsx           # Declarative HashRouter routes with RBAC guards
├── services/
│   └── api.ts                  # Central Axios client with interceptors
└── types/
    └── index.ts                # TypeScript interface and type declarations
```

---

## 8. Development, Testing & Verification

### 8.1 Backend Test Suite (Pytest)
The test suite consists of **85 comprehensive integration and unit tests** across all modules:
- `tests/test_startup.py`: FastAPI initialization, middleware verification
- `tests/test_database_connection.py`: Database health probes and degraded recovery
- `tests/test_auth.py`: Authentication, JWT generation, password hashing, RBAC enforcement
- `tests/test_expense_workflow.py`: Expense lifecycle, multi-tier approvals, policy validation
- `tests/test_expense_approval_wildcard.py`: Enforces explicit approver assignment (wildcard approval prevention)
- `tests/test_expense_workflow_history.py`: Verification of isolated expense approval histories
- `tests/test_pr.py`: Purchase Requisitions, line item calculations, inventory allocation
- `tests/test_pr_workflow_history_isolation.py`: Workflow history relationship scope isolation
- `tests/test_approval_matrix.py`: Approval matrix hierarchy calculations
- `tests/test_approval_workflow_constraint.py`: Exclusive parent constraint verification ($= 1$)
- `tests/test_procurement.py`: RFQ, Quotations, POs, Vendor blacklisting, contracts
- `tests/test_asset_incidents.py`: Asset incident logging, repair/replace approvals
- `tests/test_offboarding_workflow.py`: Employee separation and asset reclamation
- `tests/test_phase6_platform.py`: Platform monitoring, search, notifications, audit logging
- `tests/test_tesseract_service.py`: Tesseract OCR extraction parsing

**Run all tests**:
```bash
PYTHONPATH=. ./venv/bin/pytest
```
*Current Status*: **85 passed, 0 failures**.

### 8.2 Frontend Production Build
The frontend compiles with Vite and strict TypeScript type-checking:
```bash
npm --prefix frontend run build
```
*Current Status*: **Clean build with 0 TypeScript / compilation errors**.

---

## 9. Environment Variables Configuration

| Variable | Description | Default / Example |
|---|---|---|
| `ENVIRONMENT` | Application running mode | `development` / `production` |
| `LOG_LEVEL` | Logging verbosity | `INFO` / `DEBUG` |
| `DATABASE_URL` | SQLAlchemy async connection URI | `postgresql+asyncpg://user:pass@host:5432/dbname` |
| `SUPABASE_URL` | Supabase project endpoint | `https://your-project.supabase.co` |
| `SUPABASE_KEY` | Supabase anonymous / service key | `ey...` |
| `JWT_SECRET` | Secret key for local JWT signatures | `your-secure-jwt-secret` |
| `AWS_REGION` | AWS region for cloud services | `us-east-1` |
| `AWS_ACCESS_KEY_ID` | AWS IAM Access Key for Textract / S3 | `AKIA...` |
| `AWS_SECRET_ACCESS_KEY` | AWS IAM Secret Key | `...` |
| `TESSERACT_CMD` | Binary path for local Tesseract OCR | `/opt/homebrew/bin/tesseract` or `tesseract` |
| `REDIS_URL` | Redis caching connection URL (optional) | `redis://localhost:6379/0` |

---

## 10. Summary of Architectural Integrity & Health Checks

- ✅ **Database Schema Integrity**: Cross-database ANSI SQL constraints guarantee zero orphaned workflow records and clean multi-dialect execution (PostgreSQL & SQLite).
- ✅ **Security & Permissions**: Strict role segregation prevents privilege escalation (e.g., payment authorizations restricted strictly to CFO/Finance Manager; PR approvals isolated by department).
- ✅ **Automated OCR Resiliency**: Fallback OCR pipelines gracefully handle various image formats (PNG, JPEG, PDF) and normalize monetary amounts.
- ✅ **Production-Ready Frontend**: HashRouter configuration ensures zero 404s on hard page refreshes across static deployments, coupled with dynamic responsive UI styling.
