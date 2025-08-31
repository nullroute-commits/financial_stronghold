"""Multi-tenancy extension for Financial Stronghold."""

import pytest
from sqlalchemy import create_engine, TypeDecorator, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from app.core.db.connection import Base
import uuid


class UUIDTEXT(TypeDecorator):
    """UUID type that gets converted to String for SQLite."""
    impl = String
    cache_ok = True
    
    def load_dialect_impl(self, dialect):
        if dialect.name == 'sqlite':
            return dialect.type_descriptor(String(36))
        return dialect.type_descriptor(PostgreSQLUUID(as_uuid=True))
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == 'sqlite':
            return str(value)
        return value
    
    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if dialect.name == 'sqlite':
            return uuid.UUID(value)
        return value


@pytest.fixture(scope="function")
def db_session():
    """Create a test database session."""
    # Use in-memory SQLite for testing with UUID compatibility
    engine = create_engine("sqlite:///:memory:", echo=False)
    
    # Monkey patch UUID column type for SQLite compatibility
    import sqlalchemy.dialects.postgresql.base as pg_base
    original_uuid = pg_base.UUID
    pg_base.UUID = UUIDTEXT
    
    try:
        Base.metadata.create_all(engine)
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        
        try:
            yield session
        finally:
            session.close()
    finally:
        # Restore original UUID type
        pg_base.UUID = original_uuid
        engine.dispose()


@pytest.fixture(scope="function")
def test_engine():
    """Create a test database engine."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    
    # Monkey patch UUID column type for SQLite compatibility
    import sqlalchemy.dialects.postgresql.base as pg_base
    original_uuid = pg_base.UUID
    pg_base.UUID = UUIDTEXT
    
    try:
        Base.metadata.create_all(engine)
        yield engine
    finally:
        # Restore original UUID type
        pg_base.UUID = original_uuid
        engine.dispose()