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
