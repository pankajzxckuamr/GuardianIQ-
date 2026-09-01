import app.main
from app.db.session import SessionLocal
from app.modules.department.models import Department, DepartmentOwnerAssignment
from app.modules.auth.models import User
from app.modules.workflow_scheduler.models import ApprovalGroup, ApprovalGroupMember

db = SessionLocal()

print("=== DEPARTMENTS & ASSIGNMENTS ===")
target_codes = ["BUSINESS_OWNER", "TECHNICAL_OWNER", "AUDIT", "HR", "LEGAL"]
depts = db.query(Department).all()
for d in depts:
    print(f"\nDepartment: {d.department_name} (Code: {d.department_code}, ID: {d.id})")
    assignments = db.query(DepartmentOwnerAssignment).filter_by(department_id=d.id).all()
    if not assignments:
        print("  -> No owner assigned")
    for a in assignments:
        if a.owner_user_id:
            u = db.query(User).filter_by(id=a.owner_user_id).first()
            name_val = getattr(u, 'full_name', getattr(u, 'name', '')) if u else ''
            print(f"  -> Owner User: {u.email if u else 'N/A'} (Name: {name_val}, ID: {a.owner_user_id})")
        if a.owner_group_id:
            g = db.query(ApprovalGroup).filter_by(id=a.owner_group_id).first()
            print(f"  -> Owner Group: {g.name if g else 'N/A'} (ID: {a.owner_group_id})")
            members = db.query(ApprovalGroupMember).filter_by(approval_group_id=a.owner_group_id).all()
            for m in members:
                mu = db.query(User).filter_by(id=m.user_id).first()
                muname = getattr(mu, 'full_name', getattr(mu, 'name', '')) if mu else ''
                print(f"      - Member: {mu.email if mu else 'N/A'} ({muname})")

print("\n=== SYSTEM / SEED USERS ===")
users = db.query(User).all()
system_users = [u for u in users if not u.email.startswith(('test_', 'tenant_', 'flow', 'gw_', 'sim_', 'boundary_', 'chain_', 'block_', 'redaction_', 'no_', 'env_', 'provider_', 'cache_', 'timeout_', 'latency_', 'binding_', 'lifecycle_', 'repo_', 'tamper_', 'replay_', 'params_'))]
for u in system_users:
    name_val = getattr(u, 'full_name', getattr(u, 'name', ''))
    print(f"User: {u.email} | Name: {name_val} | Role: {getattr(u, 'role_code', '')} | Superuser: {getattr(u, 'is_superuser', False)}")

print("\n=== ALL APPROVAL GROUPS ===")
groups = db.query(ApprovalGroup).all()
for g in groups:
    print(f"\nGroup: {g.name} (ID: {g.id})")
    members = db.query(ApprovalGroupMember).filter_by(approval_group_id=g.id).all()
    for m in members:
        mu = db.query(User).filter_by(id=m.user_id).first()
        muname = getattr(mu, 'full_name', getattr(mu, 'name', '')) if mu else ''
        print(f"  - Member: {mu.email if mu else 'N/A'} ({muname})")
