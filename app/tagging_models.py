"""Data tagging and analytics models for USER_ID, ORG_ID, ROLE_ID level analysis."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.models import BaseModel
from app.core.tenant import TenantMixin


class TagType(PyEnum):
    """Types of tags that can be applied to data."""
    
    USER = "user"
    ORGANIZATION = "organization"
    ROLE = "role"
    CATEGORY = "category"
    CUSTOM = "custom"


class DataTag(BaseModel, TenantMixin):
    """
    Universal tagging system for USER_ID, ORG_ID, ROLE_ID level data categorization.
    """

    __tablename__ = "data_tags"

    # Tag identification
    tag_type = Column(Enum(TagType), nullable=False, index=True)
    tag_key = Column(String(100), nullable=False, index=True)  # e.g., "user_id", "org_id", "role_id"
    tag_value = Column(String(255), nullable=False, index=True)  # The actual ID or value
    
    # Target resource
    resource_type = Column(String(100), nullable=False, index=True)  # e.g., "transaction", "account", "budget"
    resource_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Tag metadata
    tag_label = Column(String(255), nullable=True)  # Human-readable label
    tag_description = Column(Text, nullable=True)
    tag_color = Column(String(7), nullable=True)  # Hex color code for UI
    
    # Status and metadata
    is_active = Column(Boolean, default=True, nullable=False)
    priority = Column(Integer, default=0, nullable=False)  # For ordering tags
    tag_metadata = Column(JSONB, nullable=True)  # Additional structured data
    
    # Ensure uniqueness of tag per resource
    __table_args__ = (
        UniqueConstraint('tag_type', 'tag_key', 'tag_value', 'resource_type', 'resource_id', 
                        name='uq_data_tag_resource'),
    )

    def __repr__(self):
        return f"<DataTag(type={self.tag_type}, key={self.tag_key}, value={self.tag_value}, resource={self.resource_type}:{self.resource_id})>"


class AnalyticsView(BaseModel, TenantMixin):
    """
    Pre-computed analytics views for different tag combinations.
    """

    __tablename__ = "analytics_views"

    # View definition
    view_name = Column(String(100), nullable=False, index=True)
    view_description = Column(Text, nullable=True)
    
    # Tag filters
    tag_filters = Column(JSONB, nullable=False)  # JSON defining tag filter criteria
    
    # Time period
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)
    
    # Computed metrics
    metrics = Column(JSONB, nullable=False)  # Computed analytical results
    
    # Resource scope
    resource_types = Column(JSONB, nullable=False)  # List of resource types included
    
    # Status and lifecycle
    is_active = Column(Boolean, default=True, nullable=False)
    last_computed = Column(DateTime(timezone=True), nullable=True)
    computation_status = Column(String(20), default="pending", nullable=False)  # pending, computing, completed, failed
    
    # Cache settings
    cache_ttl_seconds = Column(Integer, default=3600, nullable=False)  # 1 hour default
    auto_refresh = Column(Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<AnalyticsView(name={self.view_name}, status={self.computation_status}, last_computed={self.last_computed})>"


class TagHierarchy(BaseModel):
    """
    Hierarchical relationships between tags for organizational structure.
    """

    __tablename__ = "tag_hierarchies"

    # Parent-child relationship
    parent_tag_id = Column(UUID(as_uuid=True), ForeignKey("data_tags.id"), nullable=False)
    child_tag_id = Column(UUID(as_uuid=True), ForeignKey("data_tags.id"), nullable=False)
    
    # Relationship metadata
    relationship_type = Column(String(50), default="parent_child", nullable=False)
    hierarchy_level = Column(Integer, default=1, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    parent_tag = relationship("DataTag", foreign_keys=[parent_tag_id])
    child_tag = relationship("DataTag", foreign_keys=[child_tag_id])
    
    # Prevent circular references
    __table_args__ = (
        UniqueConstraint('parent_tag_id', 'child_tag_id', name='uq_tag_hierarchy'),
    )

    def __repr__(self):
        return f"<TagHierarchy(parent={self.parent_tag_id}, child={self.child_tag_id}, level={self.hierarchy_level})>"


class TaggedResourceMetrics(BaseModel, TenantMixin):
    """
    Aggregated metrics for tagged resources across different dimensions.
    """

    __tablename__ = "tagged_resource_metrics"

    # Tag dimension
    tag_combination = Column(JSONB, nullable=False, index=True)  # JSON of tag key-value pairs
    tag_combination_hash = Column(String(64), nullable=False, index=True)  # Hash of tag combination for fast lookup
    
    # Resource type
    resource_type = Column(String(100), nullable=False, index=True)
    
    # Time period
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    period_type = Column(String(20), nullable=False)  # daily, weekly, monthly, yearly
    
    # Metrics
    resource_count = Column(Integer, default=0, nullable=False)
    total_amount = Column(JSONB, nullable=True)  # Amount by currency
    average_amount = Column(JSONB, nullable=True)  # Average amount by currency
    min_amount = Column(JSONB, nullable=True)
    max_amount = Column(JSONB, nullable=True)
    
    # Additional metrics specific to resource type
    custom_metrics = Column(JSONB, nullable=True)
    
    # Computation metadata
    computed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    is_current = Column(Boolean, default=True, nullable=False)
    
    # Ensure uniqueness per tag combination, resource type, and period
    __table_args__ = (
        UniqueConstraint('tag_combination_hash', 'resource_type', 'period_start', 'period_end', 
                        name='uq_tagged_metrics_period'),
    )

    def __repr__(self):
        return f"<TaggedResourceMetrics(hash={self.tag_combination_hash}, type={self.resource_type}, period={self.period_start}-{self.period_end})>"