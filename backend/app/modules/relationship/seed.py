import os
import sys
from uuid import uuid4
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from datetime import datetime

# Adjust sys.path to run standalone
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
from app.db.session import engine

def backfill_owner_responsibilities():
    with Session(engine) as db:
        print("Starting backfill for owner responsibilities...")
        
        # Get admin user ID for default tenant_id if missing
        admin_res = db.execute(text("SELECT id FROM users WHERE email='admin@guardianiq.com' LIMIT 1"))
        admin_id = admin_res.scalar()
        if not admin_id:
            print("Admin user not found, cannot reliably backfill.")
            return

        tables = ["ai_models", "agents", "tools", "workflows"]
        
        for table in tables:
            print(f"Processing table {table}...")
            # We want to find records that don't have an owner responsibility yet
            # First fetch all rows
            try:
                res = db.execute(text(f"SELECT id, tenant_id, owner_user_id FROM {table} WHERE owner_user_id IS NOT NULL"))
                rows = res.fetchall()
                print(f"Found {len(rows)} records in {table} with an owner.")
                
                count = 0
                for row in rows:
                    obj_id = row[0]
                    tenant_id = row[1] or admin_id
                    owner_id = row[2]
                    
                    # Check if responsibility already exists
                    check_res = db.execute(text(f"""
                        SELECT id FROM object_responsibilities 
                        WHERE object_id = '{obj_id}' AND object_type = '{table}' AND responsibility_type = 'OWNER'
                    """))
                    
                    if not check_res.scalar():
                        # Insert new responsibility
                        db.execute(text(f"""
                            INSERT INTO object_responsibilities 
                            (id, tenant_id, object_type, object_id, actor_type, actor_id, responsibility_type, is_primary, effective_from, status) 
                            VALUES 
                            ('{uuid4()}', '{tenant_id}', '{table}', '{obj_id}', 'USER', '{owner_id}', 'OWNER', true, '{datetime.utcnow().isoformat()}', 'ACTIVE')
                        """))
                        count += 1
                
                print(f"Inserted {count} owner responsibilities for {table}.")
            except Exception as e:
                print(f"Error processing {table}: {e}")
        
        db.commit()
        print("Backfill completed successfully.")

if __name__ == "__main__":
    backfill_owner_responsibilities()
