from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Table
)
from sqlalchemy.orm import relationship

from app.db.session import Base


user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", ForeignKey("users.id")),
    Column("role_id", ForeignKey("roles.id"))
)


role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", ForeignKey("roles.id")),
    Column("permission_id", ForeignKey("permissions.id"))
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)

    email = Column(String, unique=True, nullable=False)

    hashed_password = Column(String, nullable=False)

    roles = relationship(
        "Role",
        secondary=user_roles,
        back_populates="users"
    )


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)

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