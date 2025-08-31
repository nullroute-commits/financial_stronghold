"""Tagging and Analytics Service for USER_ID, ORG_ID, ROLE_ID level data analysis."""

import hashlib
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.core.db.connection import get_db_session
from app.core.models import User, Role
from app.core.tenant import Organization, TenantType
from app.financial_models import Account, Budget, Transaction
from app.tagging_models import TagType


class TaggingService:
    """Service for managing data tags and performing analytics."""

    def __init__(self, db: Session):
        self.db = db

    def create_user_tag(
        self,
        user_id: Union[str, UUID],
        resource_type: str,
        resource_id: Union[str, UUID],
        tenant_type: str,
        tenant_id: str,
        label: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "DataTag":
        """Create a USER_ID level tag for a resource."""
        return self._create_tag(
            tag_type=TagType.USER,
            tag_key="user_id",
            tag_value=str(user_id),
            resource_type=resource_type,
            resource_id=resource_id,
            tenant_type=tenant_type,
            tenant_id=tenant_id,
            label=label or f"User {user_id}",
            metadata=metadata,
        )

    def create_organization_tag(
        self,
        org_id: Union[str, int],
        resource_type: str,
        resource_id: Union[str, UUID],
        tenant_type: str,
        tenant_id: str,
        label: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "DataTag":
        """Create an ORG_ID level tag for a resource."""
        return self._create_tag(
            tag_type=TagType.ORGANIZATION,
            tag_key="org_id",
            tag_value=str(org_id),
            resource_type=resource_type,
            resource_id=resource_id,
            tenant_type=tenant_type,
            tenant_id=tenant_id,
            label=label or f"Organization {org_id}",
            metadata=metadata,
        )

    def create_role_tag(
        self,
        role_id: Union[str, UUID],
        resource_type: str,
        resource_id: Union[str, UUID],
        tenant_type: str,
        tenant_id: str,
        label: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "DataTag":
        """Create a ROLE_ID level tag for a resource."""
        return self._create_tag(
            tag_type=TagType.ROLE,
            tag_key="role_id",
            tag_value=str(role_id),
            resource_type=resource_type,
            resource_id=resource_id,
            tenant_type=tenant_type,
            tenant_id=tenant_id,
            label=label or f"Role {role_id}",
            metadata=metadata,
        )

    def _create_tag(
        self,
        tag_type: TagType,
        tag_key: str,
        tag_value: str,
        resource_type: str,
        resource_id: Union[str, UUID],
        tenant_type: str,
        tenant_id: str,
        label: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "DataTag":
        """Internal method to create a tag."""
        from app.tagging_models import DataTag
        
        tag = DataTag(
            tag_type=tag_type,
            tag_key=tag_key,
            tag_value=tag_value,
            resource_type=resource_type,
            resource_id=str(resource_id),
            tenant_type=TenantType(tenant_type),
            tenant_id=tenant_id,
            tag_label=label,
            tag_metadata=metadata,
        )
        
        self.db.add(tag)
        self.db.commit()
        self.db.refresh(tag)
        return tag

    def get_resource_tags(
        self,
        resource_type: str,
        resource_id: Union[str, UUID],
        tenant_type: str,
        tenant_id: str,
        tag_types: Optional[List[TagType]] = None,
    ) -> List["DataTag"]:
        """Get all tags for a specific resource."""
        from app.tagging_models import DataTag
        
        query = self.db.query(DataTag).filter(
            and_(
                DataTag.resource_type == resource_type,
                DataTag.resource_id == str(resource_id),
                DataTag.tenant_type == TenantType(tenant_type),
                DataTag.tenant_id == tenant_id,
                DataTag.is_active.is_(True),
            )
        )
        
        if tag_types:
            query = query.filter(DataTag.tag_type.in_(tag_types))
        
        return query.all()

    def get_tagged_resources(
        self,
        tag_filters: Dict[str, str],
        resource_type: str,
        tenant_type: str,
        tenant_id: str,
    ) -> List[str]:
        """Get resource IDs that match the given tag filters."""
        from app.tagging_models import DataTag
        
        resource_ids = set()
        
        for tag_key, tag_value in tag_filters.items():
            # Determine tag type based on key
            if tag_key == "user_id":
                tag_type = TagType.USER
            elif tag_key == "org_id":
                tag_type = TagType.ORGANIZATION
            elif tag_key == "role_id":
                tag_type = TagType.ROLE
            else:
                tag_type = TagType.CUSTOM
            
            tags = self.db.query(DataTag).filter(
                and_(
                    DataTag.tag_type == tag_type,
                    DataTag.tag_key == tag_key,
                    DataTag.tag_value == tag_value,
                    DataTag.resource_type == resource_type,
                    DataTag.tenant_type == TenantType(tenant_type),
                    DataTag.tenant_id == tenant_id,
                    DataTag.is_active.is_(True),
                )
            ).all()
            
            current_resource_ids = {tag.resource_id for tag in tags}
            
            if not resource_ids:
                resource_ids = current_resource_ids
            else:
                # Intersection - resources must have ALL specified tags
                resource_ids = resource_ids.intersection(current_resource_ids)
        
        return list(resource_ids)

    def auto_tag_resource(
        self,
        resource_type: str,
        resource_id: Union[str, UUID],
        tenant_type: str,
        tenant_id: str,
        user_id: Optional[Union[str, UUID]] = None,
    ) -> List["DataTag"]:
        """Automatically create standard tags for a resource."""
        tags = []
        
        # Always create tenant-level tags
        if tenant_type == "user":
            tags.append(
                self.create_user_tag(
                    user_id=tenant_id,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    tenant_type=tenant_type,
                    tenant_id=tenant_id,
                )
            )
        elif tenant_type == "organization":
            tags.append(
                self.create_organization_tag(
                    org_id=tenant_id,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    tenant_type=tenant_type,
                    tenant_id=tenant_id,
                )
            )
        
        # Add user-specific tag if provided and different from tenant
        if user_id and str(user_id) != tenant_id:
            tags.append(
                self.create_user_tag(
                    user_id=user_id,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    tenant_type=tenant_type,
                    tenant_id=tenant_id,
                )
            )
        
        # Add role tags for the user
        if user_id:
            user = self.db.query(User).filter(User.id == str(user_id)).first()
            if user:
                for role in user.roles:
                    if role.is_active:
                        tags.append(
                            self.create_role_tag(
                                role_id=role.id,
                                resource_type=resource_type,
                                resource_id=resource_id,
                                tenant_type=tenant_type,
                                tenant_id=tenant_id,
                                label=f"Role: {role.name}",
                            )
                        )
        
        return tags


class AnalyticsService:
    """Service for computing analytics on tagged data."""

    def __init__(self, db: Session):
        self.db = db
        self.tagging_service = TaggingService(db)

    def compute_tag_metrics(
        self,
        tag_filters: Dict[str, str],
        resource_type: str,
        tenant_type: str,
        tenant_id: str,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Compute metrics for resources matching tag filters."""
        # Get resource IDs matching the tag filters
        resource_ids = self.tagging_service.get_tagged_resources(
            tag_filters=tag_filters,
            resource_type=resource_type,
            tenant_type=tenant_type,
            tenant_id=tenant_id,
        )
        
        if not resource_ids:
            return self._empty_metrics()
        
        # Compute metrics based on resource type
        if resource_type == "transaction":
            return self._compute_transaction_metrics(
                resource_ids, tenant_type, tenant_id, period_start, period_end
            )
        elif resource_type == "account":
            return self._compute_account_metrics(
                resource_ids, tenant_type, tenant_id
            )
        elif resource_type == "budget":
            return self._compute_budget_metrics(
                resource_ids, tenant_type, tenant_id
            )
        else:
            return self._empty_metrics()

    def _compute_transaction_metrics(
        self,
        resource_ids: List[str],
        tenant_type: str,
        tenant_id: str,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Compute metrics for transactions."""
        query = self.db.query(Transaction).filter(
            and_(
                Transaction.id.in_(resource_ids),
                Transaction.tenant_type == TenantType(tenant_type),
                Transaction.tenant_id == tenant_id,
            )
        )
        
        if period_start:
            query = query.filter(Transaction.created_at >= period_start)
        if period_end:
            query = query.filter(Transaction.created_at <= period_end)
        
        transactions = query.all()
        
        if not transactions:
            return self._empty_metrics()
        
        total_amount = sum(t.amount for t in transactions)
        count = len(transactions)
        avg_amount = total_amount / count if count > 0 else Decimal("0")
        
        # Group by transaction type
        type_breakdown = {}
        for transaction in transactions:
            t_type = transaction.transaction_type
            if t_type not in type_breakdown:
                type_breakdown[t_type] = {"count": 0, "amount": Decimal("0")}
            type_breakdown[t_type]["count"] += 1
            type_breakdown[t_type]["amount"] += transaction.amount
        
        # Group by currency
        currency_breakdown = {}
        for transaction in transactions:
            currency = transaction.currency
            if currency not in currency_breakdown:
                currency_breakdown[currency] = {"count": 0, "amount": Decimal("0")}
            currency_breakdown[currency]["count"] += 1
            currency_breakdown[currency]["amount"] += transaction.amount
        
        return {
            "resource_type": "transaction",
            "total_count": count,
            "total_amount": float(total_amount),
            "average_amount": float(avg_amount),
            "min_amount": float(min(t.amount for t in transactions)),
            "max_amount": float(max(t.amount for t in transactions)),
            "currency_breakdown": {
                k: {"count": v["count"], "amount": float(v["amount"])}
                for k, v in currency_breakdown.items()
            },
            "type_breakdown": {
                k: {"count": v["count"], "amount": float(v["amount"])}
                for k, v in type_breakdown.items()
            },
            "period_start": period_start.isoformat() if period_start else None,
            "period_end": period_end.isoformat() if period_end else None,
        }

    def _compute_account_metrics(
        self, resource_ids: List[str], tenant_type: str, tenant_id: str
    ) -> Dict[str, Any]:
        """Compute metrics for accounts."""
        accounts = self.db.query(Account).filter(
            and_(
                Account.id.in_(resource_ids),
                Account.tenant_type == TenantType(tenant_type),
                Account.tenant_id == tenant_id,
            )
        ).all()
        
        if not accounts:
            return self._empty_metrics()
        
        total_balance = sum(a.balance for a in accounts)
        count = len(accounts)
        active_count = sum(1 for a in accounts if a.is_active)
        
        # Group by account type
        type_breakdown = {}
        for account in accounts:
            a_type = account.account_type
            if a_type not in type_breakdown:
                type_breakdown[a_type] = {"count": 0, "balance": Decimal("0")}
            type_breakdown[a_type]["count"] += 1
            type_breakdown[a_type]["balance"] += account.balance
        
        return {
            "resource_type": "account",
            "total_count": count,
            "active_count": active_count,
            "total_balance": float(total_balance),
            "average_balance": float(total_balance / count) if count > 0 else 0.0,
            "type_breakdown": {
                k: {"count": v["count"], "balance": float(v["balance"])}
                for k, v in type_breakdown.items()
            },
        }

    def _compute_budget_metrics(
        self, resource_ids: List[str], tenant_type: str, tenant_id: str
    ) -> Dict[str, Any]:
        """Compute metrics for budgets."""
        budgets = self.db.query(Budget).filter(
            and_(
                Budget.id.in_(resource_ids),
                Budget.tenant_type == TenantType(tenant_type),
                Budget.tenant_id == tenant_id,
            )
        ).all()
        
        if not budgets:
            return self._empty_metrics()
        
        total_budget = sum(b.total_amount for b in budgets)
        total_spent = sum(b.spent_amount for b in budgets)
        count = len(budgets)
        active_count = sum(1 for b in budgets if b.is_active)
        over_budget_count = sum(1 for b in budgets if b.spent_amount > b.total_amount)
        
        return {
            "resource_type": "budget",
            "total_count": count,
            "active_count": active_count,
            "over_budget_count": over_budget_count,
            "total_budget_amount": float(total_budget),
            "total_spent_amount": float(total_spent),
            "total_remaining": float(total_budget - total_spent),
            "utilization_percentage": float((total_spent / total_budget * 100)) if total_budget > 0 else 0.0,
        }

    def _empty_metrics(self) -> Dict[str, Any]:
        """Return empty metrics structure."""
        return {
            "total_count": 0,
            "message": "No data found for the specified filters",
        }

    def get_analytics_summary(
        self,
        tenant_type: str,
        tenant_id: str,
        tag_filters: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Get comprehensive analytics summary across all resource types."""
        summary = {
            "tenant_info": {"tenant_type": tenant_type, "tenant_id": tenant_id},
            "tag_filters": tag_filters or {},
            "resource_metrics": {},
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        
        resource_types = ["transaction", "account", "budget"]
        
        for resource_type in resource_types:
            try:
                metrics = self.compute_tag_metrics(
                    tag_filters=tag_filters or {},
                    resource_type=resource_type,
                    tenant_type=tenant_type,
                    tenant_id=tenant_id,
                )
                summary["resource_metrics"][resource_type] = metrics
            except Exception as e:
                summary["resource_metrics"][resource_type] = {
                    "error": str(e),
                    "total_count": 0,
                }
        
        return summary

    def create_analytics_view(
        self,
        view_name: str,
        tag_filters: Dict[str, str],
        resource_types: List[str],
        tenant_type: str,
        tenant_id: str,
        description: Optional[str] = None,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
    ) -> "AnalyticsView":
        """Create a saved analytics view for future reference."""
        from app.tagging_models import AnalyticsView
        
        # Compute initial metrics
        metrics = {}
        for resource_type in resource_types:
            metrics[resource_type] = self.compute_tag_metrics(
                tag_filters=tag_filters,
                resource_type=resource_type,
                tenant_type=tenant_type,
                tenant_id=tenant_id,
                period_start=period_start,
                period_end=period_end,
            )
        
        view = AnalyticsView(
            view_name=view_name,
            view_description=description,
            tag_filters=tag_filters,
            resource_types=resource_types,
            metrics=metrics,
            period_start=period_start,
            period_end=period_end,
            tenant_type=TenantType(tenant_type),
            tenant_id=tenant_id,
            last_computed=datetime.now(timezone.utc),
            computation_status="completed",
        )
        
        self.db.add(view)
        self.db.commit()
        self.db.refresh(view)
        return view

    def refresh_analytics_view(self, view_id: Union[str, UUID]) -> "AnalyticsView":
        """Refresh an existing analytics view with current data."""
        from app.tagging_models import AnalyticsView
        
        view = self.db.query(AnalyticsView).filter(AnalyticsView.id == str(view_id)).first()
        if not view:
            raise ValueError(f"Analytics view {view_id} not found")
        
        view.computation_status = "computing"
        self.db.commit()
        
        try:
            # Recompute metrics
            metrics = {}
            for resource_type in view.resource_types:
                metrics[resource_type] = self.compute_tag_metrics(
                    tag_filters=view.tag_filters,
                    resource_type=resource_type,
                    tenant_type=view.tenant_type.value,
                    tenant_id=view.tenant_id,
                    period_start=view.period_start,
                    period_end=view.period_end,
                )
            
            view.metrics = metrics
            view.last_computed = datetime.now(timezone.utc)
            view.computation_status = "completed"
            self.db.commit()
            
        except Exception as e:
            view.computation_status = "failed"
            self.db.commit()
            raise e
        
        return view