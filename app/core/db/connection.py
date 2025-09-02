"""
Lightweight SQLAlchemy compatibility layer for tests.

Provides a declarative `Base` so tests that still reference SQLAlchemy
metadata can create tables in an in-memory SQLite engine.
"""

from sqlalchemy.orm import declarative_base


Base = declarative_base()

