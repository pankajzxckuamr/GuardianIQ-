from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.shared.enums.approval_status import ApprovalStatus
from datetime import datetime, timezone

class Approval(Base):
    __tablename__ = "approvals"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(SQLEnum(ApprovalStatus), nullable=False, default=ApprovalStatus.PENDING)
    comments = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, nullable=True, default=lambda: datetime.now(timezone.utc))
    
    recommendation_id = Column(Integer, ForeignKey("recommendations.id"), nullable=False)
    reviewer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Relationships
    recommendation = relationship("Recommendation", backref="approvals")
    reviewer = relationship("User", backref="approvals")
