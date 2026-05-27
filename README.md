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

- **Python 3.10+**
- **Node.js** (for the React/Vite frontend)
- **PostgreSQL** (installed locally or via Docker)

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

### 4. Run Database Migrations & Seed Data

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

> The frontend dependencies are assumed to already be installed via `npm install`. Run it if needed before starting.

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
