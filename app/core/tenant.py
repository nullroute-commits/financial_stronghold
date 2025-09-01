"""Multi-tenancy extension for Financial Stronghold."""

from __future__ import annotations

from datetime import datetime
from enum import Enum as PyEnum
from typing import List

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint
from app.core.db.uuid_type import UUID
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship

from app.core.db.connection import Base
from app.core.models import BaseModel


class TenantType(PyEnum):
    USER = "user"
    ORGANIZATION = "organization"


class TenantMixin:
    """Mixin that adds tenant scoping fields to any model."""

    @declared_attr
    def tenant_type(cls):
        return Column(Enum(TenantType), nullable=False, default=TenantType.USER)

    @declared_attr
    def tenant_id(cls):
        return Column(String(50), nullable=False, index=True)

    @property
    def tenant_key(self) -> tuple[str, str]:
        """Convenient tuple used for filtering."""
        return self.tenant_type.value, self.tenant_id


class Organization(BaseModel):
    """Top-level container for a group of users."""

    __tablename__ = "organizations"

    name = Column(String(120), unique=True, nullable=False)

    def __repr__(self):
        return f"<Organization(id={self.id}, name={self.name})>"


class UserOrganizationLink(Base):
    """Association table for user-organization membership with roles."""

    __tablename__ = "user_organization_link"
    __table_args__ = (UniqueConstraint("user_id", "org_id", name="uq_user_org_link"),)

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), primary_key=True)

    role = Column(String(20), nullable=False, default="member")
    joined_at = Column(DateTime(timezone=True), default=lambda: datetime.now().replace(tzinfo=None), nullable=False)

    # Relationships
    user = relationship("User", back_populates="organization_links")
    organization = relationship("Organization")

    def __repr__(self):
        return f"<UserOrganizationLink(user_id={self.user_id}, org_id={self.org_id}, role={self.role})>"
