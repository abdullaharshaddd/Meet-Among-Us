import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models import Base

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
# No Docker/testcontainers this phase — engine is created lazily so importing this
# conftest never fails; only tests that actually request `db` skip if it's unset.
_engine = create_engine(TEST_DATABASE_URL) if TEST_DATABASE_URL else None


@pytest.fixture()
def db() -> Session:
    if _engine is None:
        pytest.skip("TEST_DATABASE_URL not set — see backend/.env.example")
    Base.metadata.create_all(_engine)
    connection = _engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
