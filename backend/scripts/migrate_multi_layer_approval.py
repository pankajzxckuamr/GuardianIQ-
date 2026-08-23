import sys
import os
import uuid
import logging
from sqlalchemy import create_engine, text

# Add the parent directory to sys.path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.db.session import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    logger.info("Starting multi-layer approval migration...")
    
    with engine.begin() as conn:
        # 1. Add approval_default_order to departments
        logger.info("Adding approval_default_order to departments table...")
        try:
            conn.execute(text("ALTER TABLE departments ADD COLUMN approval_default_order INTEGER;"))
        except Exception as e:
            logger.warning(f"Column might already exist: {e}")

        # 2. Create department_owner_assignments table
        logger.info("Creating department_owner_assignments table...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS department_owner_assignments (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                tenant_id UUID NOT NULL,
                department_id UUID NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
                owner_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
                owner_group_id UUID REFERENCES approval_groups(id) ON DELETE SET NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT check_single_owner CHECK (
                    (owner_user_id IS NOT NULL AND owner_group_id IS NULL) OR 
                    (owner_user_id IS NULL AND owner_group_id IS NOT NULL)
                )
            );
        """))

        # 3. Create schedule_approval_layer_selections table
        logger.info("Creating schedule_approval_layer_selections table...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS schedule_approval_layer_selections (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                tenant_id UUID NOT NULL,
                schedule_id UUID NOT NULL REFERENCES workflow_schedules(id) ON DELETE CASCADE,
                department_id UUID NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
                layer_order INTEGER NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """))

        # 4. Modify workflow_schedule_approvals table
        logger.info("Modifying workflow_schedule_approvals table...")
        try:
            conn.execute(text("ALTER TABLE workflow_schedule_approvals ADD COLUMN approval_layer INTEGER DEFAULT 1 NOT NULL;"))
            conn.execute(text("ALTER TABLE workflow_schedule_approvals ADD COLUMN department_id UUID REFERENCES departments(id);"))
            conn.execute(text("ALTER TABLE workflow_schedule_approvals ADD COLUMN approval_cycle_id UUID;"))
            conn.execute(text("ALTER TABLE workflow_schedule_approvals ADD COLUMN parent_approval_id UUID REFERENCES workflow_schedule_approvals(id);"))
            conn.execute(text("ALTER TABLE workflow_schedule_approvals ADD COLUMN decided_by UUID REFERENCES users(id);"))
            conn.execute(text("ALTER TABLE workflow_schedule_approvals ADD COLUMN skip_reason TEXT;"))
        except Exception as e:
            logger.warning(f"Columns might already exist: {e}")

        # 5. Backfill existing workflow_schedule_approvals
        logger.info("Backfilling workflow_schedule_approvals...")
        
        # We need a new UUID for approval_cycle_id per row where it's null
        approvals = conn.execute(text("SELECT id, approver_user_id, decided_at FROM workflow_schedule_approvals WHERE approval_cycle_id IS NULL")).fetchall()
        for approval in approvals:
            cycle_id = str(uuid.uuid4())
            decided_by = approval.approver_user_id if approval.decided_at is not None else None
            
            update_query = text("""
                UPDATE workflow_schedule_approvals 
                SET approval_cycle_id = :cycle_id, 
                    approval_layer = 1,
                    decided_by = :decided_by
                WHERE id = :id
            """)
            conn.execute(update_query, {"cycle_id": cycle_id, "decided_by": decided_by, "id": approval.id})
            
        # Make approval_cycle_id NOT NULL after backfill
        try:
            conn.execute(text("ALTER TABLE workflow_schedule_approvals ALTER COLUMN approval_cycle_id SET NOT NULL;"))
        except Exception as e:
            logger.warning(f"Could not set approval_cycle_id to NOT NULL: {e}")

        # 6. Seed the 5 departments
        logger.info("Seeding departments...")
        
        # We need a tenant_id to create departments. We'll pick one from existing users/departments or use a default.
        tenant_row = conn.execute(text("SELECT id FROM users LIMIT 1")).fetchone() # In a real app we'd seed this per-tenant, but for this script we just need them to exist.
        
        # Just use raw SQL with subquery to get a valid tenant_id from users
        seed_departments = [
            ("BUSINESS_OWNER", "Business Owner", 1),
            ("TECHNICAL_OWNER", "Technical Owner", 2),
            ("AUDIT", "Audit", 3),
            ("HR", "HR", 4),
            ("LEGAL", "Legal", 5)
        ]
        
        for code, name, order in seed_departments:
            # Check if exists
            exists = conn.execute(text("SELECT 1 FROM departments WHERE department_code = :code"), {"code": code}).scalar()
            if not exists:
                logger.info(f"Inserting department {code}...")
                conn.execute(text("""
                    INSERT INTO departments (id, tenant_id, department_code, department_name, status, approval_default_order)
                    VALUES (gen_random_uuid(), COALESCE((SELECT tenant_id FROM users LIMIT 1), gen_random_uuid()), :code, :name, 'ACTIVE', :order)
                """), {"code": code, "name": name, "order": order})
            else:
                # Update default order
                conn.execute(text("""
                    UPDATE departments SET approval_default_order = :order WHERE department_code = :code
                """), {"code": code, "order": order})

    logger.info("Migration complete.")

if __name__ == "__main__":
    run_migration()
