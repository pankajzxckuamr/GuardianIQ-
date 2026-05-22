from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base


class DataSource(Base):
    __tablename__ = "data_sources"

    id = Column(Integer, primary_key=True, index=True)

    source_name = Column(
        String,
        nullable=False
    )

    source_type = Column(
        String,
        nullable=False
    )

    description = Column(String)

    status = Column(String)

    owner_department_id = Column(
        Integer,
        ForeignKey("departments.id")
    )

    department = relationship(
        "Department",
        back_populates="data_sources"
    )
