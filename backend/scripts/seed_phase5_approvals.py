import os
import sys
from uuid import uuid4

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ.setdefault("DATABASE_URL", "postgresql://guardianiq_user:guardianiq123@localhost:5432/guardianiq")

from sqlalchemy import text
from app.db.session import SessionLocal

def seed_phase5_approvals():
    db = SessionLocal()
    try:
        print("[INFO] Seeding Phase 5 Approval Departments...")
        
        # 1. Fetch a tenant
        tenant = db.execute(text("SELECT id FROM tenants LIMIT 1")).fetchone()
        if not tenant:
            print("[ERROR] No tenant found. Please ensure basic data has been seeded.")
            return
        tenant_id = tenant.id
        
        # 2. Insert or Update Departments
        departments = [
            ("BUSINESS_OWNER", "Business Owner", 1),
            ("TECHNICAL_OWNER", "Technical Owner", 2),
            ("AUDIT", "Audit", 3),
            ("HR", "HR", 4),
            ("LEGAL", "Legal", 5),
        ]
        
        dept_ids = {}
        for code, name, order in departments:
            # Check if exists
            row = db.execute(text("SELECT id FROM departments WHERE department_code = :code"), {"code": code}).fetchone()
            if row:
                dept_id = row.id
                db.execute(text("""
                    UPDATE departments 
                    SET approval_default_order = :order
                    WHERE id = :id
                """), {"order": order, "id": dept_id})
            else:
                dept_id = uuid4()
                db.execute(text("""
                    INSERT INTO departments (id, department_name, department_code, approval_default_order, tenant_id, created_at, updated_at)
                    VALUES (:id, :name, :code, :order, :tenant_id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """), {"id": dept_id, "code": code, "name": name, "order": order, "tenant_id": tenant_id})
            dept_ids[code] = dept_id

        # 3. Fetch some users to assign
        users = db.execute(text("SELECT id FROM users LIMIT 2")).fetchall()
        if not users:
            print("[ERROR] No users found. Please create users first via seed scripts.")
            return
            
        user1_id = users[0].id
        user2_id = users[1].id if len(users) > 1 else users[0].id
        
        print("[INFO] Seeding Department Owner Assignments...")
        # Clear old assignments for these departments
        for code, dept_id in dept_ids.items():
            db.execute(text("DELETE FROM department_owner_assignments WHERE department_id = :dept_id"), {"dept_id": dept_id})
        
        # Assign Business Owner, Audit, Legal to user1
        # Assign Technical Owner, HR to user2
        assignments = [
            (dept_ids["BUSINESS_OWNER"], user1_id),
            (dept_ids["TECHNICAL_OWNER"], user2_id),
            (dept_ids["AUDIT"], user1_id),
            (dept_ids["HR"], user2_id),
            (dept_ids["LEGAL"], user1_id),
        ]
        
        for dept_id, owner_id in assignments:
            db.execute(text("""
                INSERT INTO department_owner_assignments (id, department_id, owner_user_id, tenant_id, created_at, updated_at)
                VALUES (gen_random_uuid(), :dept_id, :owner_id, :tenant_id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """), {"dept_id": dept_id, "owner_id": owner_id, "tenant_id": tenant_id})
            
        db.commit()
        print("[SUCCESS] Phase 5 Approval data successfully seeded! user1 gets Business, Audit, Legal. user2 gets Technical, HR.")
    except Exception as e:
        print(f"[ERROR] Seeding failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_phase5_approvals()
