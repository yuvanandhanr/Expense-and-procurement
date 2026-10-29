# Enterprise Expense & Procurement Workflow Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-19.0-61DAFB.svg?style=flat-square&logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.3-3178C6.svg?style=flat-square&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Vite](https://img.shields.io/badge/Vite-5.0-646CFF.svg?style=flat-square&logo=vite&logoColor=white)](https://vitejs.dev/)
[![Tailwind CSS](https://img.shields.io/badge/TailwindCSS-3.4-38B2AC.svg?style=flat-square&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0_(Async)-D71F00.svg?style=flat-square&logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![PostgreSQL](https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E.svg?style=flat-square&logo=supabase&logoColor=white)](https://supabase.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com/)
[![Render](https://img.shields.io/badge/Deployed-Render-46E3B7.svg?style=flat-square&logo=render&logoColor=black)](https://render.com/)

> **A mission-critical, enterprise-grade Procure-to-Pay (P2P), Intelligent Expense Claim Management, Asset Lifecycle Tracking, and Multi-Tier Approval Orchestration Platform built on Clean Architecture and Domain-Driven Design (DDD) principles.**

---

## 📑 Table of Contents

- [1. Executive Overview](#1-executive-overview)
- [2. System Architecture & Solution Design](#2-system-architecture--solution-design)
  - [2.1 High-Level Architecture Diagram](#21-high-level-architecture-diagram)
  - [2.2 End-to-End Procure-to-Pay (P2P) Lifecycle](#22-end-to-end-procure-to-pay-p2p-lifecycle)
  - [2.3 Intelligent Expense Claim & OCR Extraction Flow](#23-intelligent-expense-claim--ocr-extraction-flow)
  - [2.4 Asset Lifecycle & Offboarding Recovery Flow](#24-asset-lifecycle--offboarding-recovery-flow)
- [3. Core Domain Capabilities & Feature Matrix](#3-core-domain-capabilities--feature-matrix)
- [4. Complete Technology Stack & Packages](#4-complete-technology-stack--packages)
  - [4.1 Backend Engine](#41-backend-engine)
  - [4.2 Frontend SPA](#42-frontend-spa)
  - [4.3 Database, Cloud Services & DevOps](#43-database-cloud-services--devops)
- [5. System Prerequisites](#5-system-prerequisites)
- [6. Step-by-Step Installation & Local Setup Guide](#6-step-by-step-installation--local-setup-guide)
  - [6.1 Repository Setup](#61-repository-setup)
  - [6.2 Backend Installation & Configuration](#62-backend-installation--configuration)
  - [6.3 Frontend Installation & Configuration](#63-frontend-installation--configuration)
  - [6.4 OCR Engine Installation (Tesseract)](#64-ocr-engine-installation-tesseract)
  - [6.5 Database Migrations & Initial Seed Data](#65-database-migrations--initial-seed-data)
  - [6.6 Running the Development Environment](#66-running-the-development-environment)
- [7. Environment Variables Reference](#7-environment-variables-reference)
  - [7.1 Backend Environment Configuration (`.env`)](#71-backend-environment-configuration-env)
  - [7.2 Frontend Environment Configuration (`frontend/.env`)](#72-frontend-environment-configuration-frontendenv)
- [8. Production Deployment Guide (Render & Cloud)](#8-production-deployment-guide-render--cloud)
  - [8.1 Production Architecture Topology](#81-production-architecture-topology)
  - [8.2 Backend Service Configuration (Docker Web Service)](#82-backend-service-configuration-docker-web-service)
  - [8.3 Frontend Service Configuration (Static Site)](#83-frontend-service-configuration-static-site)
  - [8.4 Supabase Connection Pooling Best Practices](#84-supabase-connection-pooling-best-practices)
- [9. REST API Directory & Interactive Documentation](#9-rest-api-directory--interactive-documentation)
- [10. Security, Middleware Pipeline & Observability](#10-security-middleware-pipeline--observability)
- [11. Testing, Code Quality & Verification](#11-testing-code-quality--verification)
- [12. Clean Directory Layout](#12-clean-directory-layout)
- [13. Troubleshooting & Operations FAQ](#13-troubleshooting--operations-faq)
- [14. License & Support](#14-license--support)

---

## 1. Executive Overview

Modern enterprises face significant operational friction across procurement and financial governance: fragmented expense receipts, out-of-policy purchasing, slow paper-based approval matrices, vendor billing discrepancies, and unmanaged IT asset leakage.

The **Enterprise Expense & Procurement Workflow Platform** delivers an all-in-one, auditable, high-throughput solution that harmonizes:

1. **Procure-to-Pay (P2P) Governance**: Unified purchase requisitions (PR) backed by automated budget reservation, RFQ dispatch, side-by-side vendor quotation scoring, purchase order (PO) generation, goods receipt note (GRN) quality inspection, automated 3-way matching (PO vs. GRN vs. Invoice), and disbursement.
2. **Intelligent Expense Management**: Multi-currency employee expense reporting with integrated optical character recognition (OCR powered by Tesseract and AWS Textract fallback), real-time policy limit checking, duplicate receipt detection, and instant manager/finance approvals.
3. **Asset Lifecycle & Offboarding Recovery**: Centralized asset tracking (hardware, laptops, licenses), barcode/serial registration, employee asset checkout ("My Assets"), incident/damage reporting, inventory pre-allocation checks before requisitions, and automated offboarding asset clearance checklists.
4. **Adaptive Hierarchical Approval Engine**: Flexible matrix-driven approval pipelines based on departmental hierarchies, custom dollar thresholds, and designated roles (Manager, Finance, CFO, CEO) with delegation and unified inbox views.
5. **Real-time Observability & Analytics**: Interactive executive dashboards, department spend distribution, budget burn-rate tracking, scheduled Excel/PDF export pipelines, and immutable audit logs.

---

## 2. System Architecture & Solution Design

The system implements **Clean Architecture** and **Domain-Driven Design (DDD)**. Dependencies flow strictly inward: business domain services remain decoupled from database implementations, HTTP routers, and external third-party integrations.

### 2.1 High-Level Architecture Diagram

```mermaid
graph TB
    subgraph Client Tier
        UI[React 19 / TypeScript SPA]
        VP[Vendor Portal SPA]
        Mob[Mobile / Browser Clients]
    end

    subgraph Security & Edge Layer
        CDN[Render CDN & Edge Cache]
        Proxy[Render Reverse Proxy / HTTPS]
        MW_CORS[CORS & Trusted Host Policy]
        MW_SEC[Security Headers CSP / HSTS / Frame-Options]
        MW_REQ[X-Request-ID Context Tracing]
        MW_LOG[Structured JSON Access Logging]
        MW_EXC[Global Exception Shield]
        MW_GZIP[GZip Compression Engine]
    end

    subgraph Application Service Layer FastAPI ASGI
        Router[FastAPI API Routers /api/v1]
        AuthServ[Auth & RBAC Service Argon2 / JWT / TOTP]
        PRServ[Requisition & Budget Encumbrance Service]
        ApprServ[Hierarchical Approval Engine & Inbox]
        RFQServ[RFQ & Quotation Evaluation Engine]
        POServ[Purchase Order & Contract Service]
        GRNServ[Delivery, Quality Inspection & GRN]
        MatchServ[Three-Way Matching PO-GRN-Invoice]
        ExpServ[Expense & OCR Processing Service]
        AssetServ[Asset Lifecycle & Offboarding Service]
        DashServ[Executive Analytics & Reports Service]
        JobSched[Background Scheduler Loop Asyncio]
    end

    subgraph Data & Integration Layer
        SupaPool[Supabase PostgreSQL Connection Pooler]
        DB[(PostgreSQL Primary Database)]
        Cache[Redis / Memory Cache Fallback]
        Tess[Tesseract OCR Engine / OCR Worker]
        AWS_Text[AWS Textract Cloud OCR Fallback]
        DiskStore[Local Uploads / S3 Document Store]
        SMTP[SMTP Email Notification Dispatcher]
    end

    UI --> Proxy
    VP --> Proxy
    Mob --> Proxy

    Proxy --> CDN
    CDN --> MW_CORS
    MW_CORS --> MW_SEC
    MW_SEC --> MW_REQ
    MW_REQ --> MW_LOG
    MW_LOG --> MW_EXC
    MW_EXC --> MW_GZIP
    MW_GZIP --> Router

    Router --> AuthServ
    Router --> PRServ
    Router --> ApprServ
    Router --> RFQServ
    Router --> POSServ
    Router --> GRNServ
    Router --> MatchServ
    Router --> ExpServ
    Router --> AssetServ
    Router --> DashServ

    JobSched -.-> DashServ
    JobSched -.-> ApprServ

    AuthServ --> SupaPool
    PRServ --> SupaPool
    ApprServ --> SupaPool
    POServ --> SupaPool
    GRNServ --> SupaPool
    MatchServ --> SupaPool
    AssetServ --> SupaPool

    SupaPool --> DB
    DashServ --> Cache
    ExpServ --> Tess
    ExpServ -.-> AWS_Text
    GRNServ --> DiskStore
    ExpServ --> DiskStore
    ApprServ --> SMTP
```

---

### 2.2 End-to-End Procure-to-Pay (P2P) Lifecycle

The diagram below details the operational stages through which every procurement requisition moves, starting from initial request to reconciliation and financial settlement:

```mermaid
sequenceDiagram
    autonumber
    actor Employee as Employee / Requester
    participant PR as PR & Budget Engine
    participant Appr as Approval Matrix Engine
    participant Sourcing as Sourcing & RFQ Engine
    actor Vendor as External Vendor
    participant WH as Warehouse / Inspection
    participant AP as Accounts Payable / 3-Way Match
    participant Fin as Finance & Payment

    Employee->>PR: 1. Create Purchase Requisition (PR)
    PR->>PR: 2. Verify Available Departmental Budget
    alt Budget Exceeded
        PR-->>Employee: Reject Requisition (Insufficient Budget)
    else Budget Confirmed
        PR->>PR: Encumber & Hold Budget Amount
        PR->>Appr: 3. Submit to Multi-Tier Approval Chain
        Appr->>Appr: Evaluate Thresholds (Manager -> Finance -> CFO)
        Appr-->>Employee: PR Formally Approved
        Appr->>Sourcing: 4. Transition to Sourcing Phase
        Sourcing->>Vendor: 5. Issue RFQ to Qualified Vendors
        Vendor->>Sourcing: 6. Submit Quotations & Pricing Bids
        Sourcing->>Sourcing: 7. Side-by-Side Evaluation & Scoring
        Sourcing->>Fin: 8. Award Winning Bid & Generate Purchase Order (PO)
        Fin->>Vendor: 9. Transmit Final PO
        Vendor->>WH: 10. Deliver Goods & Shipping Manifest
        WH->>WH: 11. Quality Inspection (Accepted vs Rejected Units)
        WH->>WH: 12. Generate Goods Receipt Note (GRN)
        opt Depreciable Capital Asset
            WH->>WH: Auto-Register into Asset Inventory Registry
        end
        Vendor->>AP: 13. Submit Billing Invoice
        AP->>AP: 14. Execute 3-Way Matching (PO vs GRN vs Invoice)
        alt Tolerance Mismatch Discrepancy
            AP-->>AP: Flag Discrepancy & Route to Audit Queue
        else Match Confirmed
            AP->>Fin: 15. Approve for Payment
            Fin->>Vendor: 16. Process Disbursement
            Fin->>PR: 17. Convert Reserved Budget to Expended (Close P2P Cycle)
        end
    end
```

---

### 2.3 Intelligent Expense Claim & OCR Extraction Flow

```mermaid
flowchart TD
    A[Employee Uploads Receipt Image / PDF] --> B[File Validation Size & MIME Type]
    B --> C[Image Preprocessing Pillow Grayscale / Contrast]
    C --> D[Tesseract OCR Engine Text Parsing]
    D -- Failure / Low Confidence --> E[AWS Textract Cloud OCR Fallback]
    D -- Success --> F[Heuristic Regex Extraction Engine]
    E --> F
    F --> G[Extracted Fields: Vendor, Date, Currency, Total, Tax]
    G --> H[Check Expense Policies: Per-Diem, Duplicate Invoice Check]
    H -- Violation --> I[Flag Soft Warning / Require Justification]
    H -- Clear --> J[Create Expense Report]
    I --> J
    J --> K[Submit to Approval Workflow Matrix]
    K --> L{Manager Review}
    L -- Approved --> M{Finance Audit}
    L -- Rejected --> N[Return to Employee with Feedback]
    M -- Approved --> O[Approved for Reimbursement Batch]
    M -- Disputed --> N
    O --> P[Disbursement & General Ledger Export]
```

---

### 2.4 Asset Lifecycle & Offboarding Recovery Flow

```mermaid
flowchart LR
    subgraph Inward Intake
        A[Inward GRN / Procurement PO] --> B[Asset Classification IT / Furniture / License]
        B --> C[Generate Barcode / Asset Tag & Serial]
    end

    subgraph Operational Lifecycle
        C --> D[Asset Inventory Stock Pool]
        D -->|Allocation Request / PR Check| E[Assign to Employee 'My Assets']
        E --> F{Operational Use}
        F -->|Damaged / Faulty| G[Incident / Damage Report]
        G --> H[Maintenance / Vendor Repair]
        H --> E
    end

    subgraph Decommission & Offboarding
        F -->|Resignation / Termination| I[Offboarding Clearance Workflow]
        I --> J[Physical Verification & Custody Return]
        J -->|Restocked| D
        J -->|End of Life| K[Asset Deprecated & Retired]
    end
```

---

## 3. Core Domain Capabilities & Feature Matrix

| Domain Module | Primary Functionality | Key Production Features |
| :--- | :--- | :--- |
| **Identity & Access Management (IAM)** | Authentication, Authorization, RBAC | • Dual-auth: Corporate Google OAuth 2.0 & Email/Password<br>• Passwordless OTP login for external vendors<br>• Time-based One-Time Password (TOTP) 2FA (`pyotp`, `qrcode`)<br>• Argon2id password hashing & Asymmetric JWT tokens<br>• Granular permission enforcement per endpoint |
| **Organization Governance** | Structure & Budgetary Limits | • Hierarchical Departments & Designations<br>• Cost Centres with real-time budget limit tracking<br>• Budget Codes with encumbrance/reservation locks |
| **Purchase Requisitions (PR)** | Demand Initiation & Validation | • Line-item requisition with unit rates, tax, and categories<br>• Automatic check for existing inventory before re-ordering<br>• Real-time budget encumbrance preventing over-allocation<br>• Priority tagging (Urgent, High, Normal, Low) with attachments |
| **Approval Engine & Inbox** | Matrix-Driven Orchestration | • Tiered rules by financial threshold (e.g. >$500 Finance, >$5000 CFO)<br>• Dynamic sequential and parallel approval routing<br>• Unified Approvals Inbox with Quick Approve/Reject/Query<br>• Collaborative audit comments and inquiry threads |
| **RFQ & Sourcing** | Vendor Discovery & Bidding | • Convert approved PRs directly into RFQ packages<br>• Vendor invitation with automated blacklisting suppression<br>• Vendor quotation comparison matrix with side-by-side scoring<br>• Single-click bid awarding and formal PO issuance |
| **Purchase Orders & Deliveries** | Order Fulfillment & Logistics | • Formally formatted PO generation with revision tracking<br>• Multi-stage delivery management (partial & split shipments)<br>• Carrier tracking, bill of lading, and dispatch notes |
| **Quality Inspection & GRN** | Goods Receipt Verification | • Warehouse inspection logging: Accepted vs Damaged units<br>• Photo evidence attachments for damaged packaging<br>• Automatic Goods Receipt Note (GRN) generation<br>• Automatic trigger for asset registration on accepted hardware |
| **Three-Way Matching** | Invoice Reconciliation | • Automated matching engine: PO vs GRN vs Vendor Invoice<br>• Line-by-line verification of quantities, unit rates, and totals<br>• Configurable tolerance limits (percentage and dollar caps)<br>• Discrepancy quarantine queue for Accounts Payable review |
| **Expenses & Intelligent OCR** | Employee Reimbursement | • Multi-currency expense submissions with conversion logic<br>• Integrated Tesseract OCR + AWS Textract cloud fallback<br>• Automated heuristic extraction (Vendor, Date, Amount, Tax)<br>• Duplicate receipt fingerprinting and policy enforcement |
| **Asset Registry & Offboarding** | Complete Hardware Lifecycle | • Centralized asset catalog with serial numbers and warranty dates<br>• Employee self-service asset custody view ("My Assets")<br>• Asset incident and damage reporting with status tracking<br>• Employee offboarding clearance protocol with asset recovery checklist |
| **Executive Dashboards & Analytics** | Strategic Insights & BI | • Real-time spend KPIs, department breakdown, and burn rates<br>• Procurement cycle-time analytics and vendor scorecards<br>• Automated scheduled background reports (`run_scheduler_loop`)<br>• Export engine generating Microsoft Excel (`openpyxl`) and CSV |
| **Platform Telemetry & Audit** | Operational Excellence | • Context-local Request ID tracing (`X-Request-ID`) across logs<br>• Tamper-proof, immutable audit logs with before/after snapshots<br>• Production health and database readiness probes (`/health`, `/ready`) |

---

## 4. Complete Technology Stack & Packages

### 4.1 Backend Engine

| Technology / Package | Version | Architectural Role & Purpose |
| :--- | :--- | :--- |
| **Python** | `3.11+` | Core asynchronous runtime environment. |
| **FastAPI** | `>=0.110.0` | High-performance ASGI web framework providing native OpenAPI and async routing. |
| **Uvicorn (standard)** | `>=0.28.0` | Lightning-fast ASGI web server implementation based on `uvloop` and `httptools`. |
| **Gunicorn** | `>=21.2.0` | Production WSGI/ASGI process manager managing worker concurrency and load-balancing. |
| **SQLAlchemy (Async)** | `>=2.0.28` | Enterprise ORM configured with asynchronous 2.0 query syntax and relationship mapping. |
| **Asyncpg** | `>=0.29.0` | Ultra high-performance asynchronous PostgreSQL driver. |
| **Pydantic & Settings** | `>=2.6.0` | Strict data validation, schema enforcement, and typed environment management. |
| **Alembic** | `>=1.13.1` | Asynchronous database migrations and schema version history control. |
| **Pytesseract** | `>=0.3.13` | Python wrapper for Google Tesseract OCR optical character extraction engine. |
| **Pillow (PIL)** | `>=10.0.0` | Digital image manipulation library used for receipt contrast and grayscale enhancement. |
| **PyJWT [crypto]** | `>=2.8.0` | RFC 7519 JSON Web Token signing, verification, and rotation. |
| **Argon2-cffi** | `>=25.1.0` | State-of-the-art, memory-hard password hashing algorithm (OWASP recommended). |
| **PyOTP** | `>=2.9.0` | Time-based One-Time Password (TOTP) RFC 6238 implementation for two-factor authentication. |
| **QRCode** | `>=7.4.2` | Generation of 2FA QR code matrices for authenticator apps. |
| **Redis** | `>=5.0.0` | High-speed in-memory caching and distributed lock coordination (with local fallback). |
| **OpenPyXL** | `>=3.1.0` | Generation of enterprise-grade Microsoft Excel spreadsheets for executive reports. |
| **Aiofiles** | `>=23.2.1` | Asynchronous non-blocking file system I/O for document uploads. |
| **HTTPX** | `>=0.27.0` | Asynchronous HTTP client for external service interactions. |
| **Pytest & Asyncio** | `>=8.1.0` | Automated testing framework with full async fixture support. |

---

### 4.2 Frontend SPA

| Technology / Package | Version | Architectural Role & Purpose |
| :--- | :--- | :--- |
| **React** | `^19.0.0` | Declarative UI library leveraging latest React Server / Client paradigms. |
| **TypeScript** | `^5.3.0` | Static typing providing end-to-end interface safety. |
| **Vite** | `^5.0.0` | Next-generation frontend build tooling offering sub-second Hot Module Replacement (HMR). |
| **Tailwind CSS** | `^3.4.0` | Utility-first CSS framework for responsive enterprise design systems. |
| **TanStack React Query**| `^5.0.0` | Asynchronous state management, optimistic UI updates, and intelligent caching. |
| **Axios** | `^1.6.0` | Promise-based HTTP client with global JWT request/response interceptors. |
| **Lucide React** | `^0.300.0` | Clean, modern, scalable iconography. |
| **Chart.js & React-Chartjs-2** | `^4.4.0` | Interactive analytical charts, spend distributions, and trend visualizations. |
| **React Hook Form & Zod** | `^7.50.0` | High-performance, schema-validated forms with minimal re-renders. |
| **React Hot Toast** | `^2.4.0` | Lightweight notification toast alerts. |
| **React Dropzone** | `^14.2.0` | Drag-and-drop document and receipt upload interface. |
| **Playwright** | `^1.62.1` | End-to-end browser automation and functional regression testing. |

---

### 4.3 Database, Cloud Services & DevOps

- **Supabase PostgreSQL**: Remote managed PostgreSQL instance accessed via high-capacity connection pooling (`aws-1-ap-south-1.pooler.supabase.com`).
- **Render Cloud**:
  - **Backend**: Containerized Docker Web Service running multi-worker Gunicorn.
  - **Frontend**: High-speed global Static Site serving optimized Vite distribution assets (`dist/`).
- **AWS Cloud (Optional Integration)**: AWS Textract for cloud fallback OCR and AWS S3 for distributed asset storage.

---

## 5. System Prerequisites

Ensure the following environments and utilities are installed on your development workstation or server:

| Tool | Recommended Version | Verification Command | Notes |
| :--- | :--- | :--- | :--- |
| **Python** | `3.11.x` | `python --version` | Ensure `pip` is updated (`python -m pip install --upgrade pip`). |
| **Node.js** | `18.x` or `20.x` LTS | `node -v` | Node 18 or 20 is required for Vite 5. |
| **npm** | `9.x` or `10.x` | `npm -v` | Installed with Node.js. |
| **Tesseract OCR** | `5.x` | `tesseract --version` | Native binary required for local receipt OCR extraction. |
| **Git** | `2.x+` | `git --version` | Version control. |
| **Docker (Optional)**| `24.x+` | `docker --version` | For containerized multi-stage testing. |

---

## 6. Step-by-Step Installation & Local Setup Guide

Follow this guide to configure and launch the backend API and frontend single-page application.

### 6.1 Repository Setup

```bash
# Clone the repository
git clone https://github.com/yuvanandhanr/Expense-and-procurement.git
cd "Expense and Procurement"
```

---

### 6.2 Backend Installation & Configuration

#### Step 1: Create and Activate Virtual Environment

**On Linux / macOS:**
```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

**On Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

#### Step 2: Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### Step 3: Configure Environment Variables

Create your local `.env` file from the provided template:

```bash
cp .env.example .env
```

Edit `.env` and configure your credentials (see [Section 7](#7-environment-variables-reference) for the complete parameter reference). Ensure your remote Supabase connection string is placed in `DATABASE_URL`.

---

### 6.3 Frontend Installation & Configuration

#### Step 1: Navigate to Frontend Directory and Install Packages

```bash
cd frontend
npm install
```

#### Step 2: Configure Frontend Environment

Create a `.env` file inside the `frontend/` directory:

```bash
# Inside frontend/.env
VITE_API_URL=http://localhost:8000/api/v1
VITE_GOOGLE_CLIENT_ID=your-google-oauth-client-id.apps.googleusercontent.com
```

Return to the root workspace:
```bash
cd ..
```

---

### 6.4 OCR Engine Installation (Tesseract)

The platform includes an intelligent OCR receipt extraction engine. For OCR to function locally:

- **Ubuntu / Debian**:
  ```bash
  sudo apt-get update
  sudo apt-get install -y tesseract-ocr tesseract-ocr-eng libtesseract-dev
  # Tesseract binary is automatically located at: /usr/bin/tesseract
  ```
- **macOS (Homebrew)**:
  ```bash
  brew install tesseract
  # Path is usually /usr/local/bin/tesseract or /opt/homebrew/bin/tesseract
  ```
- **Windows**:
  1. Download and run the official installer from [UB-Mannheim Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki).
  2. Install to `C:\Program Files\Tesseract-OCR` or your preferred directory.
  3. Update `.env` with the absolute path:
     ```ini
     TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
     ```

---

### 6.5 Database Migrations & Initial Seed Data

The project connects directly to the remote Supabase PostgreSQL database.

#### Step 1: Initialize Database Tables & Migration Schema

```bash
# Run Alembic migrations to apply all current table schemas
alembic upgrade head
```

#### Step 2: Seed Core Configuration & Reference Data

The application automatically verifies connection status and seeds system configuration, default settings, and email templates on startup. To seed initial organizational structures, users, roles, and approval matrices, run the included seeding utilities:

```bash
# 1. Seed Organizational Structure (Departments & Cost Centres)
python scripts/seed_org.py

# 2. Seed Default Roles, Permissions, and Core Team Users
python scripts/seed_users.py

# 3. Seed Threshold-Based Approval Matrix Rules
python scripts/seed_approval_matrix.py

# 4. (Optional) Populate Sample Hardware Assets for Inventory Testing
python scripts/populate_assets.py
```

---

### 6.6 Running the Development Environment

#### Option A: Running Backend & Frontend in Dual Terminals (Recommended for Development)

**Terminal 1 (Backend API Server):**
```bash
# Ensure virtual environment is activated
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```
- API Root: `http://localhost:8000`
- Interactive Swagger UI: `http://localhost:8000/docs`
- ReDoc Documentation: `http://localhost:8000/redoc`
- System Liveness Check: `http://localhost:8000/health`
- Database Readiness Check: `http://localhost:8000/ready`

**Terminal 2 (Frontend React App):**
```bash
cd frontend
npm run dev
```
- Local SPA URL: `http://localhost:5173`

#### Option B: Containerized Execution with Docker

Build and launch the production-ready multi-stage container:

```bash
docker build -t expense-procurement-api .
docker run -p 8000:8000 --env-file .env expense-procurement-api
```

---

## 7. Environment Variables Reference

### 7.1 Backend Environment Configuration (`.env`)

| Variable Name | Type | Default Value | Description & Constraints |
| :--- | :--- | :--- | :--- |
| `ENVIRONMENT` | String | `development` | Environment tier: `development`, `testing`, `staging`, `production`. |
| `LOG_LEVEL` | String | `INFO` | Logging verbosity: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`. |
| `APP_VERSION` | String | `1.0.0` | Semantic version string for release tracking. |
| `DATABASE_URL` | String | *(Required)* | Asynchronous PostgreSQL connection DSN targeting Supabase.<br>`postgresql+asyncpg://postgres.[ref]:[pass]@aws-1-ap-south-1.pooler.supabase.com:5432/postgres` |
| `SUPABASE_URL` | String | *(Required)* | Supabase project API gateway endpoint URL (`https://[project-ref].supabase.co`). |
| `SUPABASE_KEY` | String | *(Required)* | Supabase anon public API key for cloud storage / client calls. |
| `JWT_SECRET` | String | *(Required)* | Cryptographically secure secret key (minimum 32 characters) for signing JWTs. |
| `TESSERACT_CMD` | String | `/usr/bin/tesseract` | Absolute path to the Tesseract OCR executable (`.exe` on Windows). |
| `REDIS_URL` | String | `redis://localhost:6379/0` | Redis caching connection DSN (application automatically falls back to memory cache if offline). |
| `AWS_REGION` | String | `us-east-1` | Target AWS region for cloud infrastructure. |
| `AWS_ACCESS_KEY_ID` | String | `mock-key` | AWS IAM credentials for cloud operations (Textract / S3). |
| `AWS_SECRET_ACCESS_KEY`| String | `mock-secret` | AWS IAM secret key. |
| `TEXTRACT_REGION` | String | `us-east-1` | Designated AWS region for cloud fallback OCR parsing. |
| `SMTP_HOST` | String | `smtp.mailtrap.io` | SMTP server host address for notification delivery. |
| `SMTP_PORT` | Integer | `2525` | SMTP port (e.g. 587, 465, or 2525). |
| `SMTP_USER` | String | `mock-user` | SMTP authentication username. |
| `SMTP_PASSWORD` | String | `mock-pass` | SMTP authentication password. |
| `SMTP_FROM_EMAIL` | String | `no-reply@enterprise.platform` | Default outgoing sender address. |
| `MAX_UPLOAD_SIZE` | Integer | `10485760` | Maximum allowable document upload size in bytes (Default: 10MB). |

---

### 7.2 Frontend Environment Configuration (`frontend/.env`)

| Variable Name | Example Value | Description |
| :--- | :--- | :--- |
| `VITE_API_URL` | `http://localhost:8000/api/v1` | Base URL of the FastAPI backend router prefix. In production, points to the live backend URL (`https://expense-backend-ym4v.onrender.com/api/v1`). |
| `VITE_GOOGLE_CLIENT_ID`| `[client-id].apps.googleusercontent.com` | Google Cloud Console OAuth 2.0 Web Client ID for single-sign-on (SSO). |

---

## 8. Production Deployment Guide (Render & Cloud)

In accordance with architectural standards, the platform is structured for automated continuous deployment (Git CI auto-deploy) via manual dashboard configuration on Render.

```
       ┌─────────────────────────────────────────────────────────┐
       │                   Render Cloud Domain                   │
       └────────────────────────────┬────────────────────────────┘
                                    │
           ┌────────────────────────┴────────────────────────┐
           ▼                                                 ▼
┌─────────────────────────────┐               ┌─────────────────────────────┐
│       Frontend Service      │               │       Backend Service       │
│      Type: Static Site      │               │  Type: Docker Web Service   │
│  Build: npm run build       │  REST / CORS  │ Start: gunicorn -c          │
│  Publish Path: dist         │──────────────>│        gunicorn_conf.py     │
│ URL: expense-frontend-rxv8  │               │        src.main:app         │
└─────────────────────────────┘               │ URL: expense-backend-ym4v   │
                                              └──────────────┬──────────────┘
                                                             │
                                                             ▼
                                              ┌─────────────────────────────┐
                                              │    Supabase PostgreSQL     │
                                              │       Managed Cloud         │
                                              │ aws-1-ap-south-1.pooler...  │
                                              └─────────────────────────────┘
```

### 8.1 Production Architecture Topology

1. **Backend Service (`expense-backend-ym4v.onrender.com`)**:
   - **Service Type**: **Docker Web Service** built directly from root `Dockerfile`.
   - **Runtime Command**: Handled inside container via `gunicorn -c gunicorn_conf.py src.main:app`.
   - **Healthcheck Path**: `/health`.
2. **Frontend Service (`expense-frontend-rxv8.onrender.com`)**:
   - **Service Type**: **Static Site**.
   - **Root Directory**: `frontend`.
   - **Build Command**: `npm run build`.
   - **Publish Directory**: `dist`.

---

### 8.2 Backend Service Configuration (Docker Web Service)

1. Navigate to your [Render Dashboard](https://dashboard.render.com/) and click **New +** -> **Web Service**.
2. Connect your Git repository.
3. Select **Docker** as the Runtime environment.
4. Set the Health Check Path to `/health`.
5. Under **Environment Variables**, add:
   - `ENVIRONMENT` = `production`
   - `LOG_LEVEL` = `INFO`
   - `DATABASE_URL` = `postgresql+asyncpg://postgres.[ref]:[pass]@aws-1-ap-south-1.pooler.supabase.com:5432/postgres`
   - `SUPABASE_URL` = `https://[ref].supabase.co`
   - `SUPABASE_KEY` = `[your-supabase-service-key]`
   - `JWT_SECRET` = `[generate-strong-jwt-secret]`
   - `TESSERACT_CMD` = `/usr/bin/tesseract`
   - `PORT` = `8000`

---

### 8.3 Frontend Service Configuration (Static Site)

1. Click **New +** -> **Static Site**.
2. Connect the Git repository.
3. Configure the build parameters:
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Publish Directory**: `dist`
4. Under **Environment Variables**, specify:
   - `VITE_API_URL` = `https://expense-backend-ym4v.onrender.com/api/v1`
   - `VITE_GOOGLE_CLIENT_ID` = `[your-google-oauth-client-id]`
5. In **Redirects / Rewrites**, configure the Single Page Application fallback:
   - **Source**: `/*`
   - **Destination**: `/index.html`
   - **Action**: `Rewrite`

---

### 8.4 Supabase Connection Pooling Best Practices

- Always use the **Supabase Transaction / Session Connection Pooler** host:
  `aws-1-ap-south-1.pooler.supabase.com` on port `5432` or `6543`.
- The application automatically manages an asynchronous engine pool with `pool_size=10`, `max_overflow=20`, and `pool_recycle=1800` to prevent stale connection timeouts.
- Never mount local PostgreSQL containers to override the production Supabase database.

---

## 9. REST API Directory & Interactive Documentation

FastAPI automatically generates real-time, interactive API specifications:
- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`
- **OpenAPI Schema (JSON)**: `/openapi.json`

### Key API Endpoint Routes

| Router Prefix | Domain Entity | Methods | Key Endpoint Operations |
| :--- | :--- | :--- | :--- |
| `/health` | System Liveness | `GET` | Process liveness probe for load balancers. |
| `/ready` | Database Readiness | `GET` | Verifies active database connection probe. |
| `/api/v1/auth` | Authentication | `POST` | `/login`, `/register`, `/refresh`, `/google`, `/mfa/setup`, `/mfa/verify` |
| `/api/v1/users` | User Administration | `GET`, `POST`, `PUT` | `/users`, `/users/{id}`, `/users/{id}/roles` |
| `/api/v1/roles` | RBAC Matrix | `GET`, `POST` | `/roles`, `/roles/{id}`, `/roles/{id}/permissions` |
| `/api/v1/departments` | Org Structure | `GET`, `POST` | Department management and cost centre assignment. |
| `/api/v1/cost_centres` | Financial Budgets | `GET`, `POST` | Cost centre creation and encumbrance tracking. |
| `/api/v1/purchase_requisitions` | Requisitions (PR) | `GET`, `POST`, `PUT`, `DELETE` | PR draft, line-items, budget validation, submit for approval. |
| `/api/v1/approvals` | Approval Engine | `GET`, `POST` | `/history`, `/matrix`, approval/rejection actions. |
| `/api/v1/approvals-inbox`| Task Inbox | `GET` | Filtered pending approval queue for current authenticated user. |
| `/api/v1/vendors` | Vendor Directory | `GET`, `POST`, `PUT` | Vendor registration, compliance status, performance score. |
| `/api/v1/rfq` | Sourcing & RFQ | `GET`, `POST` | RFQ generation from PR, vendor quotation invitations. |
| `/api/v1/quotations` | Vendor Bids | `GET`, `POST` | Quotation submissions, matrix comparison, winning bid award. |
| `/api/v1/purchase_orders` | Purchase Orders (PO) | `GET`, `POST`, `PUT` | Formal PO creation, tracking, status updates. |
| `/api/v1/deliveries` | Logistics & Inward | `GET`, `POST` | Delivery tracking, carrier details, package intake. |
| `/api/v1/grn` | Goods Receipt Note | `GET`, `POST` | Warehouse inspection reports, accepted items, GRN creation. |
| `/api/v1/invoices` | Invoicing & 3-Way Match | `GET`, `POST` | Vendor invoice upload, automated 3-way matching engine. |
| `/api/v1/expenses` | Expense Reports | `GET`, `POST`, `PUT` | Multi-currency expense submission, receipt OCR processing. |
| `/api/v1/assets` | Hardware & Assets | `GET`, `POST`, `PUT` | Asset registry, serial assignment, "My Assets", maintenance. |
| `/api/v1/asset_incidents` | Incident Tracking | `GET`, `POST` | Asset damage reporting, repair logs, photo evidence. |
| `/api/v1/offboarding` | Offboarding Recovery | `GET`, `POST` | Employee exit asset checklist, return clearance. |
| `/api/v1/dashboard` | Executive KPIs | `GET` | Spend analytics, budget burn rate, pending task metrics. |
| `/api/v1/reports` | Export Engine | `GET`, `POST` | Downloadable reports (Excel `.xlsx` and CSV). |
| `/api/v1/audit` | Audit Log Trail | `GET` | Immutable system event history with entity change tracking. |

---

## 10. Security, Middleware Pipeline & Observability

The application executes incoming requests through a hardened ASGI middleware pipeline designed for security compliance:

```
Request ───► CORS / Trusted Host ───► ExceptionMiddleware ───► LoggingMiddleware ───► RequestIdMiddleware ───► SecurityHeaders ───► Endpoint
                                                                                                                                       │
Response ◄─── CORS / Trusted Host ◄─── ExceptionMiddleware ◄─── LoggingMiddleware ◄─── RequestIdMiddleware ◄─── SecurityHeaders ◄───┘
```

1. **Defense-in-Depth Exception Shield**: Unhandled exceptions are intercepted, mapped to the active `X-Request-ID`, and translated into standardized JSON responses (`{"detail": "..."}`) without exposing internal stack traces.
2. **Context-Safe Distributed Tracing**: Every request is assigned a unique UUID4 `X-Request-ID` stored in thread-safe `contextvars`. This ID accompanies all log records and database audit events.
3. **Hardened HTTP Security Headers**:
   - `X-Frame-Options: DENY` (Anti-clickjacking protection)
   - `X-Content-Type-Options: nosniff` (MIME-type sniffing prevention)
   - `Strict-Transport-Security: max-age=31536000; includeSubDomains` (Enforces HTTPS)
   - `Content-Security-Policy: default-src 'self'`
4. **Adaptive GZip Payload Compression**: Automatically compresses JSON response payloads larger than 1,000 bytes.
5. **OWASP-Compliant Credential Storage**: Passwords are protected using Argon2id with random 16-byte cryptographic salts.

---

## 11. Testing, Code Quality & Verification

The test suite covers unit logic, integration flows, and end-to-end P2P scenarios:

```bash
# 1. Run all Pytest test suites with detailed verbosity
python -m pytest -v

# 2. Run specific workflow isolation suites
python -m pytest tests/test_employee_procurement_workflow.py -v
python -m pytest tests/test_expense_workflow.py -v
python -m pytest tests/test_offboarding_workflow.py -v
python -m pytest tests/test_approval_matrix.py -v

# 3. Execute live API health verification script
python scripts/api_health_check.py

# 4. Execute End-to-End P2P Lifecycle Simulation Script
python scripts/e2e_full_workflow.py
```

### Frontend Quality Checks

```bash
cd frontend

# Run ESLint validation
npm run lint

# Execute production build verification
npm run build

# Run Playwright End-to-End browser tests
npx playwright test
```

---

## 12. Clean Directory Layout

```text
├── .agents/                      # Agent & workspace rules and architectural definitions
├── alembic/                      # Alembic database migration revisions and environment
├── docker/                       # Docker orchestration scripts
├── docs/                         # Additional architecture and workflow documentation
│   ├── application_architecture.md
│   └── application_workflow.md
├── frontend/                     # React 19 + TypeScript + Vite SPA
│   ├── src/
│   │   ├── components/           # Reusable UI component library (modals, forms, tables)
│   │   ├── hooks/                # Custom React hooks (auth, query, responsive)
│   │   ├── layouts/              # App navigation, sidebar, and executive headers
│   │   ├── pages/                # 26 Domain views (PRs, POs, Approvals, Expenses, Assets)
│   │   ├── routes/               # Protected route guards and role routing
│   │   ├── services/             # Axios API service clients
│   │   ├── types/                # TypeScript interface and enum contracts
│   │   ├── App.tsx               # Root application component
│   │   └── index.css             # Tailwind CSS tokens and global styling
│   ├── package.json              # Frontend dependencies and build scripts
│   └── vite.config.ts            # Vite compiler configuration
├── scripts/                      # Administration, verification, and seeding utilities
│   ├── api_health_check.py       # Live HTTP probe tester
│   ├── e2e_full_workflow.py      # End-to-End P2P lifecycle simulator
│   ├── seed_approval_matrix.py   # Seeder for multi-tier approval rules
│   ├── seed_org.py               # Seeder for departments and cost centres
│   ├── seed_users.py             # Seeder for administrative and test users
│   └── populate_assets.py        # Seeder for asset tracking registry
├── src/                          # Backend Core Application
│   ├── api/                      # 28 FastAPI Router Modules (Auth, PR, PO, Expense, etc.)
│   ├── core/                     # Configuration (Pydantic Settings), Logging, Constants
│   ├── database/                 # Async SQLAlchemy engine, session factory, dependencies
│   ├── middleware/               # Security, Exception, Request ID, and Logging middlewares
│   ├── models/                   # 24 Declarative SQLAlchemy ORM Domain Models
│   ├── repositories/             # Generic BaseRepository & customized queries
│   ├── schemas/                  # Pydantic v2 Request/Response validation models
│   ├── services/                 # 27 Domain Business Logic Services (Approval, OCR, PR, etc.)
│   ├── utils/                    # Common formatting, date handling, and calculations
│   └── main.py                   # FastAPI Application Entrypoint & Lifespan Hooks
├── tests/                        # 18 Pytest Automated Testing Suites
├── uploads/                      # Local document upload directory (receipts, manifests)
├── .env.example                  # Environment configuration template
├── Dockerfile                    # Production multi-stage Docker build specification
├── gunicorn_conf.py              # Gunicorn multi-worker ASGI server configuration
├── pyproject.toml                # Python toolchain settings (pytest, ruff)
├── requirements.txt              # Production Python package manifest
└── README.md                     # Comprehensive Production Platform Handbook
```

---

## 13. Troubleshooting & Operations FAQ

### Q1: `TesseractNotFoundError` or OCR extraction returns empty text
**Fix**: Ensure Tesseract is installed on your OS and the `TESSERACT_CMD` environment variable in your `.env` matches the binary location.
- *Windows*: Ensure path uses backslashes or raw string: `TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe`.
- *Linux*: Verify binary existence via `which tesseract` (usually `/usr/bin/tesseract`).

### Q2: Database Connection Timeout with Supabase
**Fix**: Verify that you are connecting via the Supabase connection pooler endpoint (`aws-1-ap-south-1.pooler.supabase.com:5432`) rather than the direct database instance host. Ensure that your IPv4/IPv6 egress permits SSL traffic over port 5432.

### Q3: Frontend Displays CORS Errors in Browser Console
**Fix**: Open `src/main.py` and ensure the frontend origin URL is explicitly included in `CORSMiddleware` `allow_origins` or matches `allow_origin_regex=r"https://.*\.onrender\.com"`.

### Q4: 3-Way Matching Discrepancy Alerts
**Fix**: A 3-way match failure occurs if the vendor invoice quantity or unit rate exceeds the purchase order / received GRN quantity beyond the configured tolerance limit (default: 0%). Inspect the invoice line items under **Accounts Payable -> Invoices** to review the flagged variance.

---

## 14. License & Support

This project is proprietary and confidential. Maintained by the Enterprise Architecture & Development Engineering Team.

For deployment support, bug reports, or feature enhancements, please submit an issue or contact the repository maintainers.
