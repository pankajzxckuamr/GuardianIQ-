from sqlalchemy import Column, Integer, String
from app.db.session import Base
from sqlalchemy.orm import relationship


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)


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
