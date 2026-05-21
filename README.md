# GuardianIQ Backend

GuardianIQ is a FastAPI-based backend application providing insights, governance, and RBAC (Role-Based Access Control) for personal data and AI activities.

## 🚀 Local Environment Setup

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

## 🧪 Testing Locally

Once the server is running, you can test the APIs using the interactive Swagger UI:
1. Open **http://127.0.0.1:8000/docs** in your browser.
2. Check **`GET /api/health`** to verify the server is running.
3. Check **`GET /api/health/db`** to verify the database connection is successful.
4. **Testing Auth:** Use `POST /api/auth/login` to get a JWT token, click the "Authorize" padlock at the top of the screen to inject the token, and then you can test protected routes like `GET /api/auth/roles`.