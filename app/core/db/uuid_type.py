"""
UUID and JSONB type compatibility for SQLite and PostgreSQL.
Provides unified types that work with both databases.

Last updated: 2025-08-30 22:40:55 UTC by nullroute-commits
"""

import json
import uuid
from sqlalchemy import String, Text, TypeDecorator
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID, JSONB as PostgreSQLJSONB


class UUID(TypeDecorator):
    """
    Universal UUID type that works with SQLite and PostgreSQL.

    - In PostgreSQL: Uses native UUID type
    - In SQLite: Uses String(36) and converts to/from UUID objects
    """

    impl = String
    cache_ok = True

    def __init__(self, as_uuid=True, **kwargs):
        """
        Initialize UUID type.

        Args:
            as_uuid: Whether to return UUID objects (True) or strings (False)
        """
        self.as_uuid = as_uuid
        super().__init__(**kwargs)

    def load_dialect_impl(self, dialect):
        """Load the appropriate type for the dialect."""
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PostgreSQLUUID(as_uuid=self.as_uuid))
        else:
            # SQLite and others use String(36)
            return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        """Process value when binding parameter."""
        if value is None:
            return value

        if dialect.name == "postgresql":
            # PostgreSQL handles UUID natively
            return value
        else:
            # Convert to string for SQLite
            if isinstance(value, uuid.UUID):
                return str(value)
            return str(value)

    def process_result_value(self, value, dialect):
        """Process value when loading from database."""
        if value is None:
            return value

        if dialect.name == "postgresql":
            # PostgreSQL returns UUID objects if as_uuid=True
            return value
        else:
            # Convert string back to UUID for SQLite
            if self.as_uuid and isinstance(value, str):
                return uuid.UUID(value)
            return value


class JSONB(TypeDecorator):
    """
    Universal JSONB type that works with SQLite and PostgreSQL.

    - In PostgreSQL: Uses native JSONB type
    - In SQLite: Uses Text and converts to/from JSON strings
    """

    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        """Load the appropriate type for the dialect."""
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PostgreSQLJSONB())
        else:
            # SQLite and others use Text
            return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        """Process value when binding parameter."""
        if value is None:
            return value

        if dialect.name == "postgresql":
            # PostgreSQL handles JSONB natively
            return value
        else:
            # Convert to JSON string for SQLite
            if isinstance(value, (dict, list)):
                return json.dumps(value)
            return value

    def process_result_value(self, value, dialect):
        """Process value when loading from database."""
        if value is None:
            return value

        if dialect.name == "postgresql":
            # PostgreSQL returns objects directly
            return value
        else:
            # Parse JSON string for SQLite
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return value
            return value
