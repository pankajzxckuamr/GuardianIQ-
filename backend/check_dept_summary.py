import app.main
from app.db.session import SessionLocal
from app.modules.department.models import Department, DepartmentOwnerAssignment
from app.modules.auth.models import User
from app.modules.workflow_scheduler.models import ApprovalGroup, ApprovalGroupMember

db = SessionLocal()
codes = ['BUSINESS_OWNER', 'TECHNICAL_OWNER', 'AUDIT', 'HR', 'LEGAL']

for code in codes:
    d = db.query(Department).filter(Department.department_code == code).first()
    if not d:
        print(f"Department code {code}: NOT FOUND in database!")
        continue
    print(f"\n==========================================")
    print(f"Department: {d.department_name} ({d.department_code})")
    print(f"Department ID: {d.id}")
    assignments = db.query(DepartmentOwnerAssignment).filter_by(department_id=d.id).all()
    if not assignments:
        print("  Status: No owner assignment configured in department_owner_assignments table.")
    for a in assignments:
        if a.owner_user_id:
            u = db.query(User).filter_by(id=a.owner_user_id).first()
            name_val = (u.full_name or u.name or u.email) if u else "Unknown"
            print(f"  -> Assigned User: {u.email if u else 'N/A'} (Name: {name_val}) [User ID: {a.owner_user_id}]")
        if a.owner_group_id:
            g = db.query(ApprovalGroup).filter_by(id=a.owner_group_id).first()
            print(f"  -> Assigned Group: {g.name if g else 'N/A'} [Group ID: {a.owner_group_id}]")
            members = db.query(ApprovalGroupMember).filter_by(approval_group_id=a.owner_group_id).all()
            print(f"     Group Member Count: {len(members)}")
            for m in members:
                mu = db.query(User).filter_by(id=m.user_id).first()
                muname = (mu.full_name or mu.name or mu.email) if mu else "Unknown"
                print(f"     - Member: {mu.email if mu else 'N/A'} ({muname}) [ID: {m.user_id}]")

print("\n==========================================")
print("Standard / Production Users in DB:")
for u in db.query(User).all():
    email = u.email or ""
    if "@guardianiq.com" in email or email in ["admin@guardianiq.com", "auditor@guardianiq.com", "reviewer@guardianiq.com", "sarah.jenkins@guardianiq.com"]:
        name_val = u.full_name or u.name or email
        print(f"User: {email} | Name: {name_val} | Role: {u.role_code} | ID: {u.id}")
