# GuardianIQ — Enterprise Shield Platform

GuardianIQ is a FastAPI-based backend paired with a React + Vite frontend, providing insights, governance, and RBAC (Role-Based Access Control) for personal data and AI activities.

---
 
## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Database Setup](#database-setup)
3. [Backend Setup](#backend-setup)
4. [Frontend Setup](#frontend-setup)
5. [Running the Application](#running-the-application)
6. [Credentials & Access](#credentials--access)
7. [Testing & API Reference](#testing--api-reference)

---

## Prerequisites

- **Python 3.11+**
- **Node.js 18+** (for the React/Vite frontend)
- **PostgreSQL 14+** (installed locally or via Docker)
- **Phase 0 & Phase 1 components properly configured and seeded.**

---

## Database Setup

You must have PostgreSQL installed locally or running via Docker. Open your PostgreSQL terminal (`psql` or pgAdmin) and run:

```sql
CREATE DATABASE guardianiq;
CREATE USER guardianiq_user WITH PASSWORD 'guardianiq123';
GRANT ALL PRIVILEGES ON DATABASE guardianiq TO guardianiq_user;
```

---

## Backend Setup

### 1. Navigate to the Backend Directory

```powershell
cd backend
```

### 2. Create & Activate the Python Virtual Environment

```powershell
# Create the virtual environment
python -m venv venv
```

**Activate it:**

- **Windows (Command Prompt / PowerShell)**:
  ```powershell
  .\venv\Scripts\activate
  ```
- **Mac / Linux**:
  ```bash
  source venv/bin/activate
  ```

### 3. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy the example environment file:
```powershell
cp .env.example .env
```

Open `.env` and verify the `DATABASE_URL` matches the credentials from the database setup step:
```ini
DATABASE_URL=postgresql://guardianiq_user:guardianiq123@localhost:5432/guardianiq
```

### 5. Run Database Migrations & Seed Data

Make sure your PostgreSQL database is running, then execute:

```powershell
# Create all database tables
alembic upgrade head

# Populate initial roles and security permissions
python -m app.db.seed
```

---

## Frontend Setup

### 1. Navigate to the Frontend Directory

Open a **separate terminal window** and run:

```powershell
cd frontend
```

### 2. Configure Environment Variables

```powershell
cp .env.example .env
```

### 3. Install Dependencies

```powershell
npm install
```

---

## Running the Application

### 🛠️ Start the Backend

From the `backend/` directory (with the virtual environment activated):

```powershell
uvicorn app.main:app --reload
```

| Endpoint | URL |
|----------|-----|
| API Swagger Docs | `http://127.0.0.1:8000/docs` |
| Database Health Check | `http://127.0.0.1:8000/api/health/db` |

---

### 💻 Start the Frontend

From the `frontend/` directory, choose one of the following modes:

#### Development Mode *(Recommended)*

Starts Vite with hot-module reloading and API proxying to the backend:

```powershell
npm run dev
```

> **Access URL:** `http://localhost:5173`
>
> Vite is pre-configured to proxy all `/api` requests to the backend running on port `8000`.

#### Production Mode *(Alternative)*

Tests how the app behaves under strict Content Security Policies (CSP):

```powershell
# Step 1: Build and package assets
npm run build

# Step 2: Serve the production bundle
npm run serve
```

> **Access URL:** `http://localhost:5173`

---

## Credentials & Access

Use these seeded credentials on the Login Page (`http://localhost:5173/login`):

| Field | Value |
|-------|-------|
| **Email** | `admin@guardianiq.com` |
| **Password** | `Admin@1234!` |

> This is the default admin account seeded into the PostgreSQL database.

---

## Testing & API Reference

Once the backend server is running, test the APIs using the interactive **Swagger UI** at `http://127.0.0.1:8000/docs`.

| Step | Endpoint | Description |
|------|----------|-------------|
| 1 | `GET /api/health` | Verify the server is running |
| 2 | `GET /api/health/db` | Verify the database connection |
| 3 | `POST /api/auth/login` | Obtain a JWT access token |
| 4 | `GET /api/auth/roles` | Test a protected route (requires token) |

**To authenticate in Swagger UI:**
1. Call `POST /api/auth/login` to get your JWT token.
2. Click the **"Authorize"** padlock icon at the top of the Swagger page.
3. Paste the token and confirm — all protected routes will now be accessible.

---

## Phase 2: Workflow Scheduling & Agent Execution

**Core Design Statement:** Every schedule, run, agent invocation, policy check, result, failure, and override must be controlled by identity, permissions, ownership, ABAC context, audit events, and governance status.

### Overview
Phase 2 introduces governed workflow scheduling and AI agent execution. It ensures that any automated execution is tracked, auditable, and subject to Role-Based Access Control (RBAC) and Attribute-Based Access Control (ABAC).

### Key Design Decisions
- **Database-Backed Scheduler:** Ensures persistence, transactional integrity, and visibility over scheduled tasks using `FOR UPDATE SKIP LOCKED`.
- **RBAC + ABAC:** Allows fine-grained access control based on user roles and department contexts, essential for high-risk operations.
- **Explicit Tool Lists:** Defines strict boundary rules indicating exactly which write-operations an agent is allowed to execute.
- **Immutable Audit Events:** Leverages database triggers to block updates/deletes on the `audit_events` table for cryptographic integrity.

### Quick Start (Clone to First Test Run)
1. **Ensure Backend is Running:** Follow the Backend Setup above and ensure `.env` has `PHASE2_SCHEDULER_ENABLED=true`.
2. **Start Scheduler Worker:** Open a terminal in `backend/` and run `python -m app.workers.worker_main`.
3. **Login:** Use the frontend (`http://localhost:5173`) with `admin@guardianiq.com` and `Admin@1234!`.
4. **Create Schedule:** Navigate to Workflow Scheduler > Create New. Follow the wizard, selecting a recommend-only agent, and save as `DRAFT`.
5. **Submit & Approve:** Click "Submit for Approval" on the schedule detail page, then go to Schedule Approvals to approve it.
6. **Trigger Run Now:** Click "Run Now".
7. **View Results:** Go to Run History to see the completed run output.

### Module Structure Table
| Module | Responsibility |
|---|---|
| `workflow_scheduler` | Manages creation, state transitions, and background polling of schedules |
| `workflow_run` | Handles agent execution, steps logging, output generation, and boundary checks |
| `authorization` | Enforces ABAC and RBAC security rules for schedules and runs |
| `notifications` | Emits alerts and escalations for high-risk operations |

### Status Lifecycle Diagrams

#### Schedule Status Lifecycle
```mermaid
graph TD
    DRAFT --> PENDING_APPROVAL
    PENDING_APPROVAL --> ACTIVE
    PENDING_APPROVAL --> DRAFT
    ACTIVE --> PAUSED
    PAUSED --> ACTIVE
    ACTIVE --> RETIRED
```

#### Run Status Lifecycle
```mermaid
graph TD
    QUEUED --> SCHEDULED
    SCHEDULED --> RUNNING
    RUNNING --> COMPLETED
    RUNNING --> FAILED
    RUNNING --> ESCALATED
    FAILED --> RETRY_QUEUED
    RETRY_QUEUED --> RUNNING
```

### Environment Variables
Check `.env.phase2.example` in the `backend` folder for Phase 2 specific configurations (`SCHEDULER_ENABLED`, `PHASE2_SCHEDULER_ENABLED`, etc.).

### Running Tests
To run the Phase 2 end-to-end tests:
```bash
cd backend
pytest tests/test_phase2_e2e.py -v
```

### Adding a New Governance Event
1. Define the event code in `backend/app/modules/audit/event_codes.py`.
2. Publish it anywhere in the code using `EventService.publish(event_code, context)`.
3. The trigger ensures it is immutable.

