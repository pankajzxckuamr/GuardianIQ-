from sqlalchemy import Column, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.db.session import Base
from sqlalchemy.dialects.postgresql import UUID
from app.shared.mixins import WorkflowBaseMixin, GovernableMixin

class DataSource(Base, GovernableMixin):
    __tablename__ = "data_sources"
    __object_type__ = "DATA_SOURCE"
    __name_column__ = "source_name"

    source_code = Column(String(80), unique=True, nullable=False)
    source_name = Column(String(200), nullable=False)
    source_type = Column(String(80), nullable=False)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True)
    classification = Column(String(80), nullable=False)
    sensitivity_level = Column(String(50), nullable=False)
    region = Column(String(80), nullable=True)
    contains_pii = Column(Boolean, default=False)
    retention_policy = Column(String(200), nullable=True)
    connection_reference = Column(String(500), nullable=True)

    department = relationship(
        "Department",
        back_populates="data_sources"
    )
