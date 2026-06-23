import sys
import os
from sqlalchemy import create_engine, text

DB_URL = "postgresql://guardianiq_user:guardianiq123@localhost:5432/guardianiq"

try:
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        for t in ["registry_departments", "registry_roles", "guardian_users", "registry_workflows", "registry_ai_agents", "registry_ai_models", "registry_tools", "registry_data_sources", "approval_groups"]:
            print(f"=== {t} ===")
            res = conn.execute(text(f"SELECT * FROM \"{t}\""))
            cols = res.keys()
            for r in res.fetchall():
                row_dict = dict(zip(cols, r))
                # print simple summary
                if t == "registry_departments":
                    print(f"ID: {row_dict['id']}, Code: {row_dict['department_code']}, Name: {row_dict['department_name']}")
                elif t == "registry_roles":
                    print(f"ID: {row_dict['id']}, Code: {row_dict['role_code']}, Name: {row_dict['role_name']}")
                elif t == "guardian_users":
                    print(f"ID: {row_dict['id']}, Email: {row_dict['email']}, Name: {row_dict['full_name']}")
                elif t == "registry_workflows":
                    print(f"ID: {row_dict['id']}, Code: {row_dict['workflow_code']}, Name: {row_dict['workflow_name']}")
                elif t == "registry_ai_agents":
                    print(f"ID: {row_dict['id']}, Code: {row_dict['agent_code']}, Name: {row_dict['agent_name']}")
                elif t == "registry_ai_models":
                    print(f"ID: {row_dict['id']}, Code: {row_dict['model_code']}, Name: {row_dict['model_name']}")
                elif t == "registry_tools":
                    print(f"ID: {row_dict['id']}, Code: {row_dict['tool_code']}, Name: {row_dict['tool_name']}")
                elif t == "registry_data_sources":
                    print(f"ID: {row_dict['id']}, Code: {row_dict['source_code']}, Name: {row_dict['source_name']}")
                elif t == "approval_groups":
                    print(f"ID: {row_dict['id']}, Name: {row_dict['name']}")
            print()
except Exception as e:
    print(f"Error: {e}")
