"""
ApplicationSettings model.

Stores global key-value configuration for the platform.
Each setting has a key, a value, an optional description,
and a category to group related settings.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime

from app.db.session import Base


class ApplicationSettings(Base):
    __tablename__ = "application_settings"

    id = Column(Integer, primary_key=True, index=True)

    # e.g. "auth.max_login_attempts", "audit.retention_days"
    key = Column(String, unique=True, nullable=False, index=True)

    # All values stored as strings; callers are responsible for casting
    value = Column(String, nullable=False)

    # Human-readable description of what this setting controls
    description = Column(String, nullable=True)

    # Groups settings (e.g. "auth", "audit", "notifications", "ui")
    category = Column(String, nullable=False, default="general")

    # Whether the setting can be overridden at runtime or is read-only
    is_editable = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    def __repr__(self):
        return f"<ApplicationSettings key={self.key!r} value={self.value!r}>"
