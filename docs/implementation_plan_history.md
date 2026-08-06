# Enterprise Expense & Procurement Workflow Platform
## Implementation Plan History: Phase 1 to Present

This document outlines the detailed architectural blueprints and database schemas implemented from Phase 1 through the current state.

---

### **Phase 1: Enterprise Identity & Organization Foundation**
Established the core administrative structure, user management, and organizational hierarchy.

*   **Database Schema**:
    *   `designations`: Tracks employee levels and titles (`designation_id`, `designation_name`, `description`).
    *   `departments`: Standardizes structural divisions (`department_id`, `department_code`, `department_name`, `manager_id`, `parent_department_id`).
    *   `cost_centres`: Manages financial budgets (`cost_centre_id`, `cost_centre_code`, `cost_centre_name`, `manager_id`, `budget_limit`, `spent_amount`).
    *   `users`: Core personnel information (`user_id`, `email`, `hashed_password`, `full_name`, `role_id`, `department_id`, `designation_id`, `is_active`).
    *   `roles` & `user_roles`: RBAC (Role-Based Access Control) definition.
    *   `permissions` & `role_permissions`: Granular endpoint action allowances.
    *   `login_sessions`: Monitored active logins (`session_id`, `user_id`, `ip_address`, `user_agent`, `logged_in_at`, `expires_at`).
    *   `organization_settings`: Configuration variables like currencies, thresholds, compliance rules, etc.
    *   `login_history` & `refresh_tokens`: Token lifecycle storage.

*   **Backend Features**:
    *   FastAPI setup with ASGI middleware configuration.
    *   SQLAlchemy 2.0 Async Session management (`get_db_session` dependency).
    *   CORS, exception handling, custom request logs, and security headers middlewares.

---

### **Phase 2: Purchase Requisition (PR) Lifecycle & Budgeting**
Introduced the core flow of creating, routing, and approving financial procurement request documents.

*   **Database Schema**:
    *   `purchase_requisitions`: Enhanced with status, priority, requestor, department, total amount, currency, and purchase type.
    *   `pr_items`: Line items listing specific quantities, unit prices, cost centers, and budget codes.
    *   `budget_codes`: Code mappings representing expense classifications.
    *   `budget_allocations`: Tracks allocated budget, reserved funds (pre-encumbrances), and actual spent amounts per fiscal year.
    *   `budget_reservations`: Tracks budget reserves created during PR submission to prevent overspending.
    *   `approval_matrix`: Defines approval routing requirements depending on cost centers and transaction value.
    *   `approval_workflows` & `approval_steps`: Sequential multi-step workflows.
    *   `workflow_history` & `approval_history`: Historical log of comments, rejections, delegations, and approvals.
    *   `pr_attachments`: Document uploads containing specs or justifications.

*   **Backend Features**:
    *   PR creation validation checking line totals against remaining unreserved budget allocations.
    *   Dynamic routing of approval steps based on the department thresholds in `approval_matrix`.

---

### **Phase 3: Procurement & Vendor Lifecycle**
Facilitated sourcing, RFQ bidding, vendor onboarding, quotation comparison, and formal Purchase Order issuance.

*   **Database Schema**:
    *   `vendors`: Profile tracking tax IDs, trade names, risk scores, status, and compliance flags.
    *   `vendor_contacts` & `vendor_documents`: Key contact persons and certificate uploads (e.g., ISO, tax).
    *   `vendor_blacklist`: Tracks blocked/banned vendors with reasons and dates.
    *   `request_for_quotations` (RFQ) & `rfq_items`: Sourcing events linking PRs to one or more invited vendors.
    *   `vendor_quotations` & `quotation_items`: Bids submitted by vendors.
    *   `quotation_comparison`: Bidding evaluation matrix with selection justifications.
    *   `purchase_orders` (PO) & `purchase_order_items`: Confirmed purchasing documents auto-generated from selected quotations.
    *   `contracts` & `contract_documents`: Formal binding agreements.
    *   `subscription_contracts`, `amc_contracts`, `rate_contracts`: Specialized contract structures.

---

### **Phase 4: Procure-to-Pay (P2P) Delivery & Asset Management**
Completed the operational loop from delivery check, invoice verification, three-way matching, and asset creation.

*   **Database Schema**:
    *   `deliveries` & `delivery_items`: Dispatched shipment logs.
    *   `inspection_reports` & `inspection_items`: Inspection records tracking accepted/rejected quantities.
    *   `goods_receipts` (GRN) & `goods_receipt_items`: Confirmed warehouse reception logs.
    *   `asset_categories` & `assets`: IT/physical hardware logs tracked from GRNs (`depreciation_rate`, `purchase_price`).
    *   `asset_assignments` & `asset_history` & `asset_documents`: Allocation tracking.
    *   `vendor_invoices` & `invoice_items`: Surcharges billed by vendors against POs and GRNs.
    *   `three_way_matching`: Automated reconciliation comparing PO, GRN, and Invoice values to calculate variances.
    *   `payment_requests` & `payment_approvals`: Payment processing workflows.
    *   `procurement_closure`: Finalized status flags marking sourcing events complete.

---

### **Phase 5: Platform Services & System Probes**
Built out system-level automation infrastructure for search, background jobs, caching, and logs.

*   **Database Schema**:
    *   `notification_templates` & `notifications`: Multi-channel system prompts.
    *   `email_templates` & `email_logs`: SMTP queue and email dispatcher records.
    *   `audit_logs`: Detailed immutable tracking of all security-sensitive actions.
    *   `system_settings`: Key-value registry for system properties.
    *   `dashboard_caches`: Pre-calculated metrics to minimize database read overhead.
    *   `search_indexes`: Full-text indexes.
    *   `scheduled_jobs` & `job_execution_logs`: Background job registry.

*   **Backend Features**:
    *   Memory Cache fallback layer when Redis is unavailable.
    *   Rotating log files under `logs/app.log`.
    *   Background scheduler thread executing periodic maintenance and database statistics updates.

---

### **Phase 6: Advanced Identity & Third-Party Authentication**
Extended security and login patterns to support external auth profiles and vendor verification.

*   **Database Schema Updates**:
    *   `users`: Added `google_id` and `avatar_url` to support Google OAuth 2.0 logins.
    *   `vendors`: Added `otp_secret`, `otp_secret_expires_at`, `email_verified`, and `phone_verified` for secure OTP-based access.

---

### **Technology Stack Configuration**
*   **Backend**: FastAPI, SQLAlchemy 2.0 Async, Alembic, Pydantic v2.
*   **Database**: Supabase PostgreSQL.
*   **Frontend**: React (V19.0.0), TypeScript, TailwindCSS, Axios, Vite (acting as a proxy router to backend `/api/v1` on port `8001`).
