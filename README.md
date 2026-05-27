# GuardianIQ Backend

GuardianIQ is a FastAPI-based backend application providing insights, governance, and RBAC (Role-Based Access Control) for personal data and AI activities.

##  Local Environment Setup

To run this project locally, you need to set up your PostgreSQL database and your Python environment.

### 1. Database Setup
You must have PostgreSQL installed locally (or running via Docker). Based on the `.env` configuration, you need to provision the database with the following credentials:

Open your PostgreSQL terminal (`psql` or pgAdmin) and run:
```sql
CREATE DATABASE guardianiq;
CREATE USER guardianiq_user WITH PASSWORD 'guardianiq123';
GRANT ALL PRIVILEGES ON DATABASE guardianiq TO guardianiq_user;
```

### 2. Python Environment
Ensure you have Python 3.10+ installed. Open your terminal in the root directory:

```powershell
# Navigate to the backend folder
cd backend

# Create a virtual environment
python -m venv venv

# Activate the virtual environment (Windows)
.\venv\Scripts\activate
# (On Mac/Linux: source venv/bin/activate)

# Install dependencies
pip install -r requirements.txt
```

### 3. Database Migrations & Seeding
Once your database is running and your `.env` file is ready, you need to create the tables and seed the initial roles/permissions.

```powershell
# 1. Run migrations to create all tables
alembic upgrade head

# 2. Run the seed script to populate Roles and Permissions
python -m app.db.seed
```

### 4. Running the Server
Start the local FastAPI development server:

```powershell
uvicorn app.main:app --reload
```
The API will be available at `http://127.0.0.1:8000`.

## Testing Locally


# FRONTEND + BACKEND RUN

# GuardianIQ - Quick Start & Execution Guide

This guide provides clean, step-by-step instructions on how to start and run both the **FastAPI Backend** and **React-Vite Frontend** of the GuardianIQ Enterprise Shield Platform.

---

## 🛠️ Step 1: Start the Backend (FastAPI)

The backend provides the database connections, authentication services, auditing, and RBAC APIs.

1. **Open a new terminal/command prompt** and navigate to the project's backend directory:
   ```powershell
   cd backend
   ```

2. **Activate the Python virtual environment**:
   * **Windows (Command Prompt / Powershell)**:
     ```powershell
     .\venv\Scripts\activate
     ```
   * **Mac / Linux**:
     ```bash
     source venv/bin/activate
     ```

3. **Verify Database Setup & Migrations (Only if you haven't yet)**:
   * Make sure your PostgreSQL database is running.
   * Run the Alembic database migrations to ensure the latest database schema is created:
     ```powershell
     alembic upgrade head
     ```
   * Populate initial roles and security permissions by running the database seed script:
     ```powershell
     python -m app.db.seed
     ```

4. **Start the Uvicorn Dev Server**:
   ```powershell
   uvicorn app.main:app --reload
   ```
   * **API Swagger Documentation**: Open `http://127.0.0.1:8000/docs` in your browser to inspect or test endpoints.
   * **Telemetry Health Endpoint**: Visit `http://127.0.0.1:8000/api/health/db` to verify the PostgreSQL connection.

---

## 💻 Step 2: Start the Frontend (React + Vite)

The frontend is a modern web interface equipped with the Security Cockpit, active RBAC checking, and the Foundation Health Monitor.

1. **Open a SECOND terminal window** and navigate to the project's frontend directory:
   ```powershell
   cd frontend
   ```

2. **Run in Development Mode (Recommended)**:
   Starts Vite with automatic hot-module reloading and API request proxying:
   ```powershell
   npm run dev
   ```
   * **Access URL**: Open **`http://localhost:5173`** in your browser.
   * *Note: Vite is pre-configured to proxy `/api` requests to the running backend server on port 8000.*

3. **Run in Production Mode (Alternative)**:
   To test exactly how it builds and behaves under strict Content Security Policies (CSP):
   * Build the project and package assets:
     ```powershell
     npm run build
     ```
   * Serve the production bundle using the production client server:
     ```powershell
     npm run serve
     ```
   * **Access URL**: Open **`http://localhost:5173`**.

---

## 🔐 Credentials & Access

Use these seeded credentials on the frontend Login Page (`http://localhost:5173/login`) to access the dashboard:

* **Username/Email**: `admin@guardianiq.com`
* **Password**: `admin123` *(this is the default admin account seeded into the PostgreSQL database)*



Once the server is running, you can test the APIs using the interactive Swagger UI:
1. Open **http://127.0.0.1:8000/docs** in your browser.
2. Check **`GET /api/health`** to verify the server is running.
3. Check **`GET /api/health/db`** to verify the database connection is successful.
4. **Testing Auth:** Use `POST /api/auth/login` to get a JWT token, click the "Authorize" padlock at the top of the screen to inject the token, and then you can test protected routes like `GET /api/auth/roles`.
