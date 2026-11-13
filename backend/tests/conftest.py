import os
from pathlib import Path

import pytest
from dotenv import dotenv_values
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

# pydantic-settings reads backend/.env without putting it in os.environ, so the test URL has to be
# read from the file here. This must run before the app is imported, because the app reads
# DATABASE_URL at import time.
_env_file = dotenv_values(Path(__file__).resolve().parents[1] / ".env")
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL") or _env_file.get("TEST_DATABASE_URL")

if TEST_DATABASE_URL:
    from app.core.db_projects import describe, same_project

    dev_url = os.environ.get("DATABASE_URL") or _env_file.get("DATABASE_URL") or ""

    if same_project(TEST_DATABASE_URL, dev_url):
        raise pytest.UsageError(
            "TEST_DATABASE_URL points at the same Supabase project as DATABASE_URL "
            f"({describe(TEST_DATABASE_URL)}). Use a separate project for tests."
        )

    # Point the app itself at the test database too, so no code path can reach the dev database
    # while tests run. Environment variables win over .env in pydantic-settings.
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    os.environ["DIRECT_URL"] = TEST_DATABASE_URL

from app.core import rate_limit
from app.core.db import get_db
from app.main import app
from app.models import Base


@pytest.fixture(autouse=True)
def _reset_rate_limits() -> None:
    # TestClient reuses the same synthetic client IP for every test, so
    # without this, an earlier test's login/signup attempts would count
    # against a later test's rate-limit budget.
    rate_limit.reset()

# No Docker/testcontainers this phase — engine is created lazily so importing this
# conftest never fails; only tests that actually request `db` skip if it's unset.
_engine = create_engine(TEST_DATABASE_URL) if TEST_DATABASE_URL else None


@pytest.fixture()
def db() -> Session:
    if _engine is None:
        pytest.skip("TEST_DATABASE_URL not set — see backend/.env.example")
    # voiceprints/enrollment_samples use pgvector's `vector` column type —
    # create_all fails against a fresh test DB without this. IF NOT EXISTS
    # makes re-running it every test cheap and harmless.
    with _engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
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
