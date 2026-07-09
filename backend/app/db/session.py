from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db

    finally:
        db.close()


from sqlalchemy import event
from sqlalchemy.orm import Session

@event.listens_for(Session, "before_flush")
def receive_before_flush(session, flush_context, instances):
    try:
        from app.modules.auth.models import User
        # To avoid circular imports, User is imported locally.
        admin_user = session.query(User).filter(User.email == "admin@guardianiq.com").first()
        if admin_user:
            default_tenant_id = admin_user.id
            for obj in session.new:
                if hasattr(obj, "tenant_id") and getattr(obj, "tenant_id") is None:
                    obj.tenant_id = default_tenant_id
    except Exception:
        pass

