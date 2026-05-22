from sqlalchemy import Column, Integer, String, JSON
from app.db.session import Base


class Policy(Base):
    __tablename__ = "policies"

    id = Column(Integer, primary_key=True, index=True)

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
        nullable=False
    )

    conditions = Column(JSON)

    actions = Column(JSON)

    created_by = Column(Integer)
