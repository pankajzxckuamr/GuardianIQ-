import re

filepath = r"D:\GuardianIQ--1\backend\app\api\phase2_scheduler_routes.py"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Replace await db.commit() and await db.rollback()
new_content = content.replace("await db.commit()", "db.commit()")
new_content = new_content.replace("await db.rollback()", "db.rollback()")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(new_content)

print("Successfully replaced all 'await db.commit()' and 'await db.rollback()' with synchronous calls.")
