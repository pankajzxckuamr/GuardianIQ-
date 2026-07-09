from sqlalchemy import Column, String, JSON
from app.db.session import Base
from app.shared.mixins import WorkflowBaseMixin

class Policy(Base, WorkflowBaseMixin):
    __tablename__ = "policies"

    policy_name = Column(
        String,
        nullable=False
    )

    policy_type = Column(
        String,
        nullable=False
    )

    severity = Column(
        String,
        nullable=False
    )

    status = Column(
        String,
        nullable=False,
        index=True
    )

    reference_id = Column(
        String,
        nullable=True,
        index=True
    )

    conditions = Column(JSON)
    actions = Column(JSON)
