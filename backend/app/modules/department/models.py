from sqlalchemy import Column, Integer, String, ForeignKey
from app.db.session import Base
from sqlalchemy.orm import relationship


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)

    parent_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    
    owner_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    status = Column(String(30), nullable=False, default='ACTIVE')
    
    from sqlalchemy import TIMESTAMP, text
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('NOW()'))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('NOW()'))

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
