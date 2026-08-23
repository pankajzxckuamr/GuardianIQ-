import os
import sys
from sqlalchemy import text
from app.db.session import SessionLocal

SQL_FILE = r"D:\GuardianIQ--1\database\seed\GuardianIQ_Database_Backup.sql"

def run_import():
    if not os.path.exists(SQL_FILE):
        print(f"File not found: {SQL_FILE}")
        sys.exit(1)

    print(f"Reading {SQL_FILE}...")
    with open(SQL_FILE, 'r', encoding='utf-8', errors='ignore') as f:
        sql_content = f.read()

    db = SessionLocal()
    print("Executing SQL statements...")
    
    try:
        db.execute(text(sql_content))
        db.commit()
        print("✅ Data imported successfully!")
    except Exception as e:
        db.rollback()
        print(f"❌ Error during bulk import: {e}")
        print("\nAttempting to execute statement-by-statement to safely skip duplicates...")
        
        # Fallback: execute line by line or statement by statement
        statements = sql_content.split(';')
        success = 0
        failed = 0
        for stmt in statements:
            stmt = stmt.strip()
            if not stmt:
                continue
            try:
                db.execute(text(stmt))
                db.commit()
                success += 1
            except Exception as inner_e:
                db.rollback()
                failed += 1
                
        print(f"\n✅ Fallback import finished. {success} statements succeeded, {failed} statements failed (usually duplicate entries).")
    
    finally:
        db.close()

if __name__ == "__main__":
    run_import()
