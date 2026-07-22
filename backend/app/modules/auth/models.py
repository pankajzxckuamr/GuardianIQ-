from uuid import uuid4
from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Table,
    TIMESTAMP,
    text,
    event
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id")),
    Column("role_id", UUID(as_uuid=True), ForeignKey("roles.id"))
)


role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", UUID(as_uuid=True), ForeignKey("roles.id")),
    Column("permission_id", ForeignKey("permissions.id"))
)


class User(Base):
    __tablename__ = "users"
    __object_type__ = "USER"
    __name_column__ = "full_name"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String, nullable=False)
    full_name = Column(String(200), nullable=True)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True)
    approval_limit_level = Column(String(50), nullable=True)
    status = Column(String(30), nullable=False, default='ACTIVE')
    
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('NOW()'))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('NOW()'))

    roles = relationship(
        "Role",
        secondary=user_roles,
        back_populates="users"
    )

    @property
    def role_id(self):
        if self.roles:
            return self.roles[0].id
        return None

    @property
    def role_code(self) -> str:
        if not self.roles:
            return ""
        codes = [r.role_code for r in self.roles]
        if "SUPER_ADMIN" in codes or "SYSTEM_ADMIN" in codes:
            return "ADMIN"
        if "GOVERNANCE_ADMIN" in codes:
            return "GOVERNANCE_MANAGER"
        if "AUDITOR" in codes:
            return "AUDITOR"
        return codes[0]


class Role(Base):
    __tablename__ = "roles"
    __object_type__ = "ROLE"
    __name_column__ = "role_name"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    role_code = Column(String, unique=True, nullable=False)
    role_name = Column(String, nullable=False)
    description = Column(String)

    users = relationship(
        "User",
        secondary=user_roles,
        back_populates="roles"
    )

    permissions = relationship(
        "Permission",
        secondary=role_permissions,
        back_populates="roles"
    )


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    permission_code = Column(
        String,
        unique=True,
        nullable=False
    )
    description = Column(String)

    roles = relationship(
        "Role",
        secondary=role_permissions,
        back_populates="permissions"
    )

class TokenBlocklist(Base):
    __tablename__ = "token_blocklist"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True, nullable=False)
    expires_at = Column(Integer, nullable=False)


@event.listens_for(User, "before_insert")
@event.listens_for(User, "before_update")
def user_full_name_listener(mapper, connection, target):
    if not target.full_name and target.name:
        target.full_name = target.name
    elif not target.name and target.full_name:
        target.name = target.full_name