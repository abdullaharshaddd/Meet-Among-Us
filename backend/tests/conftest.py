import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.main import app
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
    # join_transaction_mode="create_savepoint": application code (repositories) calls
    # session.commit() as it normally would in a real request. Without this, that
    # commit would commit the *outer* connection-level transaction below, and
    # transaction.rollback() at teardown would no longer undo it — test data would
    # persist in the test database. This wraps each commit in a SAVEPOINT instead and
    # restarts it, so the outer rollback always undoes everything.
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture()
def client(db: Session) -> TestClient:
    # Overrides get_db so requests made through this client run inside the same
    # rolled-back transaction as the `db` fixture — every DB-touching test is
    # isolated and leaves no rows behind, without needing per-test cleanup code.
    app.dependency_overrides[get_db] = lambda: db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_db, None)
