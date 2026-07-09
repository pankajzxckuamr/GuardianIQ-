from sqlalchemy import Column, String, ForeignKey
from app.db.session import Base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.shared.mixins import WorkflowBaseMixin, GovernableMixin

class Department(Base, GovernableMixin):
    __tablename__ = "departments"
    __object_type__ = "DEPARTMENT"
    __name_column__ = "department_name"

    parent_id = Column(UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    
    department_code = Column(
        String,
        unique=True,
        nullable=False
    )

    department_name = Column(
        String,
        nullable=False
    )

    description = Column(String)

    data_sources = relationship(
        "DataSource",
        back_populates="department"
    )
