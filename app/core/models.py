"""SQLAlchemy base models for tests and legacy modules.

Provides a declarative BaseModel with common fields to satisfy tests that
exercise the SQLAlchemy-based layer alongside Django models.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String
from sqlalchemy.orm import declarative_mixin, declared_attr

from .db.connection import Base


@declarative_mixin
class BaseModel:
    """Base model with common columns and table naming convention."""

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now().replace(tzinfo=None))
    updated_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now().replace(tzinfo=None)
    )

    @declared_attr
    def __tablename__(cls) -> str:  # type: ignore[override]
        return cls.__name__.lower() + "s"

