import os
import sys
from sqlalchemy import create_engine, text

# Get DB URL from env or use default
from dotenv import load_dotenv
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/guardianiq")

def check_schema():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        tables_to_check = [
            "ai_models", "agents", "tools", "workflows", "generic_relationships",
            "object_responsibilities", "relationship_validation_results",
            "relationship_graph_snapshots", "policy_bindings", "evidence_links"
        ]
        
        for table in tables_to_check:
            print(f"\n--- Table: {table} ---")
            try:
                res = conn.execute(text(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}';"))
                cols = res.fetchall()
                if not cols:
                    print("Table does not exist.")
                else:
                    for col in cols:
                        print(f"  {col[0]}: {col[1]}")
            except Exception as e:
                print(f"Error checking {table}: {e}")

if __name__ == "__main__":
    check_schema()
