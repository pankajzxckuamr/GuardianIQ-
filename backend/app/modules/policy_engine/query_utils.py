from typing import Optional, List, Any
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy import and_, or_
from sqlalchemy.orm import Query


def apply_tenant_filter(query: Query, model_cls: Any, tenant_id: UUID) -> Query:
    """Enforces strict tenant isolation on every database query."""
    return query.filter(model_cls.tenant_id == tenant_id)


def apply_effective_date_filter(
    query: Query,
    model_cls: Any,
    as_of: Optional[datetime] = None,
    from_col: str = "effective_from",
    to_col: str = "effective_to",
) -> Query:
    """
    Applies temporal validity filters (effective_from <= as_of <= effective_to).
    Handles nullable boundary dates safely.
    """
    ts = as_of or datetime.now(timezone.utc)
    from_attr = getattr(model_cls, from_col)
    to_attr = getattr(model_cls, to_col)

    return query.filter(
        and_(
            or_(from_attr <= ts, from_attr.is_(None)),
            or_(to_attr >= ts, to_attr.is_(None)),
        )
    )


def apply_pagination(query: Query, limit: Optional[int] = 50, offset: Optional[int] = 0) -> Query:
    """Applies standard limit and offset pagination."""
    if offset:
        query = query.offset(offset)
    if limit:
        query = query.limit(min(limit, 500))
    return query
