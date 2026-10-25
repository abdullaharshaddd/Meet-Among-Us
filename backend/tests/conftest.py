import os
import re
from pathlib import Path
from urllib.parse import urlparse

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

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

# Settings ignores unknown keys, so TEST_DATABASE_URL never reaches os.environ on its
# own. load_dotenv doesn't override variables already set in the real environment.
load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def _supabase_project_ref(url: str | None) -> str | None:
    # Pooler URLs carry the ref in the username (postgres.<ref>); direct URLs carry it
    # in the host (db.<ref>.supabase.co). Two different URLs can be the same project.
    if not url:
        return None
    parsed = urlparse(url)
    if parsed.username and "." in parsed.username:
        return parsed.username.split(".", 1)[1]
    match = re.match(r"^db\.([a-z0-9]+)\.supabase\.co$", parsed.hostname or "")

    return match.group(1) if match else None


def _refuse_if_pointing_at_real_database(test_url: str | None) -> None:
    # create_all + rollback tests must never touch the shared database. Messages below
    # deliberately never include any URL.
    if not test_url:
        return
    for name in ("DATABASE_URL", "DIRECT_URL"):
        real_url = os.environ.get(name)
        if not real_url:
            continue
        if test_url == real_url:
            pytest.exit(f"TEST_DATABASE_URL is identical to {name}. Refusing to run tests.", returncode=2)
        test_ref = _supabase_project_ref(test_url)
        if test_ref is not None and test_ref == _supabase_project_ref(real_url):
            pytest.exit(f"TEST_DATABASE_URL is the same Supabase project as {name}. Refusing to run tests.", returncode=2)


TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
_refuse_if_pointing_at_real_database(TEST_DATABASE_URL)
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
    # users.email and invites.email are CITEXT, which needs the same treatment.
    with _engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS citext"))
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
