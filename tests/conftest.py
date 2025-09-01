"""Multi-tenancy extension for Financial Stronghold."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.db.connection import Base


@pytest.fixture(scope="function")
def db_session():
    """Create a test database session."""
    # Use in-memory SQLite for testing with UUID compatibility
    engine = create_engine("sqlite:///:memory:", echo=False)
    
    try:
        Base.metadata.create_all(engine)
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        
        try:
            yield session
        finally:
            session.close()
    finally:
        engine.dispose()


@pytest.fixture(scope="function")
def test_engine():
    """Create a test database engine."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    
    try:
        Base.metadata.create_all(engine)
        yield engine
    finally:
        engine.dispose()